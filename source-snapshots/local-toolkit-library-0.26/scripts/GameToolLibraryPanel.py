"""Compact game library and presentation-only Games / Goals navigation."""
from __future__ import annotations
from datetime import datetime
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog
from GameToolLibrary import Discovery, SORTS, PRESENCE, foreground_game
from GameToolCompactUI import FlowToolbar

GOALS = (
    ('library', 'Organize games', 'Library'),
    ('mods', 'Graphics & mods', 'Mods'),
    ('keybinds', 'Controls & bindings', 'Keybinds'),
    ('checks', 'Check a game setup', 'Manual checks'),
    ('requests', 'Review AI requests', 'AI requests'),
)

def date_label(value):
    if not value:return 'Unknown'
    try:return datetime.fromtimestamp(float(value)).strftime('%d %b %Y · %H:%M')
    except (ValueError,OverflowError,OSError):return 'Unknown'

def collect(discovery,cancel,out):
    try:out.put((True,discovery.scan(cancel)))
    except Exception as exc:out.put((False,exc))

class LibraryUI:
    def __init__(self,workbench,*,auto_discover=True):
        self.w=workbench;self.store=workbench.model.library;self.closed=False
        view=self.store.value['view'];root=workbench.root
        self.mode=tk.StringVar(root,value=view.get('browse_mode','Games'))
        if self.mode.get() not in {'Games','Goals & functions'}:self.mode.set('Games')
        self.launcher=tk.StringVar(root,value=view.get('launcher','All launchers'))
        self.tag=tk.StringVar(root,value=view.get('tag','All tags'))
        self.presence=tk.StringVar(root,value=view.get('presence','All games'))
        self.sort=tk.StringVar(root,value=view.get('sort','Name'))
        if self.sort.get() not in SORTS:self.sort.set('Name')
        if self.presence.get() not in PRESENCE:self.presence.set('All games')
        self.query=workbench.game_query;self.query.set(view.get('query',''))
        self.goal_query=tk.StringVar(root)
        self.automatic=tk.BooleanVar(root,value=view.get('automatic',True))
        self.scan_status=tk.StringVar(root,value='Installed-game metadata · refresh stays local')
        self.count=tk.StringVar(root);self.active_game=tk.StringVar(root)
        self.results=queue.Queue();self.cancel=threading.Event();self.worker=None
        self.timer=None;self.auto_timer=None;self.running_timer=None;self.row_cache=[]
        self.auto_discover=auto_discover
        self.goal_query.trace_add('write',lambda *_:self.refresh_navigation())
    def save_view(self):
        old=dict(self.store.value['view'])
        self.store.value['view'].update(browse_mode=self.mode.get(),launcher=self.launcher.get(),tag=self.tag.get(),
            presence=self.presence.get(),sort=self.sort.get(),query=self.query.get()[:300],automatic=self.automatic.get())
        try:self.store.save()
        except Exception:self.store.value['view']=old;raise
    def build_sidebar(self,parent):
        self.heading=ttk.Label(parent,text='Games',style='Strong.TLabel');self.heading.pack(anchor='w',pady=(0,8))
        self.search_label=ttk.Label(parent,text='Find a game',style='Muted.TLabel');self.search_label.pack(anchor='w')
        self.rail_search=ttk.Entry(parent,textvariable=self.query,width=22);self.rail_search.pack(fill='x',pady=(3,7))
        self.rail_tools=ttk.Frame(parent);self.rail_tools.pack(fill='x',pady=(0,6))
        ttk.Button(self.rail_tools,text='Filters…',command=self.filter_popup).pack(side='left')
        sort=ttk.Menubutton(self.rail_tools,text='Sort');sort.pack(side='right')
        menu=self.w._menu(sort);sort.configure(menu=menu)
        for name in SORTS:menu.add_radiobutton(label=name,variable=self.sort,value=name,command=self.changed)
        self.games=ttk.Treeview(parent,show='tree',height=10,selectmode='browse')
        self.games.column('#0',width=218,minwidth=130);self.games.pack(fill='both',expand=True)
        self.games.bind('<<TreeviewSelect>>',self.selected);self.games.bind('<Return>',self.selected)
        ttk.Label(parent,textvariable=self.count,style='Muted.TLabel',wraplength=218).pack(anchor='w',pady=(7,4))
        ttk.Button(parent,text='Game library',command=lambda:self.w.tabs.select(self.page)).pack(fill='x')
        self.w.games=self.games
    def build_page(self):
        self.page=ttk.Frame(self.w.tabs,padding=(0,8,0,0));self.w.tabs.insert(0,self.page,text='Library')
        bar=FlowToolbar(self.page);bar.pack(fill='x',pady=(0,7))
        self.refresh_button=bar.add('Refresh games',self.refresh_async)
        bar.add('Filters…',self.filter_popup);bar.add('Add game…',self.manual_popup)
        bar.add('Tags & favorite…',self.tags_popup);bar.add('Open game',self.open_selected)
        options=ttk.Menubutton(bar,text='Options');bar.add_widget(options)
        menu=self.w._menu(options);options.configure(menu=menu)
        menu.add_checkbutton(label='Refresh automatically while Game Tools is open',variable=self.automatic,command=self.change_automatic)
        menu.add_command(label='Sources & detection status',command=self.sources_popup)
        menu.add_command(label='Reset library filters',command=self.reset_filters)
        row=ttk.Frame(self.page);row.pack(fill='x',pady=(0,7));row.columnconfigure(1,weight=1)
        ttk.Label(row,text='Find a game').grid(row=0,column=0,padx=(0,8))
        self.search=ttk.Entry(row,textvariable=self.query);self.search.grid(row=0,column=1,sticky='ew')
        ttk.Button(row,text='Clear',command=lambda:self.query.set('')).grid(row=0,column=2,padx=(6,0))
        self.filter_summary=ttk.Label(self.page,style='Muted.TLabel',wraplength=720)
        self.filter_summary.pack(fill='x',pady=(0,6))
        self.table=self.w._table(self.page,[('name','Game',250),('launcher','Launcher',125),
            ('played','Last played',145),('used','Used in Game Tools',145),('changed','Changed in Game Tools',145),('tags','Tags',140)])
        for col,sort in [('name','Name'),('launcher','Launcher'),('played','Last played'),
                         ('used','Last used in Game Tools'),('changed','Last changed in Game Tools')]:
            self.table.heading(col,command=lambda s=sort:self.set_sort(s))
        self.table.bind('<Double-1>',lambda _e:self.open_selected());self.table.bind('<Return>',lambda _e:self.open_selected())
        self.table.bind('<<TreeviewSelect>>',lambda _e:self.describe_selected())
        self.table.bind('<Button-3>',self.context_menu)
        self.table.tag_configure('missing',foreground=self.w.colors['muted'])
        ttk.Label(self.page,textvariable=self.scan_status,style='Muted.TLabel',wraplength=850).pack(fill='x',pady=(8,0))
        ttk.Label(self.page,text='Unknown means the launcher has not supplied that history. Toolkit activity is separate from play history.',
                  style='Muted.TLabel',wraplength=850).pack(fill='x',pady=(4,0))
        self.context_combo=ttk.Combobox(self.w.jobbar,textvariable=self.active_game,state='readonly',width=26)
        self.context_combo.bind('<<ComboboxSelected>>',self.context_selected)
        self.context_label=ttk.Label(self.w.jobbar,text='Game')
        self.timer=self.w.after(250,self.poll)
        if self.auto_discover and self.automatic.get():self.auto_timer=self.w.after(600,self.refresh_async)
        self.running_timer=self.w.after(15000,self.observe_running)
        self.refresh_navigation()
    def rows(self):return self.w.model.catalog.game_rows()
    def filtered(self):
        return self.store.query(self.row_cache,text=self.query.get(),launcher=self.launcher.get(),tag=self.tag.get(),presence=self.presence.get(),sort=self.sort.get())
    def refresh_navigation(self):
        if self.closed or not hasattr(self,'games'):return
        self.row_cache=self.rows();rows=self.filtered()
        self.games.delete(*self.games.get_children())
        goals=self.mode.get()=='Goals & functions'
        self.heading.configure(text='Goals & functions' if goals else 'Games')
        self.search_label.configure(text='Find a goal or function' if goals else 'Find a game')
        self.rail_search.configure(textvariable=self.goal_query if goals else self.query)
        if goals:
            self.rail_tools.pack_forget()
            for ident,label,page in GOALS:
                if self.goal_query.get().casefold() in (label+' '+page).casefold():self.games.insert('','end',iid='goal-'+ident,text=label)
            current=self.w.tabs.tab(self.w.tabs.select(),'text') if hasattr(self.w,'tabs') and self.w.tabs.select() else ''
            target=next(('goal-'+i for i,l,p in GOALS if p==current),None)
            if target and self.games.exists(target):self.games.selection_set(target)
        else:
            if not self.rail_tools.winfo_manager():self.rail_tools.pack(before=self.games,fill='x',pady=(0,6))
            for row in rows:self.games.insert('','end',iid=row['id'],text=('★ ' if row.get('favorite') else '')+row['name'])
            if self.games.exists(self.w.game_id):self.games.selection_set(self.w.game_id)
        self.count.set(f'{len(rows)} of {len(self.row_cache)} games · '+self.sort.get())
        if hasattr(self,'table'):
            selected=self.table.selection();self.table.delete(*self.table.get_children())
            for row in rows:
                self.table.insert('','end',iid=row['id'],values=(('★ ' if row.get('favorite') else '')+row['name'],
                    ', '.join(row.get('launchers',[])) or 'Not detected',date_label(row.get('last_played')),
                    date_label(row.get('last_used')),date_label(row.get('last_changed')),', '.join(row.get('tags',[]))),
                    tags=() if row.get('installed') else ('missing',))
            if selected and self.table.exists(selected[0]):self.table.selection_set(selected[0])
            active=[f'{r["name"]} · {r["id"]}' for r in self.row_cache]
            self.context_ids=dict(zip(active,[r['id'] for r in self.row_cache]));self.context_combo.configure(values=active)
            self.active_game.set(next((name for name,ident in self.context_ids.items() if ident==self.w.game_id),''))
            self.filter_summary.configure(text=' · '.join([self.launcher.get(),self.tag.get(),self.presence.get(),'Sort: '+self.sort.get()]))
        if hasattr(self.w,'view_button'):self.w.view_button.configure(text='View · '+('Goals' if goals else 'Games'))
    def selected(self,_event=None):
        selection=self.games.selection()
        if not selection or self.w._loading:return
        ident=selection[0]
        if self.mode.get()=='Goals & functions':
            goal=next((g for g in GOALS if 'goal-'+g[0]==ident),None)
            if goal:
                target=next((p for p in self.w.tabs.tabs() if self.w.tabs.tab(p,'text')==goal[2]),None)
                if target:self.w.tabs.select(target)
        elif ident!=self.w.game_id:self.w.guard(lambda:self.w.load_game(ident))
    def context_selected(self,_event=None):
        ident=self.context_ids.get(self.active_game.get())
        if ident:self.w.guard(lambda:self.w.load_game(ident))
    def switch(self):
        self.w.guard(self.save_view);self.refresh_navigation();self.w.queue_layout()
        self.w.status.set('Browsing by '+self.mode.get().lower()+'. The selected game and active work are unchanged.')
    def changed(self):
        self.w.guard(self.save_view);self.refresh_navigation()
    def set_sort(self,sort):self.sort.set(sort);self.changed()
    def reset_filters(self):
        self.query.set('');self.launcher.set('All launchers');self.tag.set('All tags');self.presence.set('All games');self.sort.set('Name');self.changed()
    def filter_popup(self):
        win=tk.Toplevel(self.w.root);win.title('Library filters');win.transient(self.w.root)
        frame=ttk.Frame(win,padding=14);frame.pack(fill='both',expand=True)
        values=[('Launcher',self.launcher,['All launchers']+sorted({v for r in self.row_cache for v in r.get('launchers',[])})),
                ('Tag',self.tag,['All tags']+sorted({v for r in self.row_cache for v in r.get('tags',[])})),
                ('Show',self.presence,PRESENCE),('Sort',self.sort,SORTS)]
        drafts=[]
        for i,(label,var,options) in enumerate(values):
            ttk.Label(frame,text=label).grid(row=i,column=0,sticky='w',padx=(0,10),pady=5)
            draft=tk.StringVar(win,value=var.get());drafts.append((var,draft))
            ttk.Combobox(frame,textvariable=draft,values=options,state='readonly',width=30).grid(row=i,column=1,sticky='ew',pady=5)
        def apply():
            for var,draft in drafts:var.set(draft.get())
            self.changed();win.destroy()
        ttk.Button(frame,text='Apply filters',command=apply).grid(row=4,column=1,sticky='e',pady=(10,0))
        ttk.Button(frame,text='Cancel',command=win.destroy).grid(row=4,column=0,sticky='w',pady=(10,0));win.bind('<Escape>',lambda _e:win.destroy())
    def chosen_id(self):
        selected=self.table.selection()
        return selected[0] if selected else self.w.game_id
    def open_selected(self):
        ident=self.chosen_id()
        if ident:
            self.w.guard(lambda:self.w.load_game(ident))
            if self.w.game_id==ident:self.w.tabs.select(self.w.mods_page)
    def describe_selected(self):
        ident=self.chosen_id();row=next((r for r in self.row_cache if r['id']==ident),None)
        if not row:return
        fields=[('Launchers',', '.join(row.get('launchers',[])) or 'Not detected'),
                ('Last played',date_label(row.get('last_played'))),('Used in Game Tools',date_label(row.get('last_used'))),
                ('Changed in Game Tools',date_label(row.get('last_changed'))),('Tags',', '.join(row.get('tags',[])) or 'None'),
                ('Detection','Launcher metadata / selected folder; game behavior has not been tested'),
                ('Play history source','Launcher metadata or a game observed in the foreground while Game Tools was open; unknown history is not inferred from file dates')]
        self.w.detail_text(row['name'],fields,row)
    def tags_popup(self):
        ident=self.chosen_id();row=next((r for r in self.row_cache if r['id']==ident),None)
        if not row:return
        win=tk.Toplevel(self.w.root);win.title('Tags & favorite');win.transient(self.w.root)
        frame=ttk.Frame(win,padding=14);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text=row['name'],style='Strong.TLabel',wraplength=400).pack(anchor='w')
        ttk.Label(frame,text='Tags, separated by commas').pack(anchor='w',pady=(10,3))
        tags=tk.StringVar(win,value=', '.join(row.get('tags',[])));ttk.Entry(frame,textvariable=tags,width=48).pack(fill='x')
        favorite=tk.BooleanVar(win,value=row.get('favorite',False));ttk.Checkbutton(frame,text='Favorite',variable=favorite).pack(anchor='w',pady=8)
        def save():
            values=list(dict.fromkeys(v.strip() for v in tags.get().split(',') if v.strip()))
            result=self.w.guard(lambda:self.store.edit(ident,tags=values,favorite=favorite.get(),last_changed=time.time()))
            if self.store.value['games'].get(ident,{}).get('tags')==values:self.refresh_navigation();win.destroy()
        bar=ttk.Frame(frame);bar.pack(fill='x');ttk.Button(bar,text='Save',command=save).pack(side='right')
        ttk.Button(bar,text='Cancel',command=win.destroy).pack(side='right',padx=6);win.bind('<Escape>',lambda _e:win.destroy())
    def manual_popup(self):
        win=tk.Toplevel(self.w.root);win.title('Add a game');win.transient(self.w.root)
        frame=ttk.Frame(win,padding=14);frame.pack(fill='both',expand=True);frame.columnconfigure(1,weight=1)
        name=tk.StringVar(win);folder=tk.StringVar(win);launcher=tk.StringVar(win,value='Other')
        for i,(label,var) in enumerate([('Game',name),('Game folder',folder),('Launcher',launcher)]):
            ttk.Label(frame,text=label).grid(row=i,column=0,sticky='w',padx=(0,8),pady=5)
            if i==2:entry=ttk.Combobox(frame,textvariable=var,values=['Steam','Epic Games','GOG','Xbox','Ubisoft Connect','EA / Origin','Battle.net','itch.io','Other'],width=35)
            else:entry=ttk.Entry(frame,textvariable=var,width=38)
            entry.grid(row=i,column=1,sticky='ew',pady=5)
        def browse():
            chosen=filedialog.askdirectory(parent=win,title='Select game folder')
            if chosen:folder.set(chosen)
        ttk.Button(frame,text='Browse…',command=browse).grid(row=1,column=2,padx=5)
        def add():
            before=len(self.store.value['manual']);self.w.guard(lambda:self.store.add_manual(name.get(),folder.get(),launcher.get()))
            if len(self.store.value['manual'])>before:self.refresh_navigation();win.destroy()
        ttk.Button(frame,text='Add to library',command=add).grid(row=3,column=1,sticky='e',pady=(10,0))
        ttk.Button(frame,text='Cancel',command=win.destroy).grid(row=3,column=0,pady=(10,0));win.bind('<Escape>',lambda _e:win.destroy())
    def context_menu(self,event):
        ident=self.table.identify_row(event.y)
        if not ident:return
        self.table.selection_set(ident)
        menu=self.w._menu(self.table);menu.add_command(label='Open game workspace',command=self.open_selected)
        menu.add_command(label='Tags & favorite…',command=self.tags_popup)
        menu.add_command(label='Details',command=lambda:(self.describe_selected(),self.w.inspect_popup()))
        menu.tk_popup(event.x_root,event.y_root)
    def sources_popup(self):
        info=self.store.value['scan']
        self.w.detail_text('Game-library sources',[('Automatic readers','Steam, Epic Games, GOG, Ubisoft Connect, EA / Origin and Xbox'),
            ('Other launchers','Add the game folder and launcher manually. No broad scan of personal folders.'),
            ('Last refresh',date_label(info.get('scanned_at'))),('Reader status',str(info.get('coverage',{}))),
            ('Warnings','\n'.join(info.get('warnings',[])) or 'None'),
            ('Automation','Metadata refresh and foreground game recognition only while Game Tools is open; no startup task, input hook or game launch')],info)
        self.w.inspect_popup()
    def change_automatic(self):
        self.w.guard(self.save_view)
        if self.auto_timer:self.w.after_cancel(self.auto_timer);self.auto_timer=None
        if self.automatic.get() and self.auto_discover:self.refresh_async()
    def refresh_async(self):
        if self.closed or self.worker and self.worker.is_alive():return
        self.auto_timer=None;self.cancel.clear();self.scan_status.set('Collecting installed-game metadata…')
        self.refresh_button.configure(state='disabled')
        self.worker=threading.Thread(target=collect,args=(Discovery(),self.cancel,self.results),name='GameLibraryMetadata',daemon=True)
        self.worker.start()
    def poll(self):
        if self.closed:return
        try:
            ok,result=self.results.get_nowait()
            if self.worker:self.worker.join(timeout=.1)
            self.worker=None;self.refresh_button.configure(state='normal')
            if ok:
                before=self.w.model.catalog.game_rows()
                saved=self.w.guard(lambda:self.store.merge(result,before))
                self.refresh_navigation()
                self.scan_status.set(f'{len(result["records"])} installations found · refreshed '+date_label(result['scanned_at'])+
                    (' · some sources need attention' if result.get('warnings') else ''))
            else:self.scan_status.set('Refresh stopped: '+str(result))
            if self.auto_discover and self.automatic.get():self.auto_timer=self.w.after(300000,self.refresh_async)
        except queue.Empty:pass
        self.timer=self.w.after(300,self.poll)
    def observe_running(self):
        if self.closed:return
        if self.auto_discover and self.automatic.get():
            try:
                ident=foreground_game(self.row_cache)
                if ident and time.time()-self.store.value['games'].get(ident,{}).get('last_seen_running',0)>60:
                    self.store.touch(ident,'last_seen_running');self.refresh_navigation()
            except (OSError,ValueError):pass
        self.running_timer=self.w.after(15000,self.observe_running)
    def close(self):
        self.closed=True;self.cancel.set()
        for timer in (self.timer,self.auto_timer,self.running_timer):
            if timer:
                try:self.w.after_cancel(timer)
                except tk.TclError:pass
