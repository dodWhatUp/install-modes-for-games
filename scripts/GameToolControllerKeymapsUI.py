"""Draft-only controller keymap editor embedded in the existing Game Tools UI."""
from __future__ import annotations
import os, tempfile, webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import GameToolControllerKeymaps as api
import GameToolRewasd as rewasd
from GameToolCompactUI import Selector, FlowToolbar, ScrollableFrame, TableLayout

VERSION='0.1.0'


class NamedSelector(Selector):
    """Shared editable behavior; private paths/hashes stay out of field labels."""
    def set_choices(self,choices):
        self.records={};counts={}
        for key,label in choices:
            count=counts.get(label,0)+1;counts[label]=count
            self.records[key]=label if count==1 else label+' ('+str(count)+')'
        self.labels={label:key for key,label in self.records.items()}
        self.configure(values=list(self.records.values()))


class KeymapsPanel:
    def __init__(self,parent,directory,status=None):
        self.parent=parent;self.directory=Path(directory);self.library=api.DraftLibrary(directory)
        self.status=status.set if hasattr(status,'set') else status or (lambda _:None)
        self.draft=None;self.pin='absent';self.closed=False
        self.scroll=ScrollableFrame(parent,min_width=0);self.scroll.pack(fill='both',expand=True);body=self.scroll.body
        form=ttk.Frame(body);form.pack(fill='x');form.columnconfigure(1,weight=1)
        ttk.Label(form,text='Game').grid(row=0,column=0,sticky='w',padx=(0,8),pady=4)
        self.game=NamedSelector(form,width=28);self.game.grid(row=0,column=1,sticky='w',pady=4)
        ttk.Label(form,text='Native source').grid(row=1,column=0,sticky='w',padx=(0,8),pady=4)
        self.source=NamedSelector(form,width=28);self.source.grid(row=1,column=1,sticky='w',pady=4)
        bar=FlowToolbar(body);bar.pack(fill='x',pady=5)
        for label,command in [('Read profile',self.read_profile),('Save draft',self.save),('Preview',self.preview),('Export…',self.export),('Refresh sources',self.refresh)]:bar.add(label,command)
        self.summary=tk.StringVar(value='Read a native profile to prepare a game-specific controller draft.')
        self.notice=ttk.Label(body,textvariable=self.summary,wraplength=700);self.notice.pack(fill='x',pady=5)
        selectors=ttk.Frame(body);selectors.pack(fill='x');selectors.columnconfigure(1,weight=1);selectors.columnconfigure(3,weight=1)
        ttk.Label(selectors,text='Layer').grid(row=0,column=0,sticky='w',padx=(0,8))
        self.layer=NamedSelector(selectors,on_select=lambda _:self.refresh_rows(),width=20);self.layer.grid(row=0,column=1,sticky='ew',padx=(0,12))
        ttk.Label(selectors,text='Context').grid(row=0,column=2,sticky='w',padx=(0,8))
        self.context=NamedSelector(selectors,on_select=lambda _:self.refresh_rows(),width=20);self.context.grid(row=0,column=3,sticky='ew')
        table_frame=ttk.Frame(body);table_frame.pack(fill='both',expand=True,pady=8);table_frame.columnconfigure(0,weight=1);table_frame.rowconfigure(0,weight=1)
        columns=('control','output','action','evidence')
        self.table=ttk.Treeview(table_frame,columns=columns,show='headings',height=9)
        for name,width in [('control',150),('output',180),('action',320),('evidence',140)]:
            self.table.heading(name,text=name.capitalize());self.table.column(name,width=width,minwidth=70)
        self.table.grid(row=0,column=0,sticky='nsew');ys=ttk.Scrollbar(table_frame,orient='vertical',command=self.table.yview);ys.grid(row=0,column=1,sticky='ns');self.table.configure(yscrollcommand=ys.set)
        self.table_layout=TableLayout(self.table);self.table.bind('<<TreeviewSelect>>',lambda _:self.select_row())
        editor=ttk.LabelFrame(body,text='Selected control · draft annotation',padding=8);editor.pack(fill='x');editor.columnconfigure(1,weight=1)
        ttk.Label(editor,text='Action').grid(row=0,column=0,sticky='w',padx=(0,8),pady=3)
        self.action=NamedSelector(editor,on_select=self.choose_action,width=32);self.action.grid(row=0,column=1,sticky='w',pady=3)
        ttk.Label(editor,text='Icon').grid(row=1,column=0,sticky='w',padx=(0,8),pady=3)
        self.icon=NamedSelector(editor,choices=[(key,(glyph+' '+key).strip()) for key,glyph in api.ICONS.items()],width=18);self.icon.grid(row=1,column=1,sticky='w',pady=3)
        ttk.Button(editor,text='Update row',command=self.update_row).grid(row=2,column=1,sticky='w',pady=4)
        self.show_icons=tk.BooleanVar(value=True)
        ttk.Checkbutton(editor,text='Show action icons in previews',variable=self.show_icons,command=self.change_icon_visibility).grid(row=3,column=1,sticky='w')
        self.scope=ttk.Label(body,text='Draft only. Native Apply and live Overlay publication remain separate. The neutral controller schematic does not verify physical positions.',wraplength=700)
        self.scope.pack(fill='x',pady=8)
        body.bind('<Configure>',lambda event:[w.configure(wraplength=max(180,event.width-24)) for w in (self.notice,self.scope)],add='+')
        self.refresh()

    def report(self,error):self.summary.set(str(error));self.status(str(error))
    def refresh(self):
        try:
            old_game=self.game.selected_id;old_source=self.source.selected_id
            from GameToolGameProfiles import Profiles
            games=Profiles(self.directory).games()
            self.game.set_choices(list(games.items()));self.game.select(old_game or next(iter(games),None))
            configs=[x for x in rewasd.discover() if 'error' not in x]
            self.source.set_choices([(x['path'],Path(x['path']).stem) for x in configs]);self.source.select(old_source or next((x['path'] for x in configs),None))
        except Exception as error:self.report(error)

    def set_source(self,game_id,game_name,config_path):
        """Optional adapter for the containing Controller tools page."""
        choices=list(self.game.records.items()) if hasattr(self.game,'records') else []
        choices=[x for x in choices if x[0]!=game_id]+[(game_id,game_name)]
        self.game.set_choices(choices);self.game.select(game_id)
        configs=list(self.source.records.items()) if hasattr(self.source,'records') else []
        value=str(config_path);configs=[x for x in configs if x[0]!=value]+[(value,Path(value).stem)]
        self.source.set_choices(configs);self.source.select(value)
        self.read_profile()

    def read_profile(self):
        try:
            api.require(self.game.selected_id and self.source.selected_id,'Choose a game and native source first')
            game=self.game.selected_id;name=self.game.records[game]
            workbook=None
            if game=='doom-the-dark-ages':
                from GameToolKeymapBuilder import SourceLibrary
                from GameToolControlsPlanner import WorkbookLibrary
                path=WorkbookLibrary(SourceLibrary(self.directory)).path(game)
                if path.exists():
                    from game_keybind_ops.core import Service
                    workbook=WorkbookLibrary(SourceLibrary(self.directory)).load(game)
                    api.planner.check_sources(workbook,Service(self.directory))
            draft=api.draft_from_profile(self.source.selected_id,game,name,workbook=workbook)
            if self.library.path(draft['id']).exists():draft=self.library.load(draft['id']);self.pin=api.fingerprint(draft)
            else:self.pin='absent'
            self.draft=draft;self.show_icons.set(draft['presentation']['show_icons'])
            self.layer.set_choices([(x['id'],x['label']) for x in draft['layers']]);self.layer.select('base')
            self.context.set_choices([(x,x) for x in draft['contexts']]);self.context.select('gameplay')
            self.action.set_choices([(x['id'],x['label']+' ['+x['native_key']+' / '+x['context']+']') for x in draft['action_catalog']])
            self.refresh_rows()
            self.summary.set(str(len(draft['bindings']))+' explicit mappings read. Game actions and physical positions retain their evidence labels; source '+api.source_status(draft)['state']+'.')
        except Exception as error:self.report(error)

    def refresh_rows(self):
        if not self.draft or not self.layer.selected_id or not self.context.selected_id:return
        selected=self.table.selection();selected=selected[0] if selected else None
        for row in self.table.get_children():self.table.delete(row)
        for row in api.rows(self.draft,self.layer.selected_id,self.context.selected_id):
            icon=api.ICONS[row['icon']]+' ' if self.show_icons.get() else ''
            self.table.insert('', 'end', iid=row['id'], values=(row['control'],row['output'],icon+row['action'],row['evidence']))
        if selected in self.table.get_children():self.table.selection_set(selected)

    def select_row(self):
        if not self.draft:return
        selected=self.table.selection()
        if not selected:return
        row=next(x for x in self.draft['bindings'] if x['id']==selected[0])
        value=row['annotations'].get(self.context.selected_id,{'label':'','icon':'unknown'})
        self.action.set(value['label']);self.icon.select(value['icon'])

    def choose_action(self,identity):
        if not self.draft:return
        item=next((x for x in self.draft['action_catalog'] if x['id']==identity),None)
        if item:self.action.set(item['label']);self.icon.select(item['icon'])

    def update_row(self):
        try:
            api.require(self.draft and self.table.selection(),'Choose a control row')
            self.draft=api.annotate(self.draft,self.table.selection()[0],self.context.selected_id,self.action.get(),self.icon.selected_id or 'unknown')
            self.refresh_rows();self.summary.set('Row updated in memory. Save draft retains it; native outputs remain unchanged.')
        except Exception as error:self.report(error)

    def change_icon_visibility(self):
        if self.draft:
            self.draft['presentation']['show_icons']=self.show_icons.get();self.refresh_rows()

    def save(self):
        try:
            api.require(self.draft is not None,'Read a profile first')
            self.pin=self.library.save(self.draft,self.pin);self.summary.set('Controller draft saved. No native Apply or Overlay publication occurred.')
        except Exception as error:self.report(error)

    def preview(self):
        try:
            api.require(self.draft is not None,'Read a profile first')
            self.library.root.mkdir(parents=True,exist_ok=True)
            folder=Path(tempfile.mkdtemp(prefix='preview-',dir=self.library.root))/'export'
            api.export_bundle(self.draft,folder,directory=self.directory)
            page=folder/'controller-preview.html'
            if os.name=='nt':os.startfile(page)
            else:webbrowser.open(page.as_uri())
            self.summary.set('Draft preview opened with neutral front/back reference and all layer/context action tables.')
        except Exception as error:self.report(error)

    def export(self):
        try:
            api.require(self.draft is not None,'Read a profile first')
            parent=filedialog.askdirectory(parent=self.parent,title='Choose parent folder for a new controller draft export')
            if not parent:return
            folder=Path(parent)/(self.draft['id']+'-r'+str(self.draft['revision']))
            api.export_bundle(self.draft,folder,directory=self.directory);self.summary.set('Exported draft JSON, searchable action preview and controller schematic to '+str(folder))
        except Exception as error:self.report(error)

    def close(self):
        if self.closed:return
        self.closed=True;self.table_layout.close();self.scroll.close()
