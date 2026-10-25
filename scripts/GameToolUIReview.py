"""Parallel UI preview over the existing mod and file-service owners."""
from __future__ import annotations
import argparse,json,os,queue,subprocess,sys,threading,webbrowser
from pathlib import Path
import tkinter as tk
from urllib.parse import urlsplit
from tkinter import ttk,messagebox,simpledialog,filedialog
from GameToolCompactUI import Selector,FlowToolbar,ScrollableFrame,window_bounds
from GameToolUIReviewModel import ReviewModel,VERSION,PAGES,MANAGERS,TARGETS
from GameToolUIReviewWidgets import Section,Visibility,ResourcePane,SchemaEditor,WindowPin,theme
from GameToolUIReviewSearch import Finder,SCOPES,group_for
from game_mod_ops.safety import ModError

class ReviewApp(ttk.Frame):
    def __init__(self,root,model,initial_page=None):
        self.root,self.model=root,model;self.page=initial_page or model.view['page'];self.instance=None;self.observation=None;self.variables={};self.sections={};self.rows=[];self.resource_id=None;self.floating=[];self.closed=False;self.worker=None;self.events=queue.Queue();self.pending=False;self.token=0
        self.finder=None;self.pending_result=None;self.field_widgets={};self.action_widgets={}
        self.status=tk.StringVar(root,value='Parallel preview • current installation and game files remain unchanged')
        self.manager=tk.StringVar(root,value=model.view.get('manager','vortex'));self.game_id=model.view.get('game_id');self.profile_id=None
        self.dark=tk.BooleanVar(root,value=model.view.get('theme')=='Dark');self.zoom=tk.StringVar(root,value=str(model.view.get('zoom',100)))
        self.palette,self.font=theme(root,self.dark.get(),int(self.zoom.get()));super().__init__(root,style='Review.TFrame',padding=12);self.pack(fill='both',expand=True)
        root.title('Game Tools UI Preview '+VERSION+' — parallel review');w,h,mw,mh=window_bounds(root.winfo_screenwidth(),root.winfo_screenheight());root.geometry(f'{w}x{h}');root.minsize(mw,mh)
        top=ttk.Frame(self,style='Review.TFrame');top.pack(fill='x');ttk.Label(top,text='Game Tools · UI Preview',style='Review.Title.TLabel').pack(side='left')
        ttk.Label(top,text='  '+VERSION+'  |  separate review version',style='Review.TLabel').pack(side='left')
        self.dark_button=ttk.Checkbutton(top,text='Dark',variable=self.dark,command=self.restyle);self.dark_button.pack(side='right')
        z=ttk.Combobox(top,textvariable=self.zoom,values=['90','100','125','150'],width=5,state='readonly');z.pack(side='right',padx=8);z.bind('<<ComboboxSelected>>',lambda _:self.restyle());self.zoom_box=z
        context=ttk.Frame(self,style='Review.TFrame');context.pack(fill='x',pady=10);context.columnconfigure(1,weight=1);context.columnconfigure(3,weight=1)
        ttk.Label(context,text='Game',style='Review.TLabel').grid(row=0,column=0,padx=(0,8));self.game=Selector(context,on_select=self.choose_game);self.game.grid(row=0,column=1,sticky='ew')
        ttk.Label(context,text='Installation',style='Review.TLabel').grid(row=0,column=2,padx=10);self.installation=Selector(context,on_select=self.choose_instance);self.installation.grid(row=0,column=3,sticky='ew')
        findbar=ttk.Frame(self,style='Review.TFrame');findbar.pack(fill='x',pady=(0,8));self.find_button=ttk.Button(findbar,text='Find settings & functions…  Ctrl+F',command=self.open_finder);self.find_button.pack(side='left')
        self.pin=WindowPin(findbar,root,model.view.setdefault('window_pins',{}).get('main',False),lambda value:self.save_pin('main',value));self.pin.pack(side='right',padx=8)
        shell=ttk.Frame(self,style='Review.TFrame');shell.pack(fill='both',expand=True);shell.columnconfigure(1,weight=1);shell.rowconfigure(0,weight=1)
        self.nav=ttk.Frame(shell,style='Review.TFrame',padding=(0,0,12,0));self.nav.grid(row=0,column=0,sticky='ns')
        for key,label in PAGES.items():ttk.Button(self.nav,text=label,style='Review.TButton',command=lambda k=key:self.navigate(k)).pack(fill='x',pady=(0,7))
        ttk.Label(self.nav,text='Parallel UI review\nDrafts saved separately\nApply requires confirmation',style='Review.TLabel',wraplength=180).pack(anchor='w',pady=12)
        self.scroll=ScrollableFrame(shell,min_width=300);self.scroll.grid(row=0,column=1,sticky='nsew');self.body=self.scroll.body;self._wrap_job=None
        self.scroll.canvas.bind('<Configure>',self.canvas_layout)
        header=ttk.Frame(self.body,style='Review.TFrame');header.pack(fill='x',pady=(0,8));self.title=tk.StringVar(root);ttk.Label(header,textvariable=self.title,style='Review.Title.TLabel').pack(side='left')
        self.visibility=Visibility(header,self.hide_section);self.visibility.pack(side='right')
        jumps=FlowToolbar(self.body);jumps.pack(fill='x',pady=(0,8))
        jumps.add('Refresh files',self.refresh);jumps.add('Locations',lambda:self.jump_section('locations'));jumps.add('Export / program',lambda:self.jump_section('handoff'))
        self.content=ttk.Frame(self.body,style='Review.TFrame');self.content.pack(fill='both',expand=True)
        bottom=ttk.Frame(self,style='Review.TFrame');bottom.pack(fill='x',pady=(8,0));self.progress=ttk.Progressbar(bottom,mode='indeterminate',length=90);self.progress.pack(side='right');ttk.Label(bottom,textvariable=self.status,style='Review.TLabel',wraplength=1000).pack(side='left',fill='x',expand=True)
        self.game_rows=model.games();self.game.set_choices([(r['game_id'],r['name']) for r in self.game_rows]);default=next((g['game_id'] for g in self.game_rows if g['instances']),self.game_rows[0]['game_id'] if self.game_rows else None)
        self.game_id=self.game_id if any(g['game_id']==self.game_id for g in self.game_rows) else default
        self.game.select(self.game_id);self.choose_game(self.game_id);self._poll=self.after(80,self.poll)
        root.protocol('WM_DELETE_WINDOW',self.close);root.bind('<Control-r>',lambda _:self.refresh());root.bind('<Control-k>',lambda _:self.game.focus_set())
        root.bind('<Control-f>',lambda _:self.open_finder());root.bind('<Control-Shift-F>',lambda _:self.open_finder(SCOPES[1]))
    @property
    def busy(self):return bool(self.worker and self.worker.is_alive())
    def safe(self,fn):
        try:return fn()
        except (ModError,ValueError,OSError,KeyError,RuntimeError,tk.TclError) as error:self.status.set(str(error));messagebox.showerror('Preview needs attention',str(error),parent=self.root)
    def save_pin(self,key,value):
        self.model.view.setdefault('window_pins',{})[key]=bool(value);self.model.save_view()
    def open_finder(self,scope=SCOPES[0]):
        self.stash()
        if self.finder and self.finder.winfo_exists():self.finder.lift();self.finder.entry.focus_set();return self.finder
        self.finder=Finder(self,scope);return self.finder
    def action(self,bar,label,fn,key):
        button=bar.add(label,lambda:self.safe(fn));self.action_widgets[key]=button;return button
    def reveal_result(self,item):
        # Discovery can navigate and focus. It must never invoke a result action.
        self.stash();target_game=item.get('game_id');target_instance=item.get('instance')
        if target_game and target_game!=self.game_id:self.game.select(target_game);self.choose_game(target_game)
        if target_instance and target_instance!=self.instance:self.installation.select(target_instance);self.choose_instance(target_instance)
        if item['page']!=self.page:self.navigate(item['page'])
        self.pending_result=item
        if not self.busy and not self.pending:self.finish_reveal()
    def finish_reveal(self):
        item=self.pending_result
        if item is None:return
        if item.get('instance') and item['instance']!=self.instance:self.pending_result=None;self.status.set('The selected installation changed. Search again.');return
        self.pending_result=None;section=item.get('section')
        if section:self.jump_section(section)
        widget=None
        if item.get('field_id'):widget=self.field_widgets.get(item['field_id'])
        elif item.get('resource_id') and hasattr(self,'resource_pane'):
            ident=item['resource_id'];self.resource_pane.selector.select(ident);self.select_resource(ident);widget=self.resource_pane.selector
        elif item.get('action_id'):
            key=item['action_id'];widget={'pin':self.pin,'find':self.find_button,'dark':self.dark_button,'zoom':self.zoom_box,'show-hide':self.visibility,'game':self.game,'installation':self.installation}.get(key) or self.action_widgets.get(key)
        self.root.update_idletasks()
        if widget and widget.winfo_exists():
            self.root.lift();widget.focus_set();top=widget.winfo_rooty()-self.body.winfo_rooty()
            if section:self.scroll.canvas.yview_moveto(max(0,top-70)/max(1,self.body.winfo_height()))
        self.status.set('Found: '+item['breadcrumb']+' • revealed only; no value changed or function run.')
    def restyle(self):
        self.palette,self.font=theme(self.root,self.dark.get(),int(self.zoom.get()));self.model.view.update(theme='Dark' if self.dark.get() else 'Light',zoom=int(self.zoom.get()));self.model.save_view()
        self.schedule_wrap()
    def canvas_layout(self,event):
        width=max(300,event.width)
        if int(float(self.scroll.canvas.itemcget(self.scroll.item,'width')))!=width:self.scroll.canvas.itemconfigure(self.scroll.item,width=width)
        self.schedule_wrap()
    def schedule_wrap(self):
        if self._wrap_job is None and not self.closed:self._wrap_job=self.after_idle(self.wrap_labels)
    def wrap_labels(self):
        self._wrap_job=None;width=max(220,self.scroll.canvas.winfo_width()-55);stack=list(self.content.winfo_children())
        while stack:
            widget=stack.pop();stack.extend(widget.winfo_children())
            if isinstance(widget,ttk.Label) and int(widget.cget('wraplength') or 0)>0 and int(widget.cget('wraplength'))!=width:widget.configure(wraplength=width)
    def stash(self):
        if self.instance and self.variables:self.model.view['drafts'][self.instance]={k:v.get() for k,v in self.variables.items()}
        self.model.view.update(page=self.page,game_id=self.game_id,instance_id=self.instance,manager=self.manager.get());self.model.save_view()
    def choose_game(self,game_id):
        if game_id is None:return
        self.stash();self.game_id=game_id;self.instance=None;self.variables={};rows=self.model.instances(game_id);self.installation.set_choices([(r['instance_id'],r['instance_id']) for r in rows])
        preferred=self.model.view.get('instance_id');ident=next((r['instance_id'] for r in rows if r['instance_id']==preferred),rows[0]['instance_id'] if rows else None);self.installation.select(ident);self.choose_instance(ident)
    def choose_instance(self,ident):
        self.stash()
        for win in self.floating:
            if win.winfo_exists():win.destroy()
        self.floating=[];self.instance=ident;self.observation=None;self.variables={};self.token+=1;self.render();self.refresh()
    def navigate(self,page):
        self.stash();self.page=page;self.token+=1;self.render();self.refresh()
    def section(self,key,title):
        card=Section(self.content,title,lambda:self.hide_section(key,True));self.sections[key]=(card,title)
        if not self.hidden(key):card.pack(fill='both',expand=True,pady=(0,10))
        return card.body
    def hidden(self,key):return self.model.view['hidden'].get(self.page+':'+key,False)
    def hide_section(self,key,hidden):
        self.model.view['hidden'][self.page+':'+key]=hidden;self.model.save_view()
        for ident,(card,_) in self.sections.items():
            card.pack_forget()
            if not self.hidden(ident):card.pack(fill='both',expand=True,pady=(0,10))
        self.visibility.set_sections([(k,v[1]) for k,v in self.sections.items()],self.hidden)
        self.status.set('Section visibility changed. Draft settings and feature states are preserved.')
    def jump_section(self,key):
        if key not in self.sections:self.status.set('That section is available on the working pages.');return
        self.hide_section(key,False);self.root.update_idletasks();card=self.sections[key][0]
        top=card.winfo_rooty()-self.body.winfo_rooty();self.scroll.canvas.yview_moveto(max(0,top)/max(1,self.body.winfo_height()))
    def clear(self):
        if hasattr(self,'resource_pane'):self.resource_pane.close();del self.resource_pane
        for widget in self.content.winfo_children():widget.destroy()
        self.sections={};self.field_widgets={};self.action_widgets={}
    def render(self):
        self.clear();self.title.set(PAGES[self.page]);self.resource_id=None
        if self.page=='mods':self.render_mods()
        elif self.page=='review':self.render_review()
        else:self.render_general()
        self.visibility.set_sections([(k,v[1]) for k,v in self.sections.items()],self.hidden)
    def render_resources(self):
        parent=self.section('locations','Locations & files')
        self.rows=self.model.resources(self.page,self.instance)
        self.resource_pane=ResourcePane(parent,on_select=self.select_resource,on_folder=lambda:self.safe(self.open_folder),on_open=lambda:self.safe(self.open_item),on_copy=lambda:self.safe(self.copy_path),on_refresh=self.refresh);self.resource_pane.pack(fill='both',expand=True)
        self.resource_pane.set_resources(self.rows);self.select_resource(self.resource_pane.selector.selected_id,refresh=False)
        button=ttk.Button(parent,text='Add location…',command=lambda:self.safe(self.add_location));button.pack(anchor='w',pady=(6,0));self.action_widgets['add-location']=button
        self.action_widgets.update({key:self.resource_pane.actions[label] for key,label in [('folder','Open location'),('item','Open selected item'),('copy','Copy path'),('refresh','Refresh files')]})
    def add_location(self):
        path=filedialog.askdirectory(parent=self.root,title='Connect an existing folder to this preview page')
        if path:self.model.add_location(self.page,path);self.stash();self.render();self.refresh()
    def render_mods(self):
        parent=self.section('draft','Draft actions · preview before applying')
        state=self.observation or {};schema=state.get('schema',[])
        if schema:
            self.ensure_variables(schema,state['values']);groups={}
            for field in schema:
                group=group_for(field)
                groups.setdefault(group,[]).append(field)
            bar=FlowToolbar(parent);bar.pack(fill='x')
            for label,fn,key in [('Preview changes',self.preview,'preview'),('Apply through current controller…',self.apply,'apply'),('Floating editor',self.floating_editor,'floating'),('Reset draft to applied',self.reset_draft,'reset')]:self.action(bar,label,fn,key)
            for index,(name,fields) in enumerate(groups.items()):
                editor=SchemaEditor(self.section('settings-'+str(index),name),fields,self.variables);editor.pack(fill='x');self.field_widgets.update(editor.widgets)
        else:ttk.Label(parent,text='Choose a connected installation with reviewed controls. Existing app connections remain the source owner.',style='Review.Card.TLabel',wraplength=750).pack(anchor='w')
        parent=self.section('profiles','Profiles · current and parallel copies');self.profile=Selector(parent,on_select=lambda ident:setattr(self,'profile_id',ident));self.profile.pack(fill='x')
        if schema:self.profile.set_choices([(r['id'],r['label']) for r in self.model.profile_rows(self.instance)])
        bar=FlowToolbar(parent);bar.pack(fill='x');self.action(bar,'Load into draft',self.load_profile,'load-profile');self.action(bar,'Save parallel profile…',self.save_profile,'save-profile')
        parent=self.section('changes','Preview & source state');self.output=tk.Text(parent,height=6,width=28,wrap='word',font=self.font,bg=self.palette['card'],fg=self.palette['ink']);self.output.pack(fill='both',expand=True);self.write('Refresh files reads applied settings. Preview and saved drafts do not change the game.')
        self.render_resources();self.render_manager()
        parent=self.section('sources','Mod sources & capability details')
        for url in state.get('sources',[]):ttk.Button(parent,text='Open source · '+urlsplit(url).netloc,command=lambda u=url:webbrowser.open(u)).pack(anchor='w',pady=2)
        ttk.Label(parent,text=state.get('notes','Capability coverage appears after reading a connected installation.'),style='Review.Card.TLabel',wraplength=820).pack(anchor='w',pady=5)
    def ensure_variables(self,schema,values):
        draft=self.model.view['drafts'].get(self.instance,{})
        for field in schema:
            key=field['id']
            if key not in self.variables:self.variables[key]=tk.BooleanVar(self,value=draft.get(key,values[key])) if field['type']=='bool' else tk.StringVar(self,value=str(draft.get(key,values[key])))
    def render_general(self):
        descriptions={'tools':'Open installed programs separately from their folders. Refresh reads file state; it does not start a program.',
            'profiles':'The same location, refresh, selection and export controls now apply to saved profiles and overlay files.',
            'reports':'Browse existing reports and diagnostics using their original files. No capture or measurement starts.',
            'files':'Find the current app, its recovery records and this parallel preview’s own files.'}
        parent=self.section('overview','Shared workflow');ttk.Label(parent,text=descriptions[self.page],style='Review.Card.TLabel',wraplength=820).pack(anchor='w')
        self.render_resources();self.render_manager()
        parent=self.section('details','Selected item details');self.output=tk.Text(parent,height=6,width=28,wrap='word',font=self.font,bg=self.palette['card'],fg=self.palette['ink']);self.output.pack(fill='both',expand=True);self.write('Select a component above, or double-click an available saved file in the file table to inspect its location.')
        self.resource_pane.tree.bind('<Double-1>',self.select_file)
    def render_manager(self):
        parent=self.section('handoff','Prepare files for a selected program')
        allowed=TARGETS.get(self.page,['folder','custom']);preferred=self.model.view.get('destination_by_page',{}).get(self.page,self.manager.get());selected=preferred if preferred in allowed else allowed[0];self.manager.set(selected)
        self.destination=Selector(parent,choices=[(key,MANAGERS[key]) for key in allowed],on_select=self.choose_manager);self.destination.pack(fill='x');self.destination.select(selected)
        bar=FlowToolbar(parent);bar.pack(fill='x',pady=4)
        for label,fn,key in [('Prepare files',self.export,'export'),('Open prepared folder',self.open_export,'export-folder'),('Open selected program',self.open_program,'program'),('Locate program…',self.locate_program,'locate-program')]:self.action(bar,label,fn,key)
        ttk.Label(parent,text='Choose the relevant program. Preparation, opening and native import/deployment are separate steps.',style='Review.Muted.TLabel',wraplength=800).pack(anchor='w')
    def choose_manager(self,ident):self.manager.set(ident);self.model.view.setdefault('destination_by_page',{})[self.page]=ident;self.model.save_view()
    def render_review(self):
        parent=self.section('compare','Compare with the current version')
        ttk.Label(parent,text='This is a separate UI preview with its own layout and drafts. Current source and native profiles keep their original owners. Explicit Apply uses the existing controller and its recovery checks. Your review decides whether to adopt this UI.',style='Review.Card.TLabel',wraplength=800).pack(anchor='w')
        bar=FlowToolbar(parent);bar.pack(fill='x');bar.add('Find current app / launcher',lambda:self.safe(lambda:self.open_path(self.model.install_root)));bar.add('Find preview APP LAUNCHER',lambda:self.safe(lambda:self.open_path(Path(__file__).resolve().parents[2] if Path(__file__).resolve().parents[1].name=='source' else self.model.root.parent)))
        parent=self.section('feedback','Your review · saved locally')
        self.verdict=tk.StringVar(self,value='Undecided');ttk.Combobox(parent,textvariable=self.verdict,values=['Undecided','Like this direction','Needs changes'],state='readonly').pack(fill='x')
        self.notes=tk.Text(parent,height=10,width=28,wrap='word',font=self.font,bg=self.palette['card'],fg=self.palette['ink']);self.notes.pack(fill='both',expand=True,pady=8)
        path=self.model.root/'feedback.json'
        if path.is_file():
            data=json.loads(path.read_text(encoding='utf-8'));self.verdict.set(data['verdict']);self.notes.insert('1.0',data['notes'])
        ttk.Button(parent,text='Save review notes',command=lambda:self.safe(self.save_notes)).pack(anchor='w')
    def save_notes(self):
        path=self.model.feedback(self.notes.get('1.0','end-1c'),self.verdict.get());self.status.set('Review saved locally: '+str(path)+' • no adoption or message was sent.')
    def select_resource(self,ident,refresh=True):
        self.resource_id=ident;row=self.selected_resource(optional=True)
        if row:self.resource_pane.show_resource(row)
        if refresh:self.token+=1;self.refresh()
    def selected_resource(self,optional=False):
        row=next((r for r in self.rows if r['id']==self.resource_id),None)
        if row is None and not optional:raise ModError('SELECTION_REQUIRED','Select a component, file or location.')
        return row
    def select_file(self,_event=None):
        ids=self.resource_pane.tree.selection()
        if not ids:return
        name=self.resource_pane.tree.item(ids[0],'values')[0];row=self.selected_resource();folder=row['path'] if row['path'].is_dir() else row['path'].parent;path=folder/name
        self.rows=[r for r in self.rows if r['id']!='selected-file']+[{'id':'selected-file','label':name,'path':path,'exists':path.exists(),'kind':'file' if path.is_file() else 'folder','origin':row['origin']}]
        self.resource_pane.set_resources(self.rows,'selected-file');self.select_resource('selected-file')
    def values(self):
        if not self.observation or not self.observation.get('schema'):raise ModError('CONTROLS_REQUIRED','Select an installation with reviewed controls.')
        result={}
        for field in self.observation['schema']:
            value=self.variables[field['id']].get();result[field['id']]=int(value) if field['type']=='int' else float(value) if field['type']=='number' else value
        return result
    def write(self,value):
        if not hasattr(self,'output') or not self.output.winfo_exists():return
        self.output.configure(state='normal');self.output.delete('1.0','end');self.output.insert('end',value if type(value) is str else json.dumps(value,indent=2));self.output.configure(state='disabled')
    def preview(self):
        result=self.model.preview(self.instance,self.values(),self.observation['revision']);self.write(result);self.status.set(str(len(result['changes']))+' draft changes • no game files written');return result
    def apply(self):
        if self.busy:raise ModError('READ_BUSY','Wait for the current read before applying.')
        preview=self.preview()
        if not preview['changes']:return
        detail='\n'.join(row['id']+': '+str(row['before'])+' → '+str(row['after']) for row in preview['changes'])
        if not messagebox.askyesno('Apply through the current controller?',detail+'\n\nThis changes the selected game using its existing controller, ownership guards and recovery. Close the game and manager first.',parent=self.root):return
        self.write(self.model.apply_current(self.instance,self.values(),preview['revision']));self.model.view['drafts'].pop(self.instance,None);self.variables={};self.observation=None;self.refresh()
    def reset_draft(self):
        for key,var in self.variables.items():var.set(self.observation['values'][key])
        self.stash();self.preview()
    def floating_editor(self):
        win=tk.Toplevel(self.root);win.title('Parallel preview · floating settings');win.geometry('580x650');win.minsize(360,300)
        pin=WindowPin(win,win,self.model.view.setdefault('window_pins',{}).get('floating',False),lambda value:self.save_pin('floating',value));pin.pack(anchor='e',padx=10,pady=6);win.review_pin=pin
        body=ScrollableFrame(win,min_width=300);body.pack(fill='both',expand=True);SchemaEditor(body.body,self.observation['schema'],self.variables).pack(fill='x',padx=10,pady=10)
        ttk.Label(body.body,text='Shared draft • hiding a section does not disable its mods.',wraplength=500).pack(anchor='w',padx=10,pady=8);self.floating.append(win)
    def save_profile(self):
        name=simpledialog.askstring('Save parallel profile','Profile name:',parent=self.root)
        if name:self.model.save_profile(self.instance,name,self.values(),self.observation['revision']);self.stash();self.render();self.status.set('Saved in the parallel preview. Current profiles and game files are unchanged.')
    def load_profile(self):
        values=self.model.load_profile(self.instance,self.profile.selected_id)
        for key,value in values.items():self.variables[key].set(value)
        self.preview()
    def refresh(self):
        if self.busy:self.pending=True;self.status.set('A bounded read is running; the latest refresh will follow.');return
        self.stash();self.pending=False;token=self.token;instance=self.instance;page=self.page;row=self.selected_resource(optional=True);self.status.set('Refreshing files… draft edits are preserved.');self.progress.start(12)
        def work():
            try:
                state=self.model.inspect(instance) if page=='mods' and instance else None
                files=self.model.refresh_files(row) if row and row['exists'] else None
                self.events.put(('refresh',token,state,files))
            except Exception as error:self.events.put(('error',token,str(error)))
        self.worker=threading.Thread(target=work,name='UI-review-read',daemon=False);self.worker.start()
    def poll(self):
        if self.closed:return
        try:
            while True:
                result=self.events.get_nowait()
                if result[1]!=self.token:continue
                if result[0]=='error':self.status.set(result[2])
                elif result[0]=='export':self.write(result[2]);self.status.set('Prepared files in the parallel preview. Open prepared folder to inspect them.')
                else:
                    _,_,state,files=result
                    if state is not None:
                        old=self.observation;self.observation=state
                        if old is None or old.get('schema_revision')!=state.get('schema_revision'):self.render()
                        elif old.get('values')!=state.get('values'):self.status.set('Applied files changed. Your draft remains; review the preview against refreshed values.')
                    if files and hasattr(self,'resource_pane'):self.resource_pane.display(files)
                    if self.status.get().startswith('Refreshing'):self.status.set('Files refreshed • drafts preserved • no game files changed')
        except queue.Empty:pass
        if not self.busy:
            self.progress.stop()
            if self.pending:self.refresh()
            elif self.pending_result:self.finish_reveal()
        self._poll=self.after(80,self.poll)
    def export(self):
        if self.busy:raise ModError('READ_BUSY','Wait for the current read before preparing files.')
        page=self.page;instance=self.instance;values=self.values() if page=='mods' else None;revision=self.observation['revision'] if values is not None else None;row=self.selected_resource(optional=page=='mods');manager=self.manager.get();token=self.token
        self.status.set('Preparing private files for '+MANAGERS[manager]+'…');self.progress.start(12)
        def work():
            try:self.events.put(('export',token,self.model.export_settings(instance,manager,values,revision) if page=='mods' else self.model.export_resource(row,manager)))
            except Exception as error:self.events.put(('error',token,str(error)))
        self.worker=threading.Thread(target=work,name='UI-review-export',daemon=False);self.worker.start()
    def open_path(self,path):
        if path is None or not Path(path).exists():raise ModError('LOCATION_UNAVAILABLE','This location is not present.')
        if os.name=='nt':os.startfile(path)
        else:subprocess.Popen(['xdg-open',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def open_folder(self):
        row=self.selected_resource();self.open_path(row['path'] if row['path'].is_dir() else row['path'].parent)
    def open_item(self):self.open_path(self.selected_resource()['path'])
    def copy_path(self):self.clipboard_clear();self.clipboard_append(str(self.selected_resource()['path']));self.status.set('Selected path copied locally.')
    def open_export(self):
        path=self.model.latest_export
        if path is None:
            saved=self.model.root/'latest-export.json'
            if saved.is_file():path=Path(json.loads(saved.read_text())['path'])
        self.open_path(path)
    def open_program(self):
        row=next((r for r in self.model.tools() if r['tool_id']==self.manager.get()),None)
        if row is None or not row['installed']:raise ModError('PROGRAM_REQUIRED','Locate the chosen installed program first; Portable folder has no program to start.')
        self.open_path(row['path'])
    def locate_program(self):
        path=filedialog.askopenfilename(parent=self.root,title='Select the existing program',filetypes=[('Windows program','*.exe')])
        if path:self.model.locate_program(self.manager.get(),path);self.status.set('Program connection saved only in the parallel preview.')
    def close(self):
        if self.busy:self.status.set('A bounded read/export is finishing. Close again when it returns; existing output is retained.');return False
        if self.finder and self.finder.winfo_exists() and not self.finder.close():self.status.set('The control finder is finishing its bounded read. Close again when it returns.');return False
        self.stash();self.closed=True;self.after_cancel(self._poll)
        if self._wrap_job is not None:self.after_cancel(self._wrap_job)
        if hasattr(self,'resource_pane'):self.resource_pane.close()
        for win in self.floating:
            if win.winfo_exists():win.destroy()
        self.scroll.close();self.root.destroy();return True

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--page',choices=PAGES);a=parser.parse_args(argv)
    value=json.loads(a.config.read_text(encoding='utf-8'));view_name='view-'+a.page+'.json' if a.page in {'mods','files'} else 'view.json';model=ReviewModel(value['source_data'],value['review_data'],value.get('install_root'),view_name=view_name)
    root=tk.Tk();ReviewApp(root,model,a.page);root.mainloop();return 0

if __name__=='__main__':raise SystemExit(main())
