"""Compact alternate views over the original mod and AI methods.

Only layout, selection/filtering and result presentation live here. Providers,
permissions, immutable jobs and approval/Stop behavior stay with their owners.
"""
from __future__ import annotations
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk
from GameToolCompactUI import FlowToolbar, ScrollableFrame, TableLayout
from GameToolAutomationPanel import AutomationPanel
from GameToolAutomation import capabilities
from game_mod_ops.panel import ModWorkflowPanel, DEFAULT_RECIPE, default_data
from game_mod_ops.recipes import load_recipe
from game_mod_ops.safety import ModError

VERSION = '0.1.0'


def concise_result(value):
    """Presentation, not a success classifier. Preserve exact machine status."""
    if not isinstance(value, dict):
        return str(value)[:400]
    code = value.get('status', value.get('kind', 'Result returned'))
    message = value.get('message', '')
    return (str(code) + (' — ' + str(message) if message else ''))[:700]


class Disclosure(ttk.Frame):
    def __init__(self, parent, title, *, opened=False):
        super().__init__(parent)
        self.title, self.opened = title, bool(opened)
        self.button = ttk.Button(self, command=self.toggle, takefocus=True)
        self.button.pack(anchor='w')
        self.body = ttk.Frame(self, padding=(0, 4))
        self.set_open(opened)
    def set_open(self, value):
        self.opened = bool(value)
        self.button.configure(text=('Hide ' if self.opened else 'Show ') + self.title)
        if self.opened: self.body.pack(fill='both', expand=True)
        else: self.body.pack_forget()
    def toggle(self): self.set_open(not self.opened)


class ColumnMenu:
    """Per-view column presets; row ordering never edits the recipe or job."""
    def __init__(self, parent, tree, presets, refresh, filter_var):
        self.tree, self.presets, self.refresh, self.filter_var = tree, presets, refresh, filter_var
        self.sort = None; self.descending = False
        self.preset = tk.StringVar(parent, value=next(iter(presets)))
        self.columns = tuple(tree['columns'])
        self.original = {c:tree.heading(c,'text') for c in self.columns}
        self.button = ttk.Menubutton(parent, text='Columns')
        self.menu = tk.Menu(self.button,tearoff=False); self.button.configure(menu=self.menu)
        for name in presets:
            self.menu.add_radiobutton(label=name,variable=self.preset,value=name,command=self.apply)
        self.menu.add_separator(); self.menu.add_command(label='Restore order and columns',command=self.reset)
        for column in self.columns:
            tree.heading(column, command=lambda c=column:self.open_column(c))
        self.apply()
    def apply(self):
        self.tree.configure(displaycolumns=self.presets[self.preset.get()])
        if hasattr(self.tree, 'game_tools_column_layout'): self.tree.game_tools_column_layout.fit_window()
    def reset(self):
        self.sort=None;self.descending=False;self.filter_var.set('');self.preset.set(next(iter(self.presets)));self.apply();self.refresh()
    def open_column(self,column):
        menu=tk.Menu(self.tree,tearoff=False)
        menu.add_command(label='Sort ascending',command=lambda:self.set_sort(column,False))
        menu.add_command(label='Sort descending',command=lambda:self.set_sort(column,True))
        menu.add_command(label='Filter this column…',command=lambda:self.filter_dialog(column))
        menu.add_command(label='Clear filters',command=lambda:self.filter_var.set(''))
        visible=list(self.tree['displaycolumns'])
        if column!='name' and len(visible)>1:
            menu.add_command(label='Hide column',command=lambda:self.tree.configure(displaycolumns=[c for c in visible if c!=column]))
        menu.add_command(label='Fit to content',command=lambda:self.tree.game_tools_column_layout.fit_text(column))
        try: menu.tk_popup(self.tree.winfo_pointerx(),self.tree.winfo_pointery())
        finally: menu.grab_release();menu.destroy()
    def set_sort(self,column,descending):
        self.sort=column;self.descending=descending;self.refresh()
    def filter_dialog(self,column):
        popup=tk.Toplevel(self.tree);popup.title('Filter '+self.original[column]);popup.transient(self.tree.winfo_toplevel())
        body=ttk.Frame(popup,padding=12);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Contains text').pack(anchor='w')
        text=tk.StringVar(popup);entry=ttk.Entry(body,textvariable=text,width=35);entry.pack(fill='x',pady=6)
        def commit(): self.filter_var.set(column+':'+text.get());popup.destroy()
        ttk.Button(body,text='Apply',command=commit).pack(side='right')
        ttk.Button(body,text='Cancel',command=popup.destroy).pack(side='right',padx=6)
        entry.bind('<Return>',lambda _e:commit());popup.bind('<Escape>',lambda _e:popup.destroy());entry.focus_set();popup.grab_set()
    def ordered(self,rows):
        if self.sort:
            col=self.sort
            rows=sorted(rows,key=lambda r:r.get(col,0) if col=='order' else str(r.get(col,'')).casefold(),reverse=self.descending)
        query=self.filter_var.get().strip().casefold()
        if not query:return rows
        if ':' in query and query.split(':',1)[0] in self.columns:
            col,term=query.split(':',1);return [r for r in rows if term in str(r.get(col,'')).casefold()]
        return [r for r in rows if query in ' '.join(str(v) for v in r.values()).casefold()]


class StretchScrollFrame(ScrollableFrame):
    """Use available height without losing overflow when details/text grow."""
    def __init__(self,parent,min_width=0):
        super().__init__(parent,min_width=min_width)
        self._stretch_job=None
        self.canvas.bind('<Configure>',self._queue_stretch,add='+')
        self.body.bind('<Configure>',self._queue_stretch,add='+')
        self.bind('<Destroy>',self._destroy_stretch,add='+')
    def _queue_stretch(self,_event=None):
        if self._stretch_job is None:self._stretch_job=self.after_idle(self._stretch)
    def _stretch(self):
        self._stretch_job=None
        target=max(self.body.winfo_reqheight(),self.canvas.winfo_height())
        if int(float(self.canvas.itemcget(self.item,'height') or 0))!=target:self.canvas.itemconfigure(self.item,height=target)
    def _destroy_stretch(self,event):
        if event.widget is self and self._stretch_job:
            self.after_cancel(self._stretch_job);self._stretch_job=None
    def close(self):
        if self._stretch_job:self.after_cancel(self._stretch_job);self._stretch_job=None
        super().close()


class FocusModPanel(ModWorkflowPanel):
    """A new view, inheriting original actions unchanged."""
    def __init__(self,parent,recipe_path=DEFAULT_RECIPE,data_root=None):
        ttk.Frame.__init__(self,parent,padding=6)
        self.recipe_path,self.data_root=Path(recipe_path),Path(data_root or default_data())
        self.recipe=load_recipe(self.recipe_path);self.job=None;self.worker=None
        self.peer_busy=lambda:False;self.cancel_event=threading.Event();self.messages=queue.Queue()
        self.mode=tk.StringVar(self,value='real-time');self.status=tk.StringVar(self,value='Choose a preset, then create a plan.')
        self.checks={};self.buttons={};self.query=tk.StringVar(self)
        self.body=StretchScrollFrame(self,min_width=340);self.body.pack(fill='both',expand=True);c=self.body.body
        ttk.Label(c,text=self.recipe['name'],font=('Segoe UI',11,'bold')).pack(anchor='w',pady=(0,4))
        self.preset_selector=ttk.Combobox(c,textvariable=self.mode,values=['real-time','turn-based'],state='readonly',width=13)
        # A separate, compact row keeps the editable mode control obvious.
        select=ttk.Frame(c);select.pack(fill='x',pady=(0,4))
        ttk.Label(select,text='Combat').pack(side='left',padx=(0,6))
        self.preset_selector.pack(in_=select,side='left')
        ttk.Button(select,text='Use preset',command=self.use_preset).pack(side='left',padx=4)
        self.choose_box=Disclosure(c,'optional mods');self.choose_box.pack(fill='x')
        for i,item in enumerate(self.recipe['items']):
            var=tk.BooleanVar(self,value=item['id'] in self.recipe['presets'].get('real-time',[]));self.checks[item['id']]=var
            ttk.Checkbutton(self.choose_box.body,text=item['name'],variable=var).grid(row=i,column=0,sticky='w')
        self.selection_label=tk.StringVar(self)
        ttk.Label(c,textvariable=self.selection_label).pack(anchor='w',pady=(0,4))
        for var in self.checks.values():var.trace_add('write',lambda *_:self.selection_summary())
        bar=FlowToolbar(c);bar.pack(fill='x',pady=(0,4));self.bar=bar
        for caption,action in [('Create plan',self.create_plan),('Download plan',self.download),('Import ZIP',self.import_one),('Prepare files',self.stage_one),('Stop',self.cancel_event.set)]:
            self.buttons[caption]=bar.add(caption,action)
        more=ttk.Menubutton(c,text='More');more_menu=tk.Menu(more,tearoff=False);more.configure(menu=more_menu)
        for label,fn in [('Open existing job',self.open_job),('Official download page',self.open_page),('Inspect game folder (read only)',self.inspect_game)]:more_menu.add_command(label=label,command=fn)
        more.pack(anchor='e')
        filters=ttk.Frame(c);filters.pack(fill='x',pady=4)
        ttk.Label(filters,text='Filter').pack(side='left',padx=(0,6));self.search=ttk.Entry(filters,textvariable=self.query);self.search.pack(side='left',fill='x',expand=True)
        self.tree=ttk.Treeview(c,columns=('order','name','version','status'),show='headings',height=11,selectmode='browse')
        for name,width in [('order',44),('name',240),('version',105),('status',190)]:
            self.tree.heading(name,text=name.title());self.tree.column(name,width=width,minwidth=44)
        self.tree.pack(fill='both',expand=True)
        self.column_layout=TableLayout(self.tree)
        self.columns=ColumnMenu(filters,self.tree,{'Essential':('name','version','status'),'Full':('order','name','version','status')},self.refresh,self.query)
        self.columns.button.pack(side='right',padx=(6,0));self.query.trace_add('write',lambda *_:self.refresh())
        yscroll=ttk.Scrollbar(c,orient='horizontal',command=self.tree.xview);yscroll.pack(fill='x');self.tree.configure(xscrollcommand=yscroll.set)
        self.tree.bind('<<TreeviewSelect>>',self.show_details)
        self.summary=tk.StringVar(self,value='Select a mod for its requirements and limitations.')
        self.summary_label=ttk.Label(c,textvariable=self.summary,wraplength=800,justify='left');self.summary_label.pack(fill='x',pady=6)
        self.state_label=ttk.Label(c,textvariable=self.status,wraplength=800,justify='left');self.state_label.pack(fill='x')
        self.boundary=ttk.Label(c,text='Prepared ≠ installed · UMM installs the mod ZIPs · game files are unchanged here.',wraplength=800,style='Focus.Scope.TLabel');self.boundary.pack(fill='x',pady=4)
        self.technical=Disclosure(c,'technical details');self.technical.pack(fill='both')
        self.details=tk.Text(self.technical.body,height=7,wrap='word',font=('Consolas',10));self.details.pack(fill='both',expand=True)
        self._last_result={};self.refresh();self.selection_summary();self.set_details({'status':'NOT_PLANNED'})
        self._poll_handle=self.after(150,self.poll);self.bind('<Destroy>',self.on_destroy,add='+')
        c.bind('<Configure>',self._wrap,add='+')
    def on_destroy(self,event):
        if event.widget is self:
            self.body.close();self.column_layout.close()
        super().on_destroy(event)
    def _wrap(self,event):
        if event.widget is self.body.body:
            width=max(230,event.width-14)
            for w in (self.summary_label,self.state_label,self.boundary):
                if int(float(w.cget('wraplength')))!=width:w.configure(wraplength=width)
    def selection_summary(self):
        chosen=[i['name'] for i in self.recipe['items'] if self.checks[i['id']].get()]
        self.selection_label.set(str(len(chosen))+' selected for next plan'+(' · current job unchanged' if self.job else ''))
    def refresh(self):
        previous=self.tree.selection();self.tree.delete(*self.tree.get_children())
        items=self.job.plan['items'] if self.job else self.recipe['items'];rows=[]
        for n,item in enumerate(items,1):
            state=self.job.latest(item['id'])['status'] if self.job else 'NOT_PLANNED'
            rows.append(dict(id=item['id'],order=n,name=item['name'],version=item.get('display_version',''),status=state))
        for row in self.columns.ordered(rows):self.tree.insert('','end',iid=row['id'],values=[row[c] for c in self.tree['columns']])
        if previous and self.tree.exists(previous[0]):self.tree.selection_set(previous[0])
        elif previous:self.summary.set('No visible selection. Clear the filter to reveal hidden items.')
        planned=self.job is not None
        for name in ('Download plan','Import ZIP','Prepare files'):self.buttons[name].configure(state='normal' if planned else 'disabled')
        self.selection_summary()
    def set_details(self,obj):
        self._last_result=obj;ModWorkflowPanel.set_details(self,obj)
        if isinstance(obj,dict) and 'status' in obj:self.status.set(concise_result(obj))
    def show_details(self,event=None):
        try:
            ident=self.selected();item=self.job.item(ident) if self.job else next(i for i in self.recipe['items'] if i['id']==ident)
            warnings=item.get('warnings',[])
            self.summary.set(item['name']+' · '+(' / '.join(warnings) if warnings else 'Review the official requirements before installation.'))
        except ModError:return
        super().show_details(event)
    def poll(self):
        try:self.after_cancel(self._poll_handle)
        except (tk.TclError,AttributeError):pass
        try:
            while True:
                result=self.messages.get_nowait();self.set_details(result);self.status.set(concise_result(result));self.refresh()
        except queue.Empty:pass
        self._poll_handle=self.after(150,self.poll)


class FocusAutomationPanel(AutomationPanel):
    """Same approval implementation; exact request preview is never optional."""
    def __init__(self,parent,service,status=None,peer_busy=None):
        ttk.Frame.__init__(self,parent,padding=6)
        self.service,self.shared_status=service,status;self.peer_busy=peer_busy or (lambda:False);self.tool_snapshot=lambda:{}
        self.worker=None;self.messages=queue.Queue();self._closed=False;self._poll=None
        self.watch=tk.BooleanVar(self,value=False);self.allow_client_requests=tk.BooleanVar(self,value=False)
        self.state=tk.StringVar(self,value='Local approval required · nothing runs on arrival.');self.buttons={}
        self.body=StretchScrollFrame(self,min_width=340);self.body.pack(fill='both',expand=True);c=self.body.body
        bar=FlowToolbar(c);bar.pack(fill='x')
        for caption,action in [('Refresh requests',self.refresh),('Import AI request',self.import_request),('Copy AI context',self.copy_context)]:self.buttons[caption]=bar.add(caption,action)
        self.connection=Disclosure(c,'connection and sharing');self.connection.pack(fill='x',pady=4)
        options=FlowToolbar(self.connection.body);options.pack(fill='x')
        for caption,action in [('Save AI context',self.save_context),('Share report summary',self.share_report),('Share tool status',self.share_tools),('Copy client setup',self.copy_client_setup),('Capabilities',self.show_capabilities)]:self.buttons[caption]=options.add(caption,action)
        ttk.Checkbutton(self.connection.body,text='Refresh requests while open (never auto-approve)',variable=self.watch,command=self.toggle_watch).pack(anchor='w')
        ttk.Checkbutton(self.connection.body,text='Allow proposals in copied client setup (still requires local approval)',variable=self.allow_client_requests).pack(anchor='w')
        ttk.Label(c,textvariable=self.state,wraplength=780).pack(fill='x',pady=4)
        self.tree=ttk.Treeview(c,columns=('operation','status','id'),show='headings',height=7,selectmode='browse')
        for col,width in [('operation',190),('status',230),('id',180)]:self.tree.heading(col,text=col.title());self.tree.column(col,width=width)
        self.tree.pack(fill='both',expand=True);self.layout=TableLayout(self.tree);self.tree.bind('<<TreeviewSelect>>',self.show_selected)
        scroll=ttk.Scrollbar(c,orient='horizontal',command=self.tree.xview);scroll.pack(fill='x');self.tree.configure(xscrollcommand=scroll.set)
        ttk.Label(c,text='Exact request / latest result',font=('Segoe UI',10,'bold')).pack(anchor='w',pady=(6,2))
        self.output=tk.Text(c,wrap='word',height=8,font=('Consolas',10));self.output.pack(fill='both',expand=True)
        actions=FlowToolbar(c);actions.pack(fill='x',pady=5)
        for caption,action in [('Approve selected',self.approve),('Reject selected',self.reject),('Stop active operation',self.stop)]:self.buttons[caption]=actions.add(caption,action)
        ttk.Label(c,text='Copy ≠ send · client setup stays private · AI cannot approve itself.',wraplength=780,style='Focus.Scope.TLabel').pack(fill='x')
        self.write({'status':'No request selected','note':'Select a request to inspect the exact action before approval.'})
        self.bind('<Destroy>',self._destroy,add='+')
