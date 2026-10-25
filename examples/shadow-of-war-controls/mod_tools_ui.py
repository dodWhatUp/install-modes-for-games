"""Compact mod browser, manager handoff and nonmodal settings editors."""
from pathlib import Path
import copy, json, os, subprocess, tkinter as tk, webbrowser
from tkinter import ttk, filedialog, messagebox
from control_service import KEYS, atomic, json_bytes, validate_values
from mod_resources import EDIT_FIELDS, get_mod, read_author_page, safe_web_url

PACKAGE='Shadow of War Manager Files.zip'

class ModTools:
    def __init__(self,panel):
        self.panel=panel;self.window=None;self.editors={}
        self.view_path=panel.service.base/'mod-tools-view.json'
        try:self.view=json.loads(self.view_path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):self.view={}
        if type(self.view) is not dict:self.view={}
        self.items=panel.service.mod_resources();self.by_id={x['id']:x for x in self.items}
        self.selected=self.view.get('selected_mod','multi-skills')
        if self.selected not in self.by_id:self.selected='multi-skills'

    def save_view(self):
        self.view['selected_mod']=self.selected
        atomic(self.view_path,json_bytes(self.view))

    def show(self,tab='mods'):
        if self.window is None or not self.window.winfo_exists():self.build()
        self.tabs.select(self.library if tab=='mods' else self.manager)
        self.window.deiconify();self.window.lift()
        self.refresh_manager()

    def build(self):
        win=self.window=tk.Toplevel(self.panel.root);win.title('Mod Control - Mods, folders & manager')
        win.geometry('840x690');win.minsize(650,540);win.transient(self.panel.root)
        self.tabs=ttk.Notebook(win);self.tabs.pack(fill='both',expand=True,padx=12,pady=12)
        self.library=ttk.Frame(self.tabs,padding=12);self.manager=ttk.Frame(self.tabs,padding=12)
        self.tabs.add(self.library,text='Mods & folders');self.tabs.add(self.manager,text='Manager transfer')
        ttk.Label(self.library,text='Choose or type to find a mod',font=('Segoe UI',12,'bold')).pack(anchor='w')
        self.mod_name=tk.StringVar();self.selector=ttk.Combobox(self.library,textvariable=self.mod_name)
        self.selector.pack(fill='x',pady=(7,8));self.selector.bind('<<ComboboxSelected>>',self.commit_selection)
        self.selector.bind('<Return>',self.commit_selection);self.selector.bind('<Escape>',lambda e:self.render_mod())
        self.selector.bind('<KeyRelease>',self.filter_mods)
        self.mod_status=tk.StringVar();ttk.Label(self.library,textvariable=self.mod_status,wraplength=730).pack(anchor='w')
        actions=ttk.Frame(self.library);actions.pack(fill='x',pady=9)
        self.settings_button=ttk.Button(actions,text='Floating settings...',command=lambda:self.floating(self.selected))
        self.settings_button.pack(side='left')
        ttk.Button(actions,text='Read author page here',command=self.read_page).pack(side='left',padx=6)
        ttk.Button(actions,text='Open author page',command=lambda:self.open_url(self.current()['page'])).pack(side='left')
        folderbar=ttk.Frame(self.library);folderbar.pack(fill='x')
        ttk.Label(folderbar,text='Folder').pack(side='left',padx=(0,7))
        self.folder_name=tk.StringVar();self.folder_combo=ttk.Combobox(folderbar,state='readonly',textvariable=self.folder_name)
        self.folder_combo.pack(side='left',fill='x',expand=True)
        self.folder_combo.bind('<<ComboboxSelected>>',lambda e:self.update_folder())
        ttk.Button(folderbar,text='Open folder',command=self.open_folder).pack(side='left',padx=(7,0))
        self.folder_path=tk.StringVar();ttk.Label(self.library,textvariable=self.folder_path,wraplength=720,style='Muted.TLabel').pack(anchor='w',pady=(5,9))
        self.details=tk.Text(self.library,wrap='word',height=12,padx=10,pady=10,font=('Segoe UI',10),relief='flat')
        scroll=ttk.Scrollbar(self.library,command=self.details.yview);self.details.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.details.pack(fill='both',expand=True)
        ttk.Button(self.library,text='Show mod information',command=self.render_mod).pack(anchor='w',pady=(7,0))
        self.build_manager();self.render_mod()

    def current(self):return self.by_id[self.selected]
    def filter_mods(self,event=None):
        if event and event.keysym in ('Return','Escape','Up','Down'):return
        query=self.mod_name.get().casefold()
        matches=[x['name'] for x in self.items if query in x['name'].casefold()]
        self.selector.configure(values=matches)
        self.mod_status.set('No matching mod. Your current selection is preserved.' if not matches else 'Choose a result or press Enter to select it.')
    def commit_selection(self,event=None):
        query=self.mod_name.get().strip().casefold();matches=[x for x in self.items if x['name'].casefold()==query]
        if not matches:matches=[x for x in self.items if query and query in x['name'].casefold()]
        if len(matches)!=1:return self.mod_status.set('Choose one matching mod. No setting was changed.')
        self.selected=matches[0]['id'];self.save_view();self.render_mod()
    def set_text(self,text):
        if self.window is None or not self.window.winfo_exists():return
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('1.0',text);self.details.configure(state='disabled')
    def render_mod(self):
        item=self.current();self.mod_name.set(item['name']);self.selector.configure(values=[x['name'] for x in self.items])
        values=self.panel.snapshot['values'] if self.panel.snapshot else {}
        key=item['id'];configured=values.get(key)
        if key in ('multi-skills','elven-speed','fov'):configured=bool(configured and values.get('gameplay'))
        elif key=='renodx':configured=values.get('graphics') and values.get('profile')=='previous'
        elif key=='luma':configured=values.get('graphics') and values.get('profile')=='luma'
        status='Configured to load' if configured else 'Configured off' if configured is not None else 'See owner controls'
        self.mod_status.set(item['category']+' | '+status)
        self.settings_button.configure(state='normal' if item['editable'] else 'disabled')
        locations=item['locations'];self.folder_combo.configure(values=list(locations));self.folder_name.set('Mod files');self.update_folder()
        text=item['name']+'\n\n'+item['summary']+'\n\n'+item['notes']+'\n\nAuthor/source page:\n'+item['page']
        if item.get('installed_file'):text+='\n\nInstalled or retained file:\n'+str(item['installed_file'])
        if not item['editable']:text+='\n\nFloating file controls are available for the three gameplay plugins and their shared loader. Graphics use their existing in-game menu and reviewed profile controls.'
        self.set_text(text)
    def update_folder(self):self.folder_path.set(str(self.current()['locations'][self.folder_name.get()]))
    def open_folder(self):self.panel.open_path(self.current()['locations'][self.folder_name.get()])
    def open_url(self,url):
        safe_web_url(url)
        if self.panel.demo:return self.panel.notice.set('Demo: external browser opening is disabled.')
        webbrowser.open(url)
    def read_page(self):
        key=self.selected
        def read():return ('AUTHOR DOCUMENTATION (isolated fixture)\n'+self.current()['name']) if self.panel.demo else read_author_page(key)
        def done(text):
            if self.window is not None and self.window.winfo_exists() and self.selected==key:self.set_text(text)
        self.panel.run(read,done)

    def build_manager(self):
        canvas=tk.Canvas(self.manager,highlightthickness=0,background='#f4f6fa')
        scroll=ttk.Scrollbar(self.manager,orient='vertical',command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(fill='both',expand=True)
        box=ttk.Frame(canvas);item=canvas.create_window((0,0),window=box,anchor='nw')
        def resize(event):
            canvas.itemconfigure(item,width=event.width)
            for child in box.winfo_children():
                if isinstance(child,ttk.Label) and int(child.cget('wraplength') or 0)>0:child.configure(wraplength=max(240,event.width-12))
        canvas.bind('<Configure>',resize);box.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        ttk.Label(box,text='Prepare files for a regular mod manager',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(box,text='Export uses the applied files, not uncommitted preview edits. Preparing or opening files does not deploy mods.',wraplength=720).pack(anchor='w',pady=(8,15))
        row=ttk.Frame(box);row.pack(fill='x')
        self.prepare_button=ttk.Button(row,text='Prepare manager files',command=self.prepare);self.prepare_button.pack(side='left')
        self.export_folder_button=ttk.Button(row,text='Open export folder',command=self.open_export_folder);self.export_folder_button.pack(side='left',padx=7)
        self.package_button=ttk.Button(row,text='Open package ZIP',command=self.open_package);self.package_button.pack(side='left')
        self.export_status=tk.StringVar();ttk.Label(box,textvariable=self.export_status,wraplength=720).pack(anchor='w',pady=(10,5))
        self.guide_button=ttk.Button(box,text='Read handoff guide here',command=self.read_guide);self.guide_button.pack(anchor='w')
        ttk.Separator(box).pack(fill='x',pady=18)
        row=ttk.Frame(box);row.pack(fill='x')
        self.manager_button=ttk.Button(row,text='Open manager',command=self.open_manager);self.manager_button.pack(side='left')
        ttk.Button(row,text='Choose installed manager...',command=self.choose_manager).pack(side='left',padx=7)
        self.manager_status=tk.StringVar();ttk.Label(box,textvariable=self.manager_status,wraplength=720).pack(anchor='w',pady=9)
        ttk.Button(box,text='Vortex extension page',command=lambda:self.open_url('https://www.nexusmods.com/site/mods/375')).pack(anchor='w')
        ttk.Label(box,text='Import the four original archives individually from the export folder. The outer ZIP is a transport/backup package, not a deployable mod.\n\nKeep one loader and one writer per file. The Vortex extension can install loaders automatically; actual ownership transfer needs review. Graphics stay under RHI and the reviewed local profiles.',wraplength=720).pack(anchor='w',pady=(9,15))
        self.manager_note=tk.StringVar();ttk.Label(box,textvariable=self.manager_note,wraplength=720,foreground='#8a4300').pack(anchor='w')
    def refresh_manager(self):
        if self.window is None or not self.window.winfo_exists():return
        self.latest=self.panel.service.latest_manager_export()
        available=self.latest is not None
        self.export_folder_button.configure(state='normal' if available else 'disabled')
        self.guide_button.configure(state='normal' if available else 'disabled')
        self.package_button.configure(state='normal' if available and (self.latest/PACKAGE).is_file() else 'disabled')
        self.export_status.set('Prepared folder:\n'+str(self.latest) if available else 'No prepared files yet. Choose Prepare manager files.')
        manager=self.panel.service.manager_executable()
        self.manager_button.configure(state='normal' if manager else 'disabled')
        self.manager_status.set('Installed manager: '+str(manager) if manager else 'No installed manager found. Choose an existing manager executable to enable Open manager.')
    def prepare(self):
        if not self.panel.snapshot or self.panel.busy:return
        snapshot=copy.deepcopy(self.panel.snapshot)
        def done(path):
            if self.window is not None and self.window.winfo_exists():
                self.refresh_manager();self.manager_note.set('Files and package ZIP are ready. No deployment or ownership transfer was performed.')
            self.panel.notice.set('Manager files prepared: '+str(path))
        self.panel.run(lambda:self.panel.service.export_vortex(snapshot),done)
    def open_export_folder(self):
        self.refresh_manager()
        if self.latest:self.panel.open_path(self.latest)
    def open_package(self):
        self.refresh_manager()
        if self.latest:self.panel.open_path(self.latest/PACKAGE)
    def read_guide(self):
        self.refresh_manager()
        if self.latest:self.panel.text_window('Manager handoff guide',(self.latest/'READ-ME-FIRST.txt').read_text(encoding='utf-8'))
    def choose_manager(self):
        if self.panel.demo:return self.manager_note.set('Demo: selecting a host executable is disabled.')
        path=filedialog.askopenfilename(parent=self.window,title='Choose an installed mod manager',filetypes=[('Windows application','*.exe')])
        if not path:return
        try:self.panel.service.set_manager_executable(path);self.refresh_manager()
        except Exception as e:messagebox.showerror('Manager not selected',str(e),parent=self.window)
    def open_manager(self):
        manager=self.panel.service.manager_executable()
        if not manager:return self.refresh_manager()
        if self.panel.demo:return self.manager_note.set('Demo: manager launching is disabled.')
        try:subprocess.Popen([str(manager)])
        except OSError as e:messagebox.showerror('Cannot open manager',str(e),parent=self.window)
    def floating(self,key):
        if key not in EDIT_FIELDS:return
        previous=self.editors.get(key)
        if previous is not None and previous.winfo_exists():previous.lift();return previous
        win=FloatingSettings(self,key);self.editors[key]=win;return win

class FloatingSettings(tk.Toplevel):
    def __init__(self,tools,key):
        self.tools=tools;self.panel=tools.panel;self.key=key;self.traces=[]
        super().__init__(self.panel.root);self.title(get_mod(key)['name']+' - Floating settings')
        self.transient(self.panel.root);self.geometry('540x420');self.minsize(480,340)
        self.columnconfigure(0,weight=1)
        body=ttk.Frame(self,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text=get_mod(key)['name'],font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(body,text='Edits share the main preview. Closing this window keeps that preview.',wraplength=480).pack(anchor='w',pady=(6,10))
        labels={'multi-skills':'Enable Multi Equip Skills','elven-speed':'Enable Elven Speed','fov':'Enable FOV Extender','gameplay':'Enable gameplay loader'}
        ttk.Checkbutton(body,text=labels[key],variable=self.panel.vars[key]).pack(anchor='w')
        fields={'elven-speed':[('duration','Ability duration',0,10,.05),('regen','Focus regeneration',-1,1,.05)],
                'fov':[('fov_min','Minimum FOV',40,70,1),('fov_max','Maximum FOV',40,70,1)]}
        self.entries={}
        for field,label,lo,hi,step in fields.get(key,[]):
            row=ttk.Frame(body);row.pack(fill='x',pady=7)
            ttk.Label(row,text=label).pack(side='left')
            entry=ttk.Spinbox(row,textvariable=self.panel.vars[field],from_=lo,to=hi,increment=step,width=12)
            entry.pack(side='right');self.entries[field]=entry
        if key=='multi-skills':
            row=ttk.Frame(body);row.pack(fill='x',pady=7);ttk.Label(row,text='Modifier').pack(side='left')
            combo=ttk.Combobox(row,textvariable=self.panel.key_label,values=list(KEYS),state='readonly',width=18)
            combo.pack(side='right');combo.bind('<<ComboboxSelected>>',lambda e:self.panel.vars['modifier'].set(KEYS[self.panel.key_label.get()]))
            ttk.Checkbutton(body,text='Press to toggle (otherwise hold)',variable=self.panel.vars['toggle']).pack(anchor='w',pady=4)
            ttk.Checkbutton(body,text='Play equip sound',variable=self.panel.vars['sound']).pack(anchor='w')
        self.topmost=tk.BooleanVar(value=bool(tools.view.get('topmost',False)))
        ttk.Checkbutton(body,text='Keep this window on top',variable=self.topmost,command=self.set_topmost).pack(anchor='w',pady=(10,7))
        self.attributes('-topmost',self.topmost.get())
        self.status=tk.StringVar();ttk.Label(body,textvariable=self.status,wraplength=480,style='Muted.TLabel').pack(anchor='w',pady=6)
        row=ttk.Frame(body);row.pack(side='bottom',fill='x',pady=(10,0))
        self.apply_button=ttk.Button(row,text='Apply this mod',command=self.apply);self.apply_button.pack(side='left')
        ttk.Button(row,text='Save profile file',command=self.panel.save_profile).pack(side='left',padx=7)
        ttk.Button(row,text='Close',command=self.destroy).pack(side='right')
        for field in EDIT_FIELDS[key]:
            var=self.panel.vars[field];self.traces.append((var,var.trace_add('write',self.update_status)))
        self.bind('<Destroy>',self.cleanup);self.update_status()
    def set_topmost(self):
        self.attributes('-topmost',self.topmost.get());self.tools.view['topmost']=self.topmost.get();self.tools.save_view()
    def target_values(self):
        if not self.panel.snapshot:raise ValueError('Refresh the applied files first.')
        desired=copy.deepcopy(self.panel.snapshot['values']);preview=self.panel.values()
        for field in EDIT_FIELDS[self.key]:desired[field]=preview[field]
        return validate_values(desired)
    def update_status(self,*_):
        try:
            desired=self.target_values();changed=bool(self.panel.service.preview(desired,self.panel.snapshot))
            self.status.set('Pending settings for this mod. Apply keeps recovery; unrelated preview edits stay pending.' if changed else 'This mod matches the applied files.')
            self.apply_button.configure(state='normal' if changed and not self.panel.busy and not self.panel.location_blocked else 'disabled')
        except Exception as e:self.status.set(str(e));self.apply_button.configure(state='disabled')
    def apply(self):
        self.panel.apply_mod(self.key,lambda:self.update_status() if self.winfo_exists() else None)
        self.apply_button.configure(state='disabled')
    def cleanup(self,event):
        if event.widget is self:
            for var,trace in self.traces:var.trace_remove('write',trace)
            self.traces=[]
