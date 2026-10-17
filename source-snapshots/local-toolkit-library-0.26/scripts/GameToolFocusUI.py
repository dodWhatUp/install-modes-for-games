"""Focus: an optional dense shell over existing Hub editors and services.

Display state lives in a separate CAS-protected file. No changing the active
release, native input, capture state, mod selections or approval policy.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import tkinter as tk
from tkinter import ttk, font as tkfont

VERSION='0.1.0'
DEFAULT={'schema_version':1,'zoom':100,'density':'Compact','navigation':True,'route':'mods'}
LABELS={'mods':'Mods','automation':'AI requests','studio':'Picture & input','overlays':'Overlays',
        'comparison':'Compare results','reports':'Reports','sessions':'Diagnostics','catalog':'Catalog',
        'tools':'Connected tools','sensors':'Sensors','rtss':'RTSS','updates':'Updates','data':'User data','guide':'Help'}
ORDER=tuple(LABELS)
SCOPES={'mods':'Plan → download → prepare → install with UMM',
        'automation':'Local approval · no automatic execution',
        'studio':'Native Studio · zoom here changes the shell only',
        'overlays':'Display choices are separate from native input mappings',
        'comparison':'Saved reports · not a live benchmark','reports':'Original saved evidence',
        'sessions':'Offline preparation · games and capture stay stopped',
        'catalog':'Recorded capabilities are not proof of installation',
        'tools':'Read-only inventory · interface launch is explicit',
        'sensors':'Provider observations · not benchmark acceptance',
        'rtss':'Provider-defined counters · no capture started',
        'updates':'Inspect before updating · user data stays separate',
        'data':'Private data · explicit backup/import actions','guide':'Capabilities and limits'}


class FocusPreferences:
    """Presentation-only, checked against the bytes read at open; no silent merge."""
    def __init__(self,path):
        self.path=Path(path);self.raw=None;self.value=dict(DEFAULT);self.error=None
        try:
            if self.path.exists():
                if self.path.is_symlink() or self.path.stat().st_size>8192:raise ValueError('Invalid view-preference file')
                self.raw=self.path.read_bytes();value=json.loads(self.raw)
                self.value=self.validate(value)
        except (ValueError,OSError) as error:self.error=str(error)
    @staticmethod
    def validate(value):
        if not isinstance(value,dict) or set(value)!=set(DEFAULT) or type(value['schema_version']) is not int or value['schema_version']!=1:raise ValueError('Unsupported Focus view schema')
        if type(value['zoom']) is not int or value['zoom'] not in range(80,201,10):raise ValueError('Zoom must be 80–200% in 10% steps')
        if value['density'] not in ('Compact','Comfortable') or type(value['navigation']) is not bool:raise ValueError('Invalid display preferences')
        if value['route'] not in ORDER:raise ValueError('Unknown route')
        return dict(value)
    def save(self,value):
        if self.error:raise ValueError('Original preferences retained: '+self.error)
        value=self.validate(value)
        if self.path.is_symlink():raise ValueError('View file became a link')
        current=self.path.read_bytes() if self.path.exists() else None
        if current!=self.raw:raise ValueError('Another window changed this view; it was not overwritten')
        raw=(json.dumps(value,indent=2)+'\n').encode()
        if raw==self.raw:return
        self.path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix='.focus-view-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'wb') as out:out.write(raw);out.flush();os.fsync(out.fileno())
            if (self.path.read_bytes() if self.path.exists() else None)!=self.raw:raise ValueError('View changed during save')
            os.replace(name,self.path);self.raw=raw;self.value=value
        finally:
            if os.path.exists(name):os.unlink(name)


class ZoomController:
    """Scale owned Tk presentation without changing native Studio or operational state."""
    def __init__(self,root):
        self.root=root;self.records=[];self.styles={};self.zoom=100;self.density='Compact'
    def register(self,container):
        seen={str(w) for w,_,_ in self.records}
        def visit(widget):
            if str(widget) not in seen:
                try:
                    if 'font' in widget.keys() and widget.cget('font'):
                        self.records.append((widget,'font',widget.cget('font')))
                    elif isinstance(widget,ttk.Widget) and 'style' in widget.keys():
                        self.records.append((widget,'style',widget.cget('style') or widget.winfo_class()))
                except tk.TclError:pass
                seen.add(str(widget))
            for child in widget.winfo_children():
                # Native child windows are not Tk descendants and are never traversed.
                visit(child)
        visit(container)
    def apply(self,zoom,density):
        if zoom not in range(80,201,10) or density not in ('Compact','Comfortable'):raise ValueError('Unsupported display setting')
        self.zoom,self.density=zoom,density;s=ttk.Style(self.root);factor=zoom/100
        for widget,kind,original in self.records:
            if not widget.winfo_exists():continue
            try:
                if kind=='font':
                    actual=tkfont.Font(root=self.root,font=original).actual();size=max(9,round(abs(actual['size'])*factor))
                    widget.configure(font=(actual['family'],size,actual['weight'],actual['slant']))
                else:
                    key='FocusZoom'+str(zoom)+density+'.'+original
                    if key not in self.styles:
                        font=s.lookup(original,'font') or 'TkDefaultFont';actual=tkfont.Font(root=self.root,font=font).actual()
                        attrs={'font':(actual['family'],max(9,round(abs(actual['size'])*factor)),actual['weight'])}
                        if original.endswith('Treeview'):attrs['rowheight']=round((29 if density=='Compact' else 36)*factor)
                        if original.endswith(('TButton','TMenubutton')):attrs['padding']=(round(8*factor),round((3 if density=='Compact' else 7)*factor))
                        if original.endswith(('TEntry','TCombobox')):attrs['padding']=round((3 if density=='Compact' else 6)*factor)
                        s.configure(key,**attrs);self.styles[key]=True
                    widget.configure(style=key)
            except tk.TclError:continue
    def restore(self):
        for widget,kind,original in self.records:
            try:
                if widget.winfo_exists():widget.configure(**{kind:original})
            except tk.TclError:pass


class FocusSurface:
    """One command strip + narrow route rail + full-width existing workspace."""
    def __init__(self,root,header,banner,workspace,status,appearance,data_dir,mod_integration=None):
        self.root,self.header,self.banner,self.w,self.status,self.appearance=root,header,banner,workspace,status,appearance
        self.mod_integration=mod_integration;self.active=False;self.closed=False;self._layout_job=None;self._status_job=None;self._manual_navigation=False
        self.preferences=FocusPreferences(Path(data_dir)/'focus-view.json')
        self.settings=dict(self.preferences.value)
        self.original_mode=appearance.current;self.original_view=workspace.export_view();self.original_preview=appearance.preview_only
        self.original_header_pack=header.pack_info();self.original_banner_pack=banner.pack_info()
        self.title=tk.StringVar(root,value='Mods');self.scope=tk.StringVar(root)
        self.query=tk.StringVar(root);self.zoom=tk.IntVar(root,value=self.settings['zoom']);self.density=tk.StringVar(root,value=self.settings['density'])
        self.nav=tk.BooleanVar(root,value=self.settings['navigation']);self.details=tk.BooleanVar(root,value=False)
        self.commands=ttk.Frame(root,padding=(8,5));self.commands.columnconfigure(1,weight=1)
        self.brand=ttk.Label(self.commands,text='Game Tools',font=('Segoe UI',12,'bold'));self.brand.grid(row=0,column=0,sticky='w',padx=(0,12))
        self.search_slot=ttk.Frame(self.commands);self.search_slot.grid(row=0,column=1,sticky='ew',padx=(0,8));self.search_slot.columnconfigure(1,weight=1)
        self.search_label=ttk.Label(self.search_slot,text='Find');self.search_label.grid(row=0,column=0,padx=(0,5))
        self.selector=ttk.Combobox(self.search_slot,textvariable=self.query,width=26);self.selector.grid(row=0,column=1,sticky='ew')
        self.selector.configure(values=[LABELS[r] for r in ORDER if r in workspace.route_tabs])
        self.selector.bind('<Return>',self.commit_search);self.selector.bind('<<ComboboxSelected>>',self.commit_search);self.selector.bind('<Escape>',self.cancel_search)
        self.selector.bind('<FocusIn>',lambda _e:self.selector.selection_range(0,'end'))
        self.controls=ttk.Frame(self.commands);self.controls.grid(row=0,column=2,sticky='e')
        self.nav_button=ttk.Button(self.controls,text='Navigation',command=self.toggle_navigation);self.nav_button.pack(side='left')
        self.zoom_button=ttk.Menubutton(self.controls,text=f'{self.zoom.get()}%');self.zoom_button.pack(side='left',padx=4)
        zm=tk.Menu(self.zoom_button,tearoff=False)
        for level in (80,90,100,110,120,130,140,150,160,170,180,190,200):zm.add_radiobutton(label=str(level)+'%',variable=self.zoom,value=level,command=self.apply_display)
        self.zoom_button.configure(menu=zm)
        self.view_button=ttk.Menubutton(self.controls,text='View');self.view_button.pack(side='left')
        vm=tk.Menu(self.view_button,tearoff=False);self.view_button.configure(menu=vm)
        for d in ('Compact','Comfortable'):vm.add_radiobutton(label=d,variable=self.density,value=d,command=self.apply_display)
        vm.add_separator();vm.add_checkbutton(label='Show navigation',variable=self.nav,command=self.apply_navigation)
        vm.add_checkbutton(label='Show page explanation',variable=self.details,command=self.show_details)
        vm.add_command(label='Reset this view',command=self.reset);vm.add_command(label='Save this view',command=self.save)
        vm.add_separator();vm.add_command(label='Original navigation (this session)',command=self.deactivate)
        vm.add_command(label='Identify UI components',command=lambda:appearance.set_identification(not appearance.markers.enabled))
        self.context=ttk.Frame(self.commands);self.context.grid(row=1,column=0,columnspan=3,sticky='ew',pady=(5,0));self.context.columnconfigure(0,weight=1)
        self.title_widget=ttk.Label(self.context,textvariable=self.title,font=('Segoe UI',12,'bold'));self.title_widget.grid(row=0,column=0,sticky='w')
        self.boundary=ttk.Label(self.context,textvariable=self.scope,style='Focus.Scope.TLabel',wraplength=780);self.boundary.grid(row=1,column=0,sticky='ew')
        self.more=ttk.Button(self.context,text='Details',command=self.toggle_details);self.more.grid(row=0,column=1,sticky='e')
        self.stop=ttk.Button(self.context,text='Stop mod / AI work',command=self.stop_work);self.stop.grid(row=0,column=2,padx=(6,0));self.stop.state(['disabled'])
        self.explanation=ttk.Label(self.commands,textvariable=self.w.description,wraplength=900,justify='left')
        self.return_button=ttk.Button(header,text='Focus layout',command=self.activate)
        self._tab_binding=workspace.notebook.bind('<<NotebookTabChanged>>',self.page_changed,add='+')
        self._configure=root.bind('<Configure>',self.queue_layout,add='+')
        self._query_trace=self.query.trace_add('write',self.filter_routes)
        self._keys=[]
        for sequence,change in [('<Control-equal>',10),('<Control-plus>',10),('<Control-minus>',-10),('<Control-0>',0)]:
            self._keys.append((sequence,root.bind(sequence,lambda e,c=change:self.zoom_key(e,c),add='+')))
        self._keys.append(('<Control-MouseWheel>',root.bind('<Control-MouseWheel>',self.wheel_zoom,add='+')))
        self.scaler=ZoomController(root);self._status_trace=status.trace_add('write',self.queue_state)
        self._activity_traces=[]
        if self.mod_integration:
            for variable in (self.mod_integration.mods.status,self.mod_integration.automation.state):
                self._activity_traces.append((variable,variable.trace_add('write',self.queue_state)))
        self.activate()
        initial=self.settings['route']
        if initial in self.w.route_tabs:self.navigate(initial)
        self.root.game_tools_focus=self
    def activate(self):
        if self.active or self.closed:return
        self.appearance.preview('Compact');self.w.view.set('Features');self.w._rebuild()
        self.active=True
        self.header.pack_forget();self.banner.pack_forget();self.return_button.pack_forget()
        self.commands.pack(fill='x',before=self.w.frame)
        self.w.frame.pack_configure(padx=6)
        self.w.toolbar.grid_remove();self.w.breadcrumb.grid_remove();self.w.view_label.grid_remove();self.w.result_widget.grid_remove()
        self.w.tree.configure(show='tree');self.w.tree.column('#0',minwidth=110,width=178,stretch=True)
        self.w.horizontal_scroll.grid_remove();self.w.sidebar.configure(padding=(4,3));self.w.sidebar_width=182
        self.w.sidebar.rowconfigure(0,weight=0);self.w.sidebar.rowconfigure(1,weight=0)
        s=ttk.Style(self.root);s.configure('Focus.Scope.TLabel',foreground='#475569',font=('Segoe UI',10))
        s.configure('TFrame',background='#f5f7fa');s.configure('TLabel',background='#f5f7fa',foreground='#172b4d')
        self.scaler.register(self.root);self.rebuild_routes();self.apply_display(persist=False);self.apply_navigation(persist=False);self.page_changed()
    def deactivate(self):
        if not self.active:return
        self.active=False;self.scaler.restore();self.commands.pack_forget();self.explanation.grid_remove()
        self.header.pack(**self.original_header_pack);self.header.pack_configure(before=self.w.frame)
        self.banner.pack(**self.original_banner_pack);self.banner.pack_configure(after=self.header)
        self.w.toolbar.grid();self.w.view_label.grid();self.w.result_widget.grid();self.w.horizontal_scroll.grid()
        self.appearance.preview(self.original_mode);self.w.restore_view(self.original_view);self.w.set_presentation(self.original_mode)
        self.w.frame.pack_configure(padx=12);self.return_button.pack(side='left',padx=8)
        self.status.set('Original layout · Focus can be restored without changing jobs, drafts or settings.')
    def filter_routes(self,*_):
        if not self.active:return
        q=self.query.get().casefold().strip()
        matches=[LABELS[r] for r in ORDER if r in self.w.route_tabs and all(t in (LABELS[r]+' '+r+' '+str(self.w.registry.feature_for_route(r))).casefold() for t in q.split())]
        self.selector.configure(values=matches)
        # Typing never selects a route, changes the current editor or hides its draft.
    def commit_search(self,_event=None):
        text=self.query.get().strip().casefold();matches=[]
        for r in ORDER:
            if r not in self.w.route_tabs:continue
            if text in (r.casefold(),LABELS[r].casefold()):matches=[r];break
            record=self.w.registry.feature_for_route(r)
            if text and all(term in (LABELS[r]+' '+r+' '+str(record)).casefold() for term in text.split()):matches.append(r)
        if len(matches)==1:self.navigate(matches[0]);self.query.set('')
        else:self.status.set('Choose one matching workspace; the current page is unchanged.')
        return 'break'
    def cancel_search(self,_event=None):self.query.set('');return 'break'
    def focus_search(self,event=None):
        if self.root.grab_current() is not None:return None
        self.selector.focus_set();self.selector.selection_range(0,'end');return 'break'
    def rebuild_routes(self):
        tree=self.w.tree;tree.delete(*tree.get_children());self.w._rows={}
        groups=[('Work',('mods','automation','overlays','studio')),('Evidence',('comparison','reports','sessions')),('Tools & setup',('catalog','tools','sensors','rtss','updates','data','guide'))]
        for index,(label,routes) in enumerate(groups):
            present=[r for r in routes if r in self.w.route_tabs]
            if not present:continue
            parent='focus.group.'+str(index);tree.insert('','end',iid=parent,text=label,open=True,tags=('domain',))
            for r in present:
                record=self.w.registry.feature_for_route(r)
                if not record:continue
                self.w._rows[record['id']]=record;tree.insert(parent,'end',iid=record['id'],text=LABELS[r])
        self.w._select_active_row()
    def navigate(self,route):
        record=self.w.registry.feature_for_route(route)
        if record and self.w.route(record['id']):self.page_changed();return True
        self.status.set('This workspace is not available in the current source/installation.');return False
    def page_changed(self,_event=None):
        if not self.active:return
        route=next((r for r,t in self.w.route_tabs.items() if t==self.w.notebook.select()),None)
        self.title.set(LABELS.get(route,route or 'Workspace'))
        self.scope.set(SCOPES.get(route,'Existing page · actions remain explicit'))
        if route in ORDER:self.settings['route']=route
        self.w.breadcrumb.grid_remove();self.state_changed();self.queue_layout()
    def queue_state(self,*_):
        if self.closed or self._status_job:return
        self._status_job=self.root.after_idle(self._flush_state)
    def _flush_state(self):
        self._status_job=None;self.state_changed()
    def state_changed(self,*_):
        if not self.active:return
        busy=self.mod_integration and (bool(self.mod_integration.mods.worker and self.mod_integration.mods.worker.is_alive()) or self.mod_integration.automation.busy)
        self.stop.configure(state='normal' if busy else 'disabled')
    def stop_work(self):
        if self.mod_integration:
            self.mod_integration.mods.cancel_event.set();self.mod_integration.automation.stop()
        self.status.set('Stop requested at the existing safe boundary; no processes killed or actions replayed.')
    def toggle_details(self):self.details.set(not self.details.get());self.show_details()
    def show_details(self):
        if self.details.get():self.explanation.grid(row=2,column=0,columnspan=3,sticky='ew',pady=5)
        else:self.explanation.grid_remove()
        self.more.configure(text='Hide details' if self.details.get() else 'Details')
    def toggle_navigation(self):
        visible=str(self.w.sidebar) in self.w.splitter.panes()
        self.nav.set(not visible);self.apply_navigation();self.queue_layout()
    def apply_navigation(self,persist=True):
        self._manual_navigation=bool(persist)
        self.settings['navigation']=bool(self.nav.get());self.w.show_navigation.set(self.nav.get());self.w._navigation_forced=False;self.w._visibility_changed()
        if persist:self.save()
    def apply_display(self,persist=True):
        self.settings.update(zoom=self.zoom.get(),density=self.density.get())
        self.zoom_button.configure(text=f'{self.zoom.get()}%');self.scaler.register(self.root);self.scaler.apply(self.zoom.get(),self.density.get())
        self.w.sidebar_width=max(150,round(182*self.zoom.get()/100));self.w._schedule_sash();self.queue_layout()
        if persist:self.save()
    def zoom_key(self,event,change):
        if not self.active or self.root.grab_current() is not None:return None
        focused=self.root.focus_get()
        if focused is None or focused.winfo_toplevel()!=self.root:return None
        self.zoom.set(100 if change==0 else max(80,min(200,self.zoom.get()+change)));self.apply_display();return 'break'
    def wheel_zoom(self,event):
        if not getattr(event,'delta',0):return None
        return self.zoom_key(event,10 if event.delta>0 else -10)
    def queue_layout(self,event=None):
        if not self.active or self.closed:return
        if event is not None and event.widget is not self.root:return
        if self._layout_job is None:self._layout_job=self.root.after_idle(self.layout)
    def layout(self):
        self._layout_job=None
        if not self.active or self.closed:return
        width=max(320,self.root.winfo_width());narrow=width<round(820*self.zoom.get()/100)
        self.brand.grid_configure(row=0,column=0)
        self.controls.grid_configure(row=0,column=2)
        self.search_slot.grid_configure(row=1 if narrow else 0,column=0 if narrow else 1,columnspan=3 if narrow else 1,pady=(4,0) if narrow else 0)
        self.context.grid_configure(row=2 if narrow else 1)
        if self.details.get():self.explanation.grid_configure(row=3 if narrow else 2)
        wrap=max(240,width-32)
        if int(float(self.boundary.cget('wraplength')))!=wrap:self.boundary.configure(wraplength=wrap)
        if int(float(self.explanation.cget('wraplength')))!=wrap:self.explanation.configure(wraplength=wrap)
        # Auto collapse is visual only, and never changes the saved preference.
        self.w.show_navigation.set(self.nav.get() and (self._manual_navigation or width>=round(790*self.zoom.get()/100)));self.w._visibility_changed()
        self.nav_button.configure(text='Hide navigation' if str(self.w.sidebar) in self.w.splitter.panes() else 'Navigation')
    def reset(self):
        route=self.settings['route'];self.settings=dict(DEFAULT,route=route);self.zoom.set(100);self.density.set('Compact');self.nav.set(True);self.details.set(False)
        self.show_details();self.apply_display(persist=False);self.apply_navigation(persist=False);self.save()
    def save(self):
        self.settings.update(zoom=self.zoom.get(),density=self.density.get(),navigation=self.nav.get())
        try:self.preferences.save(self.settings)
        except (OSError,ValueError) as error:self.status.set('View is session-only: '+str(error))
    def close(self):
        if self.closed:return
        self.closed=True
        for variable,token in self._activity_traces:variable.trace_remove('write',token)
        if self._status_job:
            try:self.root.after_cancel(self._status_job)
            except tk.TclError:pass
        if self._layout_job:
            try:self.root.after_cancel(self._layout_job)
            except tk.TclError:pass
        self.w.notebook.unbind('<<NotebookTabChanged>>',self._tab_binding)
        self.root.unbind('<Configure>',self._configure)
        for sequence,ident in self._keys:self.root.unbind(sequence,ident)
        self.query.trace_remove('write',self._query_trace);self.status.trace_remove('write',self._status_trace)
        # Do not persist changes made by the original interface through this view.
        self.appearance.preview_only=True
