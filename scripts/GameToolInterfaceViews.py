"""Existing/New views in one Hub; native engines and applied state keep their owners."""
from __future__ import annotations
import json,os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from GameToolUnified import atomic_json
from GameToolUIReviewModel import ReviewModel

VERSION='1.0.1'
MODES=('Existing','New')

class InterfacePreference:
    def __init__(self,path):self.path=Path(path)
    def read(self):
        if not self.path.exists():return {'schema_version':1,'interface':'Existing'}
        if self.path.stat().st_size>65536:raise ValueError('Interface preference exceeds its size bound.')
        obj=json.loads(self.path.read_text(encoding='utf-8'))
        if type(obj) is not dict or obj.get('schema_version')!=1 or obj.get('interface') not in MODES:raise ValueError('Unsupported interface preference; existing view retained.')
        return obj
    def select(self,mode):
        if mode not in MODES:raise ValueError('Choose Existing or New.')
        obj=self.read();obj['interface']=mode
        atomic_json(self.path,obj)

class IntegratedModel(ReviewModel):
    """Retain earlier preview drafts, but new saved profiles share the original owner."""
    def save_profile(self,instance,name,changes,revision):
        return self.controls.save_profile_local(instance,name,changes,revision)
    def resources(self,page,instance=None):
        rows=super().resources(page,instance)
        names={'parallel-profiles':'Earlier interface profiles','parallel-data':'New interface settings and drafts','exports':'Prepared files'}
        for row in rows:
            row['label']=names.get(row['id'],row['label'])
            if row.get('origin','').startswith('Parallel preview'):row['origin']='New interface'
        return rows

class InterfaceViews:
    def __init__(self,root,notebook,controls,data_dir,status,*,install_root=None,preference=None,app_factory=None,model_factory=None):
        self.root,self.notebook,self.controls,self.data_dir,self.status=root,notebook,controls,Path(data_dir),status
        self.install_root=Path(install_root) if install_root else None
        self.preference=preference or InterfacePreference(self.data_dir/'interface-choice.json')
        self.app_factory=app_factory;self.model_factory=model_factory
        self.app=None;self.host=None;self.original=[];self.shortcut_scripts={};self.shortcut_ids={};self.closed=False;self.mode='Existing';self.original_topmost=None
        self.bar=ttk.Frame(root,padding=(12,5));original=root.pack_slaves()
        self.bar.pack(side='top',fill='x',**({'before':original[0]} if original else {}))
        ttk.Label(self.bar,text='Interface').pack(side='left')
        self.selected=tk.StringVar(root,value='Existing');self.selector=ttk.Combobox(self.bar,textvariable=self.selected,values=MODES,state='readonly',width=11)
        self.selector.pack(side='left',padx=(6,10));self.selector.bind('<<ComboboxSelected>>',lambda _:self.show(self.selected.get()))
        self.tools_button=ttk.Menubutton(self.bar,text='All tools');self.menu=tk.Menu(self.tools_button,tearoff=False,postcommand=self.update_tools);self.tools_button.configure(menu=self.menu);self.tools_button.pack(side='left')
        self.launcher=ttk.Button(self.bar,text='Show APP LAUNCHER',command=self.show_launcher);self.launcher.pack(side='right')
        self.state_label=ttk.Label(self.bar,textvariable=status,wraplength=600);self.state_label.pack(side='left',fill='x',expand=True,padx=10)
        self.bar.bind('<Configure>',lambda event:self.state_label.configure(wraplength=max(140,event.width-470)))
        try:saved=self.preference.read();self.startup_mode=saved['interface']
        except (ValueError,OSError) as error:self.startup_mode='Existing';status.set(str(error))
        self._startup=root.after(0,lambda:self.show(self.startup_mode,persist=False))
        self.update_tools()
    def review_root(self):
        value=self.preference.read().get('review_root')
        return Path(value) if value else self.data_dir.parent/(self.data_dir.name+'-Interface-Views')
    def create_app(self):
        from GameToolUIReview import ReviewApp
        model=(self.model_factory or IntegratedModel)(self.data_dir,self.review_root(),self.install_root,controls=self.controls,view_name='view-mods.json')
        host=ttk.Frame(self.root)
        try:app=(self.app_factory or ReviewApp)(self.root,model,host=host,embedded=True)
        except Exception:host.destroy();raise
        self.host,self.app=host,app
    def _new_shortcuts(self):
        shortcuts={'<Control-f>':self.app.open_finder,'<Control-Shift-F>':lambda:self.app.open_finder('Selected game'),'<Control-r>':self.app.refresh,'<Control-k>':self.app.game.focus_set}
        # Existing bindings are restored byte-for-byte when returning; the host
        # WM_DELETE_WINDOW handler, game inputs and native hotkeys are untouched.
        for sequence,action in shortcuts.items():
            self.shortcut_scripts[sequence]=self.root.bind(sequence)
            self.shortcut_ids[sequence]=self.root.bind(sequence,lambda event,fn=action:(fn(),'break')[1])
    def _restore_shortcuts(self):
        for sequence,script in self.shortcut_scripts.items():
            self.root.unbind(sequence,self.shortcut_ids[sequence])
            if script:self.root.bind(sequence,script)
        self.shortcut_scripts={};self.shortcut_ids={}
    def _restore_original(self):
        # Reinsert in the exact original order, including the banner that stays
        # visible in New. Merely appending hidden frames would reorder it.
        for widget,_ in self.original:
            if widget.winfo_exists():widget.pack_forget()
        for widget,options in self.original:
            if widget.winfo_exists():widget.pack(**options)
    def show(self,mode,persist=True):
        if self.closed:return False
        if mode not in MODES:self.selected.set(self.mode);return False
        if mode==self.mode:self.selected.set(mode);return True
        try:
            if mode=='New':
                topmost=self.root.attributes('-topmost')
                self.original_topmost=topmost
                if self.app is None:self.create_app()
                else:self.app.refresh()
                banner=getattr(self.root,'game_tools_scope_banner',None)
                self.original=[(widget,widget.pack_info()) for widget in self.root.pack_slaves() if widget not in (self.bar,self.host)]
                for widget,_ in self.original:
                    if widget is not banner:widget.pack_forget()
                self.host.pack(fill='both',expand=True);self._new_shortcuts()
                self.root.attributes('-topmost',bool(self.app.model.view.get('window_pins',{}).get('main',False)))
            else:
                self.app.stash();self.host.pack_forget();self._restore_shortcuts()
                self._restore_original()
                if self.original_topmost is not None:self.root.attributes('-topmost',self.original_topmost)
            self.mode=mode;self.selected.set(mode)
            if persist:self.preference.select(mode)
            self.status.set(mode+' interface · drafts retained · settings were not applied')
            return True
        except Exception as error:
            # A missing/corrupt optional view cannot take away the original app.
            if self.host:self.host.pack_forget()
            self._restore_shortcuts()
            self._restore_original()
            if self.original_topmost is not None:self.root.attributes('-topmost',self.original_topmost)
            self.mode='Existing';self.selected.set('Existing');self.status.set('Existing interface retained: '+str(error));return False
    def pages(self):
        return [(ident,str(self.notebook.tab(ident,'text'))) for ident in self.notebook.tabs()]
    def update_tools(self):
        self.menu.delete(0,'end')
        for ident,label in self.pages():self.menu.add_command(label=label,command=lambda tab=ident:self.open_tool(tab))
    def open_tool(self,tab):
        if tab not in self.notebook.tabs():self.status.set('That tool is no longer available.');return False
        if self.notebook.tab(tab,'state')=='disabled':self.status.set('That tool is currently disabled; its state was preserved.');return False
        if not self.show('Existing'):return False
        self.notebook.select(tab)
        self.status.set(self.notebook.tab(tab,'text')+' · existing tools and draft retained');return True
    def show_launcher(self):
        if not self.install_root or not self.install_root.is_dir():self.status.set('APP LAUNCHER is in the installed app folder.');return
        if os.name=='nt':os.startfile(self.install_root)
        else:
            import subprocess
            subprocess.Popen(['xdg-open',str(self.install_root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def can_close(self):
        ready=self.app is None or self.app.can_close()
        if not ready:self.status.set(self.app.status.get())
        return ready
    def close(self):
        if self.closed:return True
        if not self.can_close():return False
        if self.mode=='New':self.show('Existing',persist=False)
        self.closed=True
        if self._startup:self.root.after_cancel(self._startup);self._startup=None
        self._restore_shortcuts()
        if self.app:self.app.close()
        if self.host:self.host.destroy()
        self.bar.destroy();return True

def mount(notebook,controls,data_dir,status):
    root=notebook.winfo_toplevel();install=None
    if '--unified-install' in __import__('sys').argv:
        args=__import__('sys').argv;index=args.index('--unified-install')
        if index+1<len(args):install=Path(args[index+1])
    return InterfaceViews(root,notebook,controls,data_dir,status,install_root=install)
