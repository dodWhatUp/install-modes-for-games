"""A game-first operator workbench. Uses existing mod, approval and evidence owners.

This optional UI does not replace the native Studio or the existing Hub panels.
No automatic downloads, game launches, scanning of private folders, or services.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
import queue
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
import webbrowser
from urllib.parse import urlparse
from GameToolGameWorkspaces import (GameWorkspaces, ViewState, MANUAL_CHECKS,
    STATE_LABELS, GOOD_FILES, WAITING, BASE)
from game_mod_ops.safety import ModError, require, read_json
from game_mod_ops.recipes import load_recipe
from GameToolCompactUI import FlowToolbar, TableLayout
from game_keybind_ops.panel import attach as attach_keybind_panel

VERSION = "0.2.0"
PALETTES={
 'Dark':dict(bg='#10141c',panel='#181e29',raised='#222b39',ink='#e8edf7',muted='#a8b5c9',
             line='#313d50',accent='#a9baff',selected='#304265',danger='#ffb6b6',ok='#a6dfc0'),
 'Light':dict(bg='#f3f5f9',panel='#ffffff',raised='#e8edf5',ink='#18263c',muted='#52627a',
             line='#c7d0df',accent='#304cb4',selected='#dbe6ff',danger='#9d263a',ok='#19623e')}
OP_LABELS={'mods.create_plan':'Create plan','mods.download':'Download files','mods.stage':'Prepare files'}


class Workbench(ttk.Frame):
    def __init__(self,root,data_dir,*,on_original=None):
        self.root=root;self.data_dir=Path(data_dir);self.model=GameWorkspaces(self.data_dir)
        self.view=ViewState(Path(data_dir)/'workbench-view.json')
        self.game_id=self.view.value['active_game'];self.job_id=None;self.recipe=None
        self._loading=True;self.closed=False;self._tick=None;self._layout_job=None
        self.on_original=on_original;self.raw_detail={};self.request_rows={};self.last_review=None
        self._text_widgets=[];self._menus=[];self._selected_item=None
        self.zoom=tk.IntVar(root,value=self.view.value['zoom'])
        self.density=tk.StringVar(root,value=self.view.value['density'])
        self.theme=tk.StringVar(root,value=self.view.value['theme'])
        self.mode=tk.StringVar(root,value='real-time');self.query=tk.StringVar(root)
        self.game_query=tk.StringVar(root);self.job_choice=tk.StringVar(root,value='New draft')
        self.title=tk.StringVar(root);self.subtitle=tk.StringVar(root)
        self.status=tk.StringVar(root,value='Local workbench · no game files changed')
        self.summary=tk.StringVar(root);self.activity_count=tk.StringVar(root,value='No active tasks')
        self.page=tk.StringVar(root,value='Mods');self.watch=tk.BooleanVar(root,value=False)
        self.body_font=tkfont.Font(root,family='Segoe UI' if os.name=='nt' else 'DejaVu Sans',size=10)
        self.small_font=tkfont.Font(root,family=self.body_font.cget('family'),size=9)
        self.title_font=tkfont.Font(root,family=self.body_font.cget('family'),size=17,weight='bold')
        self.bold_font=tkfont.Font(root,family=self.body_font.cget('family'),size=10,weight='bold')
        self.apply_style()
        super().__init__(root,padding=0,style='WB.TFrame');self.pack(fill='both',expand=True)
        root.title('Game Tools — Workbench preview');root.geometry('1240x800');root.minsize(720,500)
        self.columnconfigure(0,weight=1);self.rowconfigure(1,weight=1)
        self._build_header();self._build_body();self._build_footer()
        self._loading=False
        games=self.model.game_rows()
        if self.game_id not in {g['id'] for g in games}:self.game_id=self.model.builtin_id
        self.load_game(self.game_id,persist=False)
        self.query.trace_add('write',self.filter_changed)
        self.game_query.trace_add('write',lambda *_:self.refresh_games())
        self.root.bind('<Configure>',self.queue_layout,add='+')
        self.root.bind('<Control-k>',self.focus_search,add='+')
        for key,delta in (('<Control-plus>',10),('<Control-equal>',10),('<Control-minus>',-10),('<Control-0>',0)):
            self.root.bind(key,lambda e,d=delta:self.zoom_key(e,d),add='+')
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self._tick=self.after(180,self.poll)
        self.queue_layout()

    def apply_style(self):
        p=PALETTES[self.theme.get()];self.colors=p;factor=self.zoom.get()/100
        self.body_font.configure(size=max(9,round(10*factor)))
        self.small_font.configure(size=max(9,round(9*factor)))
        self.bold_font.configure(size=max(9,round(10*factor)))
        self.title_font.configure(size=max(14,round(17*factor)))
        style=ttk.Style(self.root)
        if style.theme_use()!='clam':style.theme_use('clam')
        style.configure('.',background=p['bg'],foreground=p['ink'],font=self.body_font)
        style.configure('TFrame',background=p['bg']);style.configure('WB.TFrame',background=p['bg'])
        style.configure('Panel.TFrame',background=p['panel'])
        style.configure('TLabel',background=p['bg'],foreground=p['ink'],font=self.body_font)
        style.configure('Muted.TLabel',foreground=p['muted'],font=self.small_font)
        style.configure('Title.TLabel',font=self.title_font)
        style.configure('Strong.TLabel',font=self.bold_font)
        style.configure('TButton',background=p['raised'],foreground=p['ink'],bordercolor=p['line'],
                        lightcolor=p['raised'],darkcolor=p['raised'],borderwidth=0,padding=(10,7),font=self.body_font)
        style.map('TButton',background=[('active',p['selected']),('pressed',p['selected'])],
                  foreground=[('disabled',p['muted'])])
        style.configure('Primary.TButton',background=p['accent'],foreground=p['bg'],font=self.bold_font)
        style.map('Primary.TButton',background=[('disabled',p['raised']),('active',p['selected'])],
                  foreground=[('disabled',p['muted']),('active',p['ink'])])
        style.configure('TMenubutton',background=p['raised'],foreground=p['ink'],padding=(8,7),borderwidth=0)
        style.configure('TEntry',fieldbackground=p['panel'],foreground=p['ink'],insertcolor=p['ink'],padding=7,bordercolor=p['line'])
        style.configure('TCombobox',fieldbackground=p['panel'],background=p['raised'],foreground=p['ink'],padding=6,arrowsize=13)
        style.map('TCombobox',fieldbackground=[('readonly',p['panel'])],foreground=[('readonly',p['ink'])],selectbackground=[('readonly',p['selected'])])
        rowheight=round((32 if self.density.get()=='Compact' else 40)*factor)
        style.configure('Treeview',background=p['panel'],fieldbackground=p['panel'],foreground=p['ink'],
                        rowheight=rowheight,borderwidth=0,font=self.body_font)
        style.configure('Treeview.Heading',background=p['raised'],foreground=p['muted'],font=self.bold_font,
                        padding=(7,7),relief='flat')
        style.map('Treeview',background=[('selected',p['selected'])],foreground=[('selected',p['ink'])])
        style.configure('TNotebook',background=p['bg'],borderwidth=0)
        style.configure('TNotebook.Tab',background=p['bg'],foreground=p['muted'],padding=(12,8),font=self.body_font)
        style.map('TNotebook.Tab',background=[('selected',p['panel'])],foreground=[('selected',p['accent'])])
        style.configure('TCheckbutton',background=p['bg'],foreground=p['ink'],padding=4)
        style.configure('TPanedwindow',background=p['line'])
        self.root.configure(background=p['bg'])
        self.root.option_add('*TCombobox*Listbox.background',p['panel'])
        self.root.option_add('*TCombobox*Listbox.foreground',p['ink'])
        self.root.option_add('*TCombobox*Listbox.selectBackground',p['selected'])
        for text in getattr(self,'_text_widgets',[]):
            if text.winfo_exists():
                text.configure(background=p['panel'],foreground=p['ink'],insertbackground=p['ink'],
                               selectbackground=p['selected'],font=self.body_font)
                text.tag_configure('heading',font=self.bold_font,foreground=p['accent'],spacing1=12,spacing3=4)
                text.tag_configure('muted',foreground=p['muted'])
                text.tag_configure('danger',foreground=p['danger'])
        for menu in getattr(self,'_menus',[]):
            if menu.winfo_exists():menu.configure(background=p['panel'],foreground=p['ink'],activebackground=p['selected'],activeforeground=p['ink'])
        for tree in [getattr(self,n,None) for n in ('mods','requests','checks_tree','activity')]:
            if tree is not None:
                tree.tag_configure('alternate',background=p['raised'])
                tree.tag_configure('attention',foreground=p['danger'])
        if hasattr(self,'title_label'):self.queue_layout()

    def _menu(self,parent):
        m=tk.Menu(parent,tearoff=False);self._menus.append(m);return m

    def _build_header(self):
        self.header=ttk.Frame(self,padding=(14,10));self.header.grid(row=0,column=0,sticky='ew')
        self.header.columnconfigure(1,weight=1)
        self.brand=ttk.Label(self.header,text='GAME TOOLS',style='Strong.TLabel');self.brand.grid(row=0,column=0,sticky='w',padx=(0,18))
        self.header_activity=ttk.Label(self.header,textvariable=self.activity_count,style='Muted.TLabel')
        self.header_activity.grid(row=0,column=1,sticky='w')
        controls=ttk.Frame(self.header);self.header_controls=controls;controls.grid(row=0,column=2,sticky='e')
        self.games_button=ttk.Button(controls,text='Games',command=self.game_picker)
        self.samples_button=ttk.Button(controls,text='Try samples',command=self.samples)
        self.copy_button=ttk.Button(controls,text='Copy for chat',command=self.copy_context)
        self.view_button=ttk.Menubutton(controls,text='View')
        menu=self._menu(self.view_button);self.view_button.configure(menu=menu)
        for val in ('Dark','Light'):menu.add_radiobutton(label=val,variable=self.theme,value=val,command=self.change_view)
        menu.add_separator()
        for val in ('Compact','Comfortable'):menu.add_radiobutton(label=val,variable=self.density,value=val,command=self.change_view)
        zoom=self._menu(menu);menu.add_cascade(label='Zoom',menu=zoom)
        for val in range(80,201,10):zoom.add_radiobutton(label=f'{val}%',variable=self.zoom,value=val,command=self.change_view)
        menu.add_command(label='Reset appearance',command=self.reset_view)
        more=ttk.Menubutton(controls,text='More');self.more_button=more
        self._header_buttons=(self.games_button,self.samples_button,self.copy_button,self.view_button,more)
        self._has_saved_jobs=False;self._header_layout_key=None
        mm=self._menu(more);more.configure(menu=mm)
        mm.add_command(label='Import game support or recipe…',command=self.import_recipe)
        mm.add_command(label='Create game template…',command=self.create_support_template)
        mm.add_command(label='Game support details',command=self.support_details)
        mm.add_command(label='Copy extension brief for chat',command=self.copy_extension_brief)
        mm.add_command(label='Export game support…',command=self.export_support)
        mm.add_command(label='Export files for mod manager…',command=self.manager_handoff)
        mm.add_command(label='Try sample workflow…',command=self.samples)
        mm.add_command(label='Copy AI client setup…',command=self.copy_setup)
        mm.add_command(label='Open original tools',command=self.open_original)
        mm.add_separator();mm.add_command(label='Read changes and limits',command=self.open_guide)

    def _build_body(self):
        self.shell=ttk.Panedwindow(self,orient='horizontal');self.shell.grid(row=1,column=0,sticky='nsew')
        self.shell.bind('<Configure>',lambda _e:self.queue_layout())
        self.rail=ttk.Frame(self.shell,padding=(12,10));self.shell.add(self.rail,weight=0)
        ttk.Label(self.rail,text='Games',style='Strong.TLabel').pack(anchor='w',pady=(0,8))
        ttk.Label(self.rail,text='Find a game',style='Muted.TLabel').pack(anchor='w')
        ttk.Entry(self.rail,textvariable=self.game_query,width=21).pack(fill='x',pady=(3,10))
        self.games=ttk.Treeview(self.rail,columns=(),show='tree',height=10,selectmode='browse')
        self.games.column('#0',width=210,minwidth=120);self.games.pack(fill='both',expand=True)
        self.games.bind('<<TreeviewSelect>>',self.game_selected)
        ttk.Button(self.rail,text='Add game support',command=self.import_recipe).pack(fill='x',pady=(8,0))
        self.main=ttk.Frame(self.shell,padding=(14,8));self.shell.add(self.main,weight=1)
        self.main.columnconfigure(0,weight=1);self.main.rowconfigure(3,weight=1)
        titlebar=ttk.Frame(self.main);titlebar.grid(row=0,column=0,sticky='ew');titlebar.columnconfigure(0,weight=1)
        self.title_label=ttk.Label(titlebar,textvariable=self.title,style='Title.TLabel',wraplength=500);self.title_label.grid(row=0,column=0,sticky='w')
        self.inspect_button=ttk.Button(titlebar,text='Inspect selected',command=self.inspect_popup);self.inspect_button.grid(row=0,column=1,sticky='e')
        self.sub_label=ttk.Label(self.main,textvariable=self.subtitle,style='Muted.TLabel',wraplength=780);self.sub_label.grid(row=1,column=0,sticky='ew',pady=(3,10))
        self.jobbar=ttk.Frame(self.main);self.jobbar.grid(row=2,column=0,sticky='ew',pady=(0,8));self.jobbar.columnconfigure(1,weight=1)
        ttk.Label(self.jobbar,text='Plan').grid(row=0,column=0,padx=(0,7))
        self.job_combo=ttk.Combobox(self.jobbar,textvariable=self.job_choice,state='readonly',width=25)
        self.job_combo.grid(row=0,column=1,sticky='ew');self.job_combo.bind('<<ComboboxSelected>>',self.job_selected)
        ttk.Button(self.jobbar,text='New draft',command=self.new_draft).grid(row=0,column=2,padx=(6,0))
        self.tabs=ttk.Notebook(self.main);self.tabs.grid(row=3,column=0,sticky='nsew')
        self.mods_page=ttk.Frame(self.tabs,padding=(0,10,0,0));self.tabs.add(self.mods_page,text='Mods')
        self.requests_page=ttk.Frame(self.tabs,padding=(0,10,0,0));self.tabs.add(self.requests_page,text='AI requests')
        self.checks_page=ttk.Frame(self.tabs,padding=(0,10,0,0));self.tabs.add(self.checks_page,text='Manual checks')
        self.keybind_panel=attach_keybind_panel(self.tabs,self.data_dir,service=self.model.keybinds,
            busy_guard=lambda:bool(self.model.runner.active()))
        self.tabs.bind('<<NotebookTabChanged>>',self.tab_changed)
        self._build_mods();self._build_requests();self._build_checks()
        self.details_frame=ttk.Frame(self.shell,padding=(14,12));self.shell.add(self.details_frame,weight=0)
        ttk.Label(self.details_frame,text='Inspector',style='Strong.TLabel').pack(anchor='w',pady=(0,8))
        self.detail=self._text(self.details_frame,height=22,width=32);self.detail.pack(fill='both',expand=True)
        self.tech_button=ttk.Button(self.details_frame,text='Technical details',command=self.show_technical);self.tech_button.pack(fill='x',pady=(8,0))
        self.activity_frame=ttk.Frame(self,padding=(14,7))
        row=ttk.Frame(self.activity_frame);row.pack(fill='x')
        ttk.Label(row,text='Activity · all games',style='Strong.TLabel').pack(side='left')
        self.stop_all=ttk.Button(row,text='Stop active tasks',command=self.stop);self.stop_all.pack(side='right')
        self.activity=ttk.Treeview(self.activity_frame,columns=('game','action','status'),show='headings',height=3)
        for c,w in [('game',220),('action',230),('status',290)]:self.activity.heading(c,text=c.title());self.activity.column(c,width=w)
        self.activity.pack(fill='x',pady=(5,0));self.activity.bind('<<TreeviewSelect>>',self.activity_selected)

    def _table(self,parent,columns,selectmode='browse'):
        frame=ttk.Frame(parent);frame.pack(fill='both',expand=True)
        frame.columnconfigure(0,weight=1);frame.rowconfigure(0,weight=1)
        tree=ttk.Treeview(frame,columns=[c for c,_,_ in columns],show='headings',selectmode=selectmode,height=10)
        for c,title,width in columns:tree.heading(c,text=title);tree.column(c,width=width,minwidth=44,stretch=c in {'name','status','result'})
        tree.grid(row=0,column=0,sticky='nsew')
        y=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);y.grid(row=0,column=1,sticky='ns')
        x=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview);x.grid(row=1,column=0,sticky='ew')
        tree.configure(yscrollcommand=y.set,xscrollcommand=x.set)
        return tree

    def _build_mods(self):
        p=self.mods_page
        self.modebar=ttk.Frame(p);self.modebar.pack(fill='x',pady=(0,6))
        ttk.Label(self.modebar,text='Preset').pack(side='left',padx=(0,6))
        self.mode_combo=ttk.Combobox(self.modebar,textvariable=self.mode,values=['real-time','turn-based'],state='readonly',width=12)
        self.mode_combo.pack(side='left');ttk.Button(self.modebar,text='Use preset',command=self.use_preset).pack(side='left',padx=5)
        self.mode_combo.bind('<<ComboboxSelected>>',lambda _e:self.remember())
        self.actionbar=FlowToolbar(p);self.actionbar.pack(fill='x',pady=(0,6))
        self.primary=self.actionbar.add('Create plan',self.primary_action);self.primary.configure(style='Primary.TButton')
        self.import_button=self.actionbar.add('Import ZIP',self.import_zip)
        self.files_button=self.actionbar.add('Show files',self.show_files)
        self.next_button=self.actionbar.add('More actions',self.mod_menu)
        filt=ttk.Frame(p);filt.pack(fill='x',pady=(0,7));filt.columnconfigure(1,weight=1)
        ttk.Label(filt,text='Filter').grid(row=0,column=0,padx=(0,6))
        self.search=ttk.Entry(filt,textvariable=self.query);self.search.grid(row=0,column=1,sticky='ew')
        ttk.Button(filt,text='Clear',command=lambda:self.query.set('')).grid(row=0,column=2,padx=(5,0))
        self.mods=self._table(p,[('use','Use',48),('name','Mod',230),('version','Version',90),('status','Files',155),('next','Next step',170)],'extended')
        self.mods.configure(displaycolumns=('use','name','status','next'))
        self.mods.bind('<<TreeviewSelect>>',self.mod_selected)
        self.mods.bind('<Button-1>',self.mod_clicked,add='+');self.mods.bind('<space>',self.toggle_include,add='+')
        self.mod_layout=TableLayout(self.mods)
        self.sort_column=None;self.sort_reverse=False
        for c in ('name','version','status','next'):self.mods.heading(c,command=lambda col=c:self.sort_rows(col))
        self.footer_note=ttk.Label(p,textvariable=self.summary,style='Muted.TLabel',wraplength=740)
        self.footer_note.pack(fill='x',pady=(7,0))

    def _build_requests(self):
        bar=FlowToolbar(self.requests_page);bar.pack(fill='x',pady=(0,6))
        bar.add('Refresh',self.refresh_requests);bar.add('Import request',self.import_request)
        bar.add('Test approval flow',self.test_request)
        self.requests=self._table(self.requests_page,[('action','Action',155),('status','State',170),('id','Request',170)])
        self.requests.bind('<<TreeviewSelect>>',self.request_selected)
        self.reviewbar=FlowToolbar(self.requests_page);self.reviewbar.pack(fill='x',pady=(8,0))
        self.approve_button=self.reviewbar.add('Approve request',self.approve_request);self.approve_button.configure(style='Primary.TButton',state='disabled')
        self.reject_button=self.reviewbar.add('Reject',self.reject_request);self.reject_button.configure(state='disabled')
        self.reviewbar.add('Stop this game',lambda:self.stop(self.game_id))
        ttk.Checkbutton(self.requests_page,text='Auto refresh on this page (2 s)',variable=self.watch).pack(anchor='w',pady=(5,0))
        ttk.Label(self.requests_page,text='A request is not approval. Review the game, action and exact items first.',style='Muted.TLabel',wraplength=720).pack(fill='x',pady=5)

    def _build_checks(self):
        bar=FlowToolbar(self.checks_page);bar.pack(fill='x',pady=(0,6))
        self.inspect_installed_button=bar.add('Inspect game folder',self.inspect_installed)
        bar.add('Record manual check',self.record_check)
        bar.add('Refresh',self.refresh_checks)
        self.checks_tree=self._table(self.checks_page,[('name','Mod',190),('check','Check',200),('result','Reported result',160),('current','Scope',140)])
        self.checks_tree.bind('<<TreeviewSelect>>',self.check_selected)
        ttk.Label(self.checks_page,text='Your observations are saved as reports—not promoted to machine-verified success.',style='Muted.TLabel',wraplength=720).pack(fill='x',pady=7)

    def _build_footer(self):
        bar=ttk.Frame(self,padding=(14,7));bar.grid(row=3,column=0,sticky='ew');bar.columnconfigure(0,weight=1)
        self.status_label=ttk.Label(bar,textvariable=self.status,style='Muted.TLabel',wraplength=1000)
        self.status_label.grid(row=0,column=0,sticky='ew')

    def _text(self,parent,**kwargs):
        t=tk.Text(parent,wrap='word',relief='flat',borderwidth=0,highlightthickness=0,padx=10,pady=7,**kwargs)
        self._text_widgets.append(t);return t

    def detail_text(self,title,fields,raw=None):
        self.raw_detail=raw if raw is not None else dict(fields)
        self.detail.configure(state='normal');self.detail.delete('1.0','end')
        self.detail.insert('end',title+'\n','heading')
        for label,value in fields:
            self.detail.insert('end',label+'\n','heading')
            self.detail.insert('end',str('Unknown' if value is None or value=='' else value)+'\n')
        self.detail.configure(state='disabled')

    def show_error(self,error):
        text=error.message if isinstance(error,ModError) else 'The action could not finish. Inspect existing files before retrying.'
        self.status.set(text)
        self.detail_text('Action stopped',[('Reason',text),('What changed','No automatic retry or alternate route was started.')],
                         error.record() if isinstance(error,ModError) else {'status':'LOCAL_ERROR'})

    def guard(self,fn):
        try:return fn()
        except (ModError,OSError,ValueError,KeyError) as e:self.show_error(e);return None

    def remember(self):
        if self._loading:return
        draft=self.view.value['games'].setdefault(self.game_id,{})
        draft.update(mode=self.mode.get(),job_id=self.job_id,filter=self.query.get()[:200])
        self.view.value.update(active_game=self.game_id,zoom=self.zoom.get(),density=self.density.get(),theme=self.theme.get())
        self.guard(self.view.save)

    def load_game(self,game_id,persist=True):
        if not self._loading:self.remember()
        self._loading=True;self.game_id=game_id;self.last_review=None
        row=next(r for r in self.model.game_rows() if r['id']==game_id)
        self.recipe=self.model.catalog.get(game_id)['recipe'] if row['recipe_available'] else None
        draft=self.view.value['games'].setdefault(game_id,{})
        presets=list(self.recipe.get('presets',{})) if self.recipe else []
        default_mode='default' if 'default' in presets else ('real-time' if 'real-time' in presets else (presets[0] if presets else 'default'))
        if self.recipe and 'selected' not in draft:draft['selected']=list(self.recipe.get('presets',{}).get(default_mode,[]))
        self.mode_combo.configure(values=presets or ['default'])
        self.mode.set(draft.get('mode',default_mode));self.query.set(draft.get('filter',''))
        self.job_id=draft.get('job_id');self._selected_item=draft.get('item_id')
        jobs=self.model.jobs(game_id)
        if self.job_id not in {j['job_id'] for j in jobs}:self.job_id=None
        self.title.set(row['name'])
        self.subtitle.set(({'unity-mod-manager':'Unity Mod Manager'}.get(row['manager'],row['manager'])+' · recipe ready · installation not verified') if self.recipe else
            ('Keybind pack ready · mod recipe not registered · gameplay not verified' if row.get('keybind_pack_available') else
             'Recipe needed · catalog entry only, not an installed-game claim'))
        values=tuple(self.keybind_panel.game_box.cget('values'))
        if game_id in values:self.keybind_panel.game.set(game_id)
        self._loading=False
        self.refresh_games();self.refresh_jobs();self.refresh_mods();self.refresh_requests();self.refresh_checks()
        if not self.recipe and row.get('keybind_pack_available'):
            self.detail_text('Keybind workspace ready',[('Game',row['name']),('Available','Imported data-only keybind pack and the shared Keybinds pane.'),('Unavailable','No reviewed mod recipe is registered for this game.'),('Runtime','Gameplay and native Windows behavior remain unverified.')])
        elif not self.recipe:self.detail_text('Recipe needed',[('Why mod controls are unavailable','A reviewed installation recipe has not been supplied for this game.'),('Next','Import a game-specific JSON recipe. Creating a workspace does not make this game supported.')])
        else:self.detail_text('Choose a mod or request',[('Game',row['name']),('Workflow','Select a plan, inspect an item, then use its next action.'),('Parallel work','Other games stay available while this game has an operation running.')])
        self.apply_style()
        if persist:self.remember()

    def refresh_games(self):
        selected=self.game_id;self.games.delete(*self.games.get_children())
        q=self.game_query.get().casefold().strip()
        from collections import Counter
        counts=Counter(r['game_id'] for r in self.model.jobs())
        self._has_saved_jobs=bool(counts)
        self.queue_layout()
        for r in self.model.game_rows():
            if q and q not in (r['name']+' '+r['id']).casefold():continue
            count=counts[r['id']]
            suffix=(f'  ({count})' if count else ('  · keybinds' if r.get('keybind_pack_available') and not r['recipe_available'] else ('  · setup' if not r['recipe_available'] else '')))
            self.games.insert('','end',iid=r['id'],text=r['name']+suffix)
        if self.games.exists(selected):self.games.selection_set(selected)

    def game_selected(self,_e=None):
        rows=self.games.selection()
        if not self._loading and rows and rows[0]!=self.game_id:self.guard(lambda:self.load_game(rows[0]))

    def refresh_jobs(self):
        self.job_values={'New draft':None}
        for row in self.model.jobs(self.game_id):
            ident=row['job_id'];date=ident[:8];clock=ident[9:15]
            label=f'{date[4:6]}/{date[6:8]} {clock[:2]}:{clock[2:4]} · {row["prepared"]}/{row["items"]} prepared · {ident[-4:]}'
            self.job_values[label]=ident
        self.job_combo.configure(values=list(self.job_values))
        self.job_choice.set(next((label for label,ident in self.job_values.items() if ident==self.job_id),'New draft'))
        if self.job_id:self.modebar.pack_forget()
        elif not self.modebar.winfo_manager():self.modebar.pack(before=self.actionbar,fill='x',pady=(0,6))

    def job_selected(self,_e=None):
        self.job_id=self.job_values.get(self.job_choice.get());self._selected_item=None
        self.refresh_jobs();self.refresh_mods();self.refresh_checks();self.remember()

    def new_draft(self):
        self.job_id=None;self.refresh_jobs();self.refresh_mods();self.remember()
        self.tabs.select(self.mods_page)

    def use_preset(self):
        if not self.recipe:return
        self.view.value['games'][self.game_id]['selected']=list(self.recipe.get('presets',{}).get(self.mode.get(),[]))
        self.refresh_mods();self.remember()

    def filter_changed(self,*_):
        if not self._loading:self.refresh_mods();self.remember()

    def sort_rows(self,col):
        self.sort_reverse=not self.sort_reverse if self.sort_column==col else False;self.sort_column=col
        self.refresh_mods()
        for c in ('name','version','status','next'):
            title={'name':'Mod','version':'Version','status':'Files','next':'Next step'}[c]
            self.mods.heading(c,text=title+(' ↓' if self.sort_reverse else ' ↑') if c==col else title)

    def refresh_mods(self):
        previous=self.mods.selection();self.mods.delete(*self.mods.get_children());self.mod_rows={}
        if not self.recipe:
            self.primary.configure(text='Import recipe',state='normal');self.summary.set('No compatible recipe. No download or installation actions are offered.')
            for b in (self.import_button,self.files_button,self.next_button):b.configure(state='disabled')
            return
        draft=self.view.value['games'][self.game_id];chosen=set(draft.get('selected',[]))
        if self.job_id:rows=self.model.item_rows(self.game_id,self.job_id)
        else:rows=[{'id':i['id'],'name':i['name'],'version':i.get('display_version','Unknown'),'kind':i['kind'],
                    'state':'DRAFT','label':'Included' if i['id'] in chosen else 'Optional','next':'Create plan','runtime':'Not verified'} for i in self.recipe['items']]
        if self.sort_column:rows=sorted(rows,key=lambda r:str(r.get('label' if self.sort_column=='status' else self.sort_column,'')).casefold(),reverse=self.sort_reverse)
        q=self.query.get().strip().casefold()
        for i,r in enumerate(rows):
            if q and q not in ' '.join(str(v) for v in r.values()).casefold():continue
            ident=r['id'];self.mod_rows[ident]=r
            use='—' if self.job_id else ('✓' if ident in chosen else '○')
            self.mods.insert('','end',iid=ident,values=(use,r['name'],r['version'],r['label'],r['next']),tags=('alternate',) if i%2 else ())
        visible=[i for i in previous if self.mods.exists(i)]
        if not visible and self._selected_item and self.mods.exists(self._selected_item):visible=[self._selected_item]
        if not visible and self.mods.get_children():visible=[self.mods.get_children()[0]]
        if visible:self.mods.selection_set(visible)
        for b in (self.import_button,self.files_button):b.configure(state='normal' if self.job_id else 'disabled')
        self.next_button.configure(state='normal')
        busy=not self.model.runner.can_start(self.game_id)[0]
        self.primary.configure(text='Create plan' if not self.job_id else 'Next action',state='disabled' if busy else 'normal')
        self.summary.set((f'{len(chosen)} chosen · dependencies are included when the plan is created' if not self.job_id else f'{len(rows)} items · prepared files are not installed or enabled'))

    def mod_clicked(self,e):
        if not self.job_id and self.mods.identify_region(e.x,e.y)=='cell' and self.mods.identify_column(e.x)=='#1':
            ident=self.mods.identify_row(e.y)
            if ident:self.mods.selection_set(ident);self.toggle_include();return 'break'

    def toggle_include(self,_e=None):
        if self.job_id or not self.recipe:return 'break'
        selection=self.mods.selection();chosen=self.view.value['games'][self.game_id].setdefault('selected',[])
        for ident in selection:
            if ident in chosen:chosen.remove(ident)
            else:chosen.append(ident)
        self.refresh_mods();self.remember();return 'break'

    def selected_mod(self):
        ids=list(self.mods.selection());require(bool(ids),'SELECTION_REQUIRED','Select a mod row first.');return ids[0]

    def mod_selected(self,_e=None):
        ids=self.mods.selection()
        if not ids:return
        ident=ids[0];self._selected_item=ident
        self.view.value['games'][self.game_id]['item_id']=ident
        self.guard(lambda:self.describe_mod(ident))

    def describe_mod(self,ident):
        item=next(i for i in (self.model.job(self.game_id,self.job_id).plan['items'] if self.job_id else self.recipe['items']) if i['id']==ident)
        state=self.mod_rows[ident];requires=item.get('requires',[])
        self.detail_text(item['name'],[
            ('Game',self.title.get()),('Current state',state['label']),('Next step',state['next']),
            ('Requirements',', '.join(requires) if requires else 'No dependencies declared'),
            ('Important', '\n\n'.join(item.get('warnings',[])) or 'No recipe warning recorded. This is not proof of compatibility.'),
            ('Runtime','Not verified by this workbench')],{'item':item,'job':self.job_id,'state':state})
        if self.job_id:
            caption='Prepare selected' if state['state']=='ACQUIRED' and item['kind']=='mod' else 'Download plan' if state['state'] in WAITING else 'Show files'
            self.primary.configure(text=caption)

    def capture_job(self):
        require(self.job_id is not None,'PLAN_REQUIRED','Create or choose an existing plan first.')
        gid,jid=self.game_id,self.job_id;j=self.model.job(gid,jid)
        return gid,jid,self.model.revision(j)

    def start(self,label,action,network=False):
        gid=self.game_id;jid=self.job_id
        ok,reason=self.model.runner.can_start(gid,network)
        if not ok:self.status.set(reason);return
        self.guard(lambda:self.model.runner.start(gid,label,action,network=network,job_id=jid))
        self.status.set(label+' · '+self.title.get());self.refresh_mods();self.refresh_activity()

    def primary_action(self):self.guard(self._primary)
    def _primary(self):
        if not self.recipe:return self.import_recipe()
        gid=self.game_id
        if not self.job_id:
            ids=list(self.view.value['games'][gid].get('selected',[]));mode=self.mode.get()
            self.start('Create plan',lambda cancel:{'new_job':self.model.new_plan(gid,ids,mode).path.name,'game_id':gid,'status':'PLANNED'});return
        if not self.mods.selection():self.status.set('Select a mod to see its next action.');return
        gid,jid,revision=self.capture_job();ids=list(self.mods.selection())
        selected=[self.mod_rows[i] for i in ids]
        if all(i['state']=='ACQUIRED' and i['kind']=='mod' for i in selected):
            self.start('Prepare files',lambda cancel:self.model.prepare(gid,jid,revision,ids,cancel));return
        if any(i['state'] in WAITING for i in selected):
            if messagebox.askyesno('Download plan — '+self.title.get(),
                'Download this exact plan?\n\nLimit: 128 MiB, 40 requests, 5 minutes.\nNo game files are installed or changed.\nOther games remain available for review.',parent=self.root):
                self.start('Download files',lambda cancel:self.model.download(gid,jid,revision,cancel),True)
            return
        self.show_files()

    def import_zip(self):
        def go():
            gid,jid,revision=self.capture_job();ident=self.selected_mod()
            file=filedialog.askopenfilename(parent=self.root,title='Original mod ZIP',filetypes=[('ZIP archives','*.zip')])
            if file and messagebox.askyesno('Confirm original archive',f'Game: {self.title.get()}\nMod: {self.mod_rows[ident]["name"]}\n\nDid this ZIP come from the author’s official download?',parent=self.root):
                self.start('Import archive',lambda cancel:self.model.import_zip(gid,jid,revision,ident,Path(file),True))
        self.guard(go)

    def show_files(self):
        def go():
            gid,jid,_=self.capture_job();j=self.model.job(gid,jid)
            path=j.path
            if self.mods.selection():
                ident=self.selected_mod();e=j.checkpoint(ident,'ACQUIRED')
                if e:path=j.acquired(ident)[0].parent
            if os.name=='nt':os.startfile(str(path))
            else:
                self.root.clipboard_clear();self.root.clipboard_append(str(path));self.status.set('Local folder path copied; it is not included in AI context.')
        self.guard(go)

    def official_page(self):
        def go():
            ident=self.selected_mod();items=self.model.job(self.game_id,self.job_id).plan['items'] if self.job_id else self.recipe['items']
            url=next(i['download_page'] for i in items if i['id']==ident);parsed=urlparse(url)
            require(parsed.scheme=='https' and not parsed.username and not parsed.password,'UNSAFE_URL','Only an HTTPS author page can be opened.')
            webbrowser.open(url)
        self.guard(go)

    def mod_menu(self):
        m=self._menu(self.next_button)
        m.add_command(label='Show versions' if 'version' not in self.mods['displaycolumns'] else 'Hide versions',command=self.toggle_versions)
        m.add_separator()
        for label,fn in [('Official download page',self.official_page),('Inspect game folder',self.inspect_installed),
                         ('Record manual check',self.record_check),('Compare with another plan',self.compare_dialog),
                         ('Export for manager',self.manager_handoff),('Game support details',self.support_details),('Show exact item details',self.show_technical)]:m.add_command(label=label,command=fn)
        m.tk_popup(self.next_button.winfo_rootx(),self.next_button.winfo_rooty()+self.next_button.winfo_height());m.grab_release()

    def toggle_versions(self):
        self.mods.configure(displaycolumns=('use','name','version','status','next') if 'version' not in self.mods['displaycolumns'] else ('use','name','status','next'))
        self.mod_layout.fit_window()

    def import_recipe(self):
        if self.model.runner.active():
            self.status.set('Finish active tasks before updating game support.');return
        source=filedialog.askopenfilename(parent=self.root,title='Game support or legacy recipe',
                                         filetypes=[('Game support / recipe','*.json *.zip')])
        if not source:return
        def go():
            from game_mod_ops.support import read_pack, describe
            ispack=Path(source).suffix.lower()=='.zip' or read_json(Path(source)).get('kind')=='game_support_pack'
            if ispack:
                pack,_=read_pack(source);review=self.model.catalog.support.review(pack);v=review['after'];gid=v['game_id']
                old=self.model.catalog.recipes().get(gid)
                details=(f"{v['name']}\nManager: {v['manager_id']} · adapter: {v['adapter']}\n"
                         f"Recipe items: {v['mod_items']} · pack {v['pack_version']}\n"
                         f"Changed: {', '.join(review['changed_sections']) or 'None'}\n\n"
                         "Select this exact support revision for future plans? Existing jobs and game files will not be changed.")
                if messagebox.askyesno('Review game support',details,parent=self.root):
                    self.model.catalog.import_support(Path(source),reviewed_sha256=v['revision'],
                        expected_revision=review['before_revision'],expected_recipe_revision=old['revision'] if old else None,confirmed=True)
                    self.load_game(gid);self.status.set('Game support registered. No installation or download performed.')
            else:
                r=load_recipe(Path(source))
                if messagebox.askyesno('Register recipe',f'{r.get("name",r["game_id"])}\nGame ID: {r["game_id"]}\nManager: {r["manager_id"]}\nItems: {len(r["items"])}\n\nRegister this reviewed recipe? This does not install mods.',parent=self.root):
                    result=self.model.catalog.import_local(Path(source),confirmed=True);self.load_game(result['game_id'])
        self.guard(go)

    def create_support_template(self):
        if self.model.runner.active():self.status.set('Finish active tasks before changing game support.');return
        from game_mod_ops.support import scaffold
        win=tk.Toplevel(self.root);win.title('Create game support');win.transient(self.root)
        body=ttk.Frame(win,padding=14);body.pack(fill='both',expand=True)
        name=tk.StringVar(win);ident=tk.StringVar(win);exe=tk.StringVar(win,value='Game.exe');adapter=tk.StringVar(win,value='directory')
        for label,var in [('Game name',name),('Stable ID · lowercase-hyphens',ident),('Game executable · relative path',exe)]:
            ttk.Label(body,text=label).pack(anchor='w');ttk.Entry(body,textvariable=var,width=48).pack(fill='x',pady=(2,8))
        ttk.Label(body,text='Reusable format').pack(anchor='w')
        ttk.Combobox(body,textvariable=adapter,values=['umm','smapi','bepinex','directory','external'],state='readonly').pack(fill='x')
        ttk.Label(body,text='Creates a data template. Mod choices and exact paths still need review.',wraplength=440,style='Muted.TLabel').pack(fill='x',pady=10)
        def save():
            def run():
                pack=scaffold(ident.get(),name.get(),adapter.get(),exe.get())
                target=filedialog.asksaveasfilename(parent=win,title='Save game support',initialfile=ident.get()+'.json',defaultextension='.json')
                if not target:return
                from game_mod_ops.safety import json_new
                json_new(Path(target),pack);win.destroy();self.status.set('Data template saved. Import it after reviewing paths and adding mod choices.')
            self.guard(run)
        ttk.Button(body,text='Save template',style='Primary.TButton',command=save).pack(side='right')
        ttk.Button(body,text='Cancel',command=win.destroy).pack(side='right',padx=8);win.bind('<Escape>',lambda e:win.destroy());win.grab_set()

    def support_details(self):
        def go():
            from game_mod_ops.support import describe
            row=self.model.catalog.support.get(self.game_id);v=describe(row['pack'])
            self.detail_text('Game support',[('Game',v['name']),('Adapter',v['adapter']),('Pack version',v['pack_version']),
                ('Mod choices',v['mod_items']),('Installation','Not performed; native managers retain ownership'),
                ('Next','Add or update this game’s data pack, not the whole app.')],row['pack']);self.inspect_popup()
        self.guard(go)

    def copy_extension_brief(self):
        def go():
            from game_mod_ops.support import schema
            row=self.model.catalog.support.rows().get(self.game_id)
            brief={'task':'Extend this game with a reviewed data-only game_support_pack. Reuse supported adapters; do not rebuild the app.',
                   'game_id':self.game_id,'contract':schema(),'current_pack':row['pack'] if row else None,
                   'recipe':self.recipe,'requirements':['Use official sources and exact identifiers.','Validate with games_support_validate or Game-Support.py validate.',
                   'Keep custom presets, dependencies, source URLs and mod IDs in data.','Return one JSON pack; local import must show and approve its revision diff.',
                   'Separate capability, filesystem observation and runtime acceptance. Do not insert commands, secrets or machine paths.']}
            self.root.clipboard_clear();self.root.clipboard_append(json.dumps(brief,indent=2));self.status.set('Extension brief copied. It includes author support notes; review before sharing.')
        self.guard(go)

    def export_support(self):
        def go():
            target=filedialog.asksaveasfilename(parent=self.root,title='Export data-only game support',initialfile=self.game_id+'.json',defaultextension='.json')
            if target:self.model.catalog.support.export(self.game_id,Path(target));self.status.set('Support pack exported. No mod binaries or private settings included.')
        self.guard(go)

    def manager_handoff(self):
        def go():
            gid,jid,revision=self.capture_job()
            parent=filedialog.askdirectory(parent=self.root,title='Parent folder for new private manager handoff')
            if not parent:return
            if not messagebox.askyesno('Export for manager','Copy accepted original archives into an ordered private folder?\nThis does not install mods or change the game.',parent=self.root):return
            target=Path(parent)/('GameTools-handoff-'+jid)
            self.start('Export for manager',lambda cancel:self.model.export_for_manager(gid,jid,revision,target,True))
        self.guard(go)

    def refresh_requests(self):
        previous=self.requests.selection();self.requests.delete(*self.requests.get_children());self.request_rows={};self.last_review=None
        if self.recipe:
            for row in self.model.service(self.game_id).list_requests():
                ident=row['request_id'];self.request_rows[ident]=row
                self.requests.insert('','end',iid=ident,values=(OP_LABELS.get(row.get('operation'),'Existing request'),STATE_LABELS.get(row['status'],row['status'].replace('_',' ').title()),ident[:18]))
        if previous and self.requests.exists(previous[0]):self.requests.selection_set(previous[0]);self.request_selected()
        else:
            self.approve_button.configure(state='disabled');self.reject_button.configure(state='disabled')

    def request_selected(self,_e=None):
        ids=self.requests.selection()
        if not ids:return
        def go():
            review=self.model.request_review(self.game_id,ids[0]);self.last_review=copy.deepcopy(review)
            pending=review['status']=='AWAITING_LOCAL_APPROVAL' and review['current']
            self.approve_button.configure(state='normal' if pending else 'disabled')
            self.reject_button.configure(state='normal' if review['status']=='AWAITING_LOCAL_APPROVAL' else 'disabled')
            self.detail_text(OP_LABELS.get(review['operation'],review['operation']),[
                ('Target game',review['game_name']),('State',STATE_LABELS.get(review['status'],review['status'])),
                ('What will change',review['effect']),('Exact items',', '.join(review['items']) or 'None'),
                ('Limit',review['limit']),('Latest source check',review['blocking_reason'] or 'Matches the reviewed job and recipe'),
                ('Result',review['result']['status'] if review['result'] else 'Not executed')],review)
        self.guard(go)

    def import_request(self):
        source=filedialog.askopenfilename(parent=self.root,title='AI proposal JSON',filetypes=[('JSON request','*.json')])
        if not source:return
        def go():
            r=read_json(Path(source),32768)
            require(type(r) is dict and set(r)=={'game_id','operation','arguments','request_id'},'INVALID_ARGUMENTS','A workbench proposal needs game_id, operation, arguments and request_id; no approval field.')
            require(r['game_id']==self.game_id,'GAME_MISMATCH','Select the request’s target game before importing it.')
            self.model.service(self.game_id).propose(r['operation'],r['arguments'],request_id=r['request_id'])
            self.refresh_requests();self.requests.selection_set(r['request_id']);self.request_selected();self.tabs.select(self.requests_page)
        self.guard(go)

    def test_request(self):
        def go():
            require(self.recipe is not None,'RECIPE_REQUIRED','Import a recipe first.')
            r=self.model.service(self.game_id).propose('mods.create_plan',{'selected':list(self.view.value['games'][self.game_id].get('selected',[])),'mode':self.mode.get()})
            self.refresh_requests();self.requests.selection_set(r['request_id']);self.request_selected()
            self.status.set('Local test proposal created. No action runs until you approve it. This is not a live AI connection test.')
        self.guard(go)

    def approve_request(self):
        review=copy.deepcopy(self.last_review)
        if not review:return
        if review['game_id']!=self.game_id:self.status.set('Select and review the request’s game again.');return
        gid=review['game_id'];service=self.model.service(gid);ident=review['request_id'];sha=review['request_sha256']
        if not messagebox.askyesno('Approve — '+review['game_name'],review['effect']+'\n\nGame: '+review['game_name']+'\nItems: '+', '.join(review['items'])+'\nLimit: '+review['limit'],parent=self.root):return
        def run(cancel):
            return self.model.approve_request(gid,ident,sha,cancel)
        self.start('Approve '+OP_LABELS.get(review['operation'],'request'),run,review['operation']=='mods.download')

    def reject_request(self):
        review=copy.deepcopy(self.last_review)
        if not review:return
        self.guard(lambda:self.model.service(review['game_id']).reject_local(review['request_id'],review['request_sha256']))
        self.refresh_requests()

    def refresh_checks(self):
        previous=self.checks_tree.selection();self.checks_tree.delete(*self.checks_tree.get_children());self.check_rows={}
        self.inspect_installed_button.configure(state='normal' if self.game_id in self.model.catalog.support.rows() or self.job_id and self.game_id=='pathfinder-kingmaker' else 'disabled')
        if not self.job_id:return
        for n,r in enumerate(self.model.checks(self.game_id,self.job_id)):
            key=str(n);self.check_rows[key]=r
            result={'passed':'Reported pass','failed':'Reported failure','not_tested':'Not tested'}[r['outcome']]
            self.checks_tree.insert('','end',iid=key,values=(r['item_id'],MANUAL_CHECKS[r['check']],result,'Stale — plan changed' if r['stale'] else 'Current job revision'))
        if previous and self.checks_tree.exists(previous[0]):self.checks_tree.selection_set(previous[0])

    def check_selected(self,_e=None):
        selected=self.checks_tree.selection()
        if selected:
            r=self.check_rows[selected[0]]
            self.detail_text('Manual observation',[('Game',self.title.get()),('Item',r['item_id']),('Check',MANUAL_CHECKS[r['check']]),('Reported outcome',r['outcome']),('Note (local only)',r['note'] or 'No note'),('Validity','Stale job revision' if r['stale'] else 'Same job revision'),('Evidence','Operator report, not independently verified')],r)

    def record_check(self):
        def go():
            gid,jid,revision=self.capture_job();j=self.model.job(gid,jid)
            win=tk.Toplevel(self.root);win.title('Record manual check — '+self.title.get());win.transient(self.root)
            body=ttk.Frame(win,padding=16);body.pack(fill='both',expand=True)
            item=tk.StringVar(win,value=self._selected_item if self._selected_item in j.items else next(iter(j.items)))
            check=tk.StringVar(win,value=next(iter(MANUAL_CHECKS)));result=tk.StringVar(win,value='not_tested')
            for label,var,values in [('Mod',item,list(j.items)),('Check',check,list(MANUAL_CHECKS)),('Your result',result,['not_tested','passed','failed'])]:
                ttk.Label(body,text=label).pack(anchor='w');ttk.Combobox(body,textvariable=var,values=values,state='readonly',width=40).pack(fill='x',pady=(2,8))
            ttk.Label(body,text='Note · stays local').pack(anchor='w');note=tk.Text(body,width=50,height=4);note.pack(fill='x')
            ttk.Label(body,text='This records your observation. It does not verify or launch a game.',wraplength=440,style='Muted.TLabel').pack(fill='x',pady=8)
            def save():
                r=self.guard(lambda:self.model.record_check(gid,jid,revision,item.get(),check.get(),result.get(),note.get('1.0','end-1c')))
                if r:win.destroy();self.refresh_checks();self.tabs.select(self.checks_page)
            buttons=ttk.Frame(body);buttons.pack(fill='x');ttk.Button(buttons,text='Cancel',command=win.destroy).pack(side='right');ttk.Button(buttons,text='Save observation',style='Primary.TButton',command=save).pack(side='right',padx=5)
            win.bind('<Escape>',lambda e:win.destroy());win.grab_set()
        self.guard(go)

    def inspect_installed(self):
        def go():
            gid=self.game_id;jid=self.job_id
            rev=self.model.revision(self.model.job(gid,jid)) if jid else None
            folder=filedialog.askdirectory(parent=self.root,title=self.title.get()+' folder · read only')
            if folder:self.start('Inspect installed files',lambda cancel:self.model.inspect_installed(gid,jid,rev,Path(folder)))
        self.guard(go)

    def compare_dialog(self):
        def go():
            gid,jid,_=self.capture_job();current=self.model.job(gid,jid)
            others=[r['job_id'] for r in self.model.jobs(gid) if r['job_id']!=jid]
            require(bool(others),'SECOND_PLAN_REQUIRED','This game needs a second saved plan to compare.')
            win=tk.Toplevel(self.root);win.title('Compare intended mod sets');win.transient(self.root)
            frame=ttk.Frame(win,padding=14);frame.pack(fill='both',expand=True)
            choice=tk.StringVar(win,value=others[0]);ttk.Label(frame,text='Compare with').pack(anchor='w')
            ttk.Combobox(frame,textvariable=choice,values=others,state='readonly',width=50).pack(fill='x',pady=8)
            def compare():
                old=self.model.job(gid,choice.get());diff=self.model.compare_plans(gid,old.path.name,jid)
                added,removed,changed=diff['added'],diff['removed'],diff['changed']
                self.detail_text('Plan comparison',[('Game',self.title.get()),('Added',', '.join(added) or 'None'),('Removed',', '.join(removed) or 'None'),('Changed',', '.join(sorted(changed)) or 'None'),('Meaning','Compared intended plans, not the installed state. Nothing was applied.')],{'from_job':old.path.name,'to_job':jid,'added':added,'removed':removed,'changed':changed});win.destroy();self.inspect_popup()
            ttk.Button(frame,text='Compare',command=compare).pack(side='right');win.grab_set()
        self.guard(go)

    def copy_context(self):
        def go():
            data=self.model.context(self.game_id)
            self.root.clipboard_clear();self.root.clipboard_append(json.dumps(data,indent=2,ensure_ascii=False))
            self.status.set('Game-scoped context copied. Nothing was sent; private paths and manual notes are excluded.')
        self.guard(go)

    def copy_setup(self):
        if not messagebox.askyesno('Local client setup', 'Copy private setup for a compatible local MCP client?\nThis includes local paths. It does not connect this chat or start a server.\nOnly read tools and proposals are exposed; local approval is still required.',parent=self.root):return
        exe=Path(sys.executable)
        if exe.name.lower()=='pythonw.exe':exe=exe.with_name('python.exe')
        if not exe.is_file():self.status.set('A console Python executable is required for MCP stdio; no setup was copied.');return
        cfg={'mcpServers':{'game-tools':{'command':str(exe),'args':['-B',str(BASE/'scripts/GameToolAI.py'),'--data-dir',str(self.model.data_dir),'--workspaces','--allow-requests','stdio']}}}
        self.root.clipboard_clear();self.root.clipboard_append(json.dumps(cfg,indent=2));self.status.set('Private client setup copied. Native client acceptance is still unverified.')

    def show_technical(self):
        win=tk.Toplevel(self.root);win.title('Exact local record');win.geometry('740x520');win.transient(self.root)
        text=tk.Text(win,wrap='word',font=('Consolas',10));text.pack(fill='both',expand=True)
        text.insert('end',json.dumps(self.raw_detail,indent=2,ensure_ascii=False,default=str));text.configure(state='disabled')
        ttk.Button(win,text='Close',command=win.destroy).pack(anchor='e',padx=8,pady=8)

    def inspect_popup(self):
        if str(self.details_frame) in self.shell.panes():self.detail.focus_set();return
        win=tk.Toplevel(self.root);win.title('Inspector — '+self.title.get());win.geometry('520x580');win.transient(self.root)
        text=tk.Text(win,wrap='word',font=self.body_font,padx=14,pady=14);text.pack(fill='both',expand=True)
        text.insert('end',self.detail.get('1.0','end-1c'));text.configure(state='disabled')
        ttk.Button(win,text='Technical details',command=self.show_technical).pack(side='left',padx=8,pady=8)
        ttk.Button(win,text='Close',command=win.destroy).pack(side='right',padx=8,pady=8)

    def game_picker(self):
        win=tk.Toplevel(self.root);win.title('Choose game');win.transient(self.root)
        frame=ttk.Frame(win,padding=12);frame.pack(fill='both',expand=True)
        for row in self.model.game_rows():
            def pick(gid=row['id']):win.destroy();self.guard(lambda:self.load_game(gid))
            ttk.Button(frame,text=row['name'],command=pick).pack(fill='x',pady=3)
        win.bind('<Escape>',lambda e:win.destroy())

    def tab_changed(self,_e=None):
        current=self.tabs.select()
        if current==str(self.requests_page):self.refresh_requests()
        if current==str(self.checks_page):self.refresh_checks()

    def change_view(self):self.apply_style();self.remember();self.queue_layout()
    def reset_view(self):self.zoom.set(100);self.density.set('Compact');self.theme.set('Dark');self.change_view()
    def zoom_key(self,event,delta):
        if self.root.grab_current() is not None:return None
        self.zoom.set(100 if delta==0 else max(80,min(200,self.zoom.get()+delta)));self.change_view();return 'break'
    def focus_search(self,event=None):
        if self.root.grab_current() is not None:return None
        self.tabs.select(self.mods_page);self.search.focus_set();self.search.selection_range(0,'end');return 'break'
    def queue_layout(self,event=None):
        if self.closed:return
        if event is not None and event.widget is not self.root:return
        if self._layout_job is None:self._layout_job=self.after_idle(self.layout)
    def layout(self):
        self._layout_job=None
        if self.closed:return
        w=self.root.winfo_width();factor=self.zoom.get()/100
        show_rail=w>=round(970*factor);show_details=w>=round(1160*factor)
        panes=self.shell.panes()
        if show_rail and str(self.rail) not in panes:self.shell.insert(0,self.rail,weight=0)
        if not show_rail and str(self.rail) in panes:self.shell.forget(self.rail)
        panes=self.shell.panes()
        if show_details and str(self.details_frame) not in panes:self.shell.add(self.details_frame,weight=0)
        if not show_details and str(self.details_frame) in panes:self.shell.forget(self.details_frame)
        self._layout_header(w,show_rail)
        if show_rail:
            try:self.shell.sashpos(0,round(240*factor))
            except tk.TclError:pass
        if show_details:
            try:self.shell.sashpos(len(self.shell.panes())-2,max(480,w-round(330*factor)))
            except tk.TclError:pass
        available=max(280,self.main.winfo_width()-40)
        self.title_label.configure(wraplength=max(220,available-150));self.sub_label.configure(wraplength=available)
        self.footer_note.configure(wraplength=available);self.status_label.configure(wraplength=max(500,w-32))

    def _layout_header(self,width,show_rail):
        # Wrap the controls themselves, not merely the containing strip. At 200%
        # text size a single packed row clipped More on a narrow window.
        self.view_button.configure(text=f'View · {self.zoom.get()}%')
        visible=tuple(b for b in self._header_buttons
                      if not (b is self.games_button and show_rail)
                      and not (b is self.samples_button and self._has_saved_jobs))
        widths=tuple(b.winfo_reqwidth()+6 for b in visible)
        available=max(240,width-28)
        self.header_activity.configure(wraplength=max(180,available-self.brand.winfo_reqwidth()-28))
        single_row=sum(widths)
        inline=single_row+self.brand.winfo_reqwidth()+self.header_activity.winfo_reqwidth()+36<=available
        key=(tuple(str(b) for b in visible),widths,available,inline)
        if key==self._header_layout_key:return
        self._header_layout_key=key
        if inline:self.header_controls.grid(row=0,column=2,columnspan=1,sticky='e',pady=0)
        else:self.header_controls.grid(row=1,column=0,columnspan=3,sticky='w',pady=(6,0))
        for b in self._header_buttons:b.place_forget()
        x=3;y=0;row_height=0
        for b,requested in zip(visible,widths):
            height=b.winfo_reqheight()
            if x>3 and x+requested-3>available:
                y+=row_height+4;x=3;row_height=0
            b.place(x=x,y=y,width=requested-6,height=height)
            x+=requested;row_height=max(row_height,height)
        self.header_controls.configure(width=single_row if inline else min(single_row,available),
                                       height=y+row_height)

    def refresh_activity(self):
        active=self.model.runner.active();keybind_active=bool(self.keybind_panel.working)
        count=len(active)+(1 if keybind_active else 0)
        self.activity_count.set(f'{count} active · other games available' if count else 'No active tasks')
        rows=list(active)
        if keybind_active:
            rows.append({'activity_id':'keybind-pane-active','game_id':self.keybind_panel.game.get() or self.game_id,
                'label':'Keybind operation','status':'RUNNING','job_id':None})
        rows+=self.model.runner.history[-5:][::-1]
        self.activity.delete(*self.activity.get_children())
        for row in rows:
            self.activity.insert('','end',iid=row['activity_id'],values=(row['game_id'],row['label'],row['status'].replace('_',' ').title()))
        self.stop_all.configure(state='normal' if active or keybind_active else 'disabled')
        if rows:self.activity_frame.grid(row=2,column=0,sticky='ew')
        else:self.activity_frame.grid_remove()

    def activity_selected(self,_e=None):
        ids=self.activity.selection()
        if not ids:return
        if ids[0]=='keybind-pane-active':
            self.detail_text('Keybind operation',[('Game',self.keybind_panel.game.get() or self.game_id),('State','Running'),('Status',self.keybind_panel.status.get()),('Scope','Local activity. Returned is not a claim of installation or gameplay success.')]);return
        row=next((r for r in self.model.runner.active()+self.model.runner.history if r['activity_id']==ids[0]),None)
        if row:self.detail_text(row['label'],[('Game',row['game_id']),('State',row['status']),('Job',row['job_id'] or 'New plan'),('Scope','Local activity. Returned is not a claim of installation or gameplay success.')],row)

    def poll(self):
        if self.closed:return
        changed=False
        try:
            while True:
                row=self.model.runner.events.get_nowait();changed=True
                result=row.get('result',{})
                new_job=result.get('new_job') if isinstance(result,dict) else None
                if not new_job and isinstance(result,dict) and result.get('operation')=='mods.create_plan':
                    new_job=result.get('result',{}).get('job_id')
                if row['game_id']==self.game_id:
                    if new_job:self.job_id=new_job
                    # Preserve current game and another game's draft on late completion.
                    self.status.set(row['label']+' · '+row['status'].replace('_',' ').lower())
                    if isinstance(result,dict) and result.get('status') in {'UNKNOWN_EFFECTS','CONCURRENT_CHANGE','HASH_MISMATCH','GAME_MISMATCH'}:self.detail_text('Action needs review',[('Result',result.get('message',result['status']))],result)
                    elif isinstance(result,dict) and result.get('evidence')=='filesystem_metadata_not_runtime':
                        v=result['result'];comparison=result.get('comparison',{}).get('items',[])
                        self.detail_text('Installed-folder inspection',[('Game',self.title.get()),
                            ('Status',v.get('inventory_status','Filesystem metadata observed')),('Mod records',len(v['mods'])),
                            ('Warnings','; '.join(v.get('warnings',[])) or 'None'),
                            ('Plan comparison',str(len(comparison))+' mod choices compared'),
                            ('Runtime','Not checked; this is file metadata only')]+
                            [(c['item_id'],c['state'].replace('_',' ').lower()+((' · '+c['observed_version']) if c.get('observed_version') else '')) for c in comparison[:8]]+
                            ([('More results',str(len(comparison)-8)+' in exact details')] if len(comparison)>8 else []),result)
                elif new_job:self.view.value['games'].setdefault(row['game_id'],{})['job_id']=new_job
        except queue.Empty:pass
        if changed:
            self.guard(lambda:(self.refresh_jobs(),self.refresh_mods(),self.refresh_requests(),self.refresh_checks(),self.refresh_games(),self.remember()))
        if changed or self.model.runner.active():self.refresh_activity()
        if self.watch.get() and self.tabs.select()==str(self.requests_page) and self.model.runner.can_start(self.game_id)[0]:
            self.guard(self.refresh_requests)
        self._tick=self.after(2000 if self.watch.get() else 180,self.poll)

    def stop(self,game_id=None):
        self.model.runner.stop(game_id)
        if self.keybind_panel.working:self.keybind_panel.cancel.set()
        self.refresh_activity();self.status.set('Stop requested at the next safe boundary. No process was killed.')

    def samples(self):
        if self.model.runner.active():
            self.status.set('Finish active work before adding samples.');return
        if not messagebox.askyesno('Try the sample workflow',
                'Create two fictional game workspaces with a harmless text file?\n\n'
                'No network, real mods, game files, or production settings are used.',parent=self.root):return
        def add():
            result=self.model.create_samples_local(confirmed=True)
            for row in result['jobs']:
                self.view.value['games'].setdefault(row['game_id'],{})['job_id']=row['job_id']
            self.load_game(result['jobs'][0]['game_id'])
            self.status.set('Sample Alpha is prepared. Sample Beta is downloaded. These are not real games.')
        self.guard(add)

    def open_original(self):
        if self.model.runner.active() or self.keybind_panel.working:
            self.status.set('Finish or stop active tasks before switching the whole interface.');return
        if self.on_original:self.remember();self.close();self.on_original()
        else:self.status.set('Use OPEN Original UI after closing this workbench. The preview profile is shared.')
    def open_guide(self):
        p=BASE/'docs/WORKBENCH-REVIEW.md'
        if p.exists():
            self.detail_text('Changes and remaining limits',[('Guide',p.read_text(encoding='utf-8'))])
            self.inspect_popup()
    def close(self):
        if self.closed:return True
        if self.model.runner.active() or self.keybind_panel.working:
            self.stop();messagebox.showinfo('Operation still active','Stop requested. Close after the active operation reaches its safe boundary.',parent=self.root);return False
        self.remember();self.closed=True
        if self._tick:self.after_cancel(self._tick)
        if self._layout_job:self.after_cancel(self._layout_job)
        self.mod_layout.close();self.root.destroy();return True


def gui(data_dir,*,on_original=None):
    root=tk.Tk();app=Workbench(root,data_dir,on_original=on_original);root.game_tools_workbench=app
    root.mainloop()
