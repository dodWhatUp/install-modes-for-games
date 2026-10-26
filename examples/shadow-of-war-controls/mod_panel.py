"""Native, nonresident file controls. --demo is an isolated fixture only."""
from __future__ import annotations
import argparse, copy, json, os, queue, subprocess, sys, threading, traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from control_service import ControlService, DemoService, DEFAULTS, KEYS, MODS, VERSION, atomic, json_bytes
from mod_resources import EDIT_FIELDS
from mod_tools_ui import ModTools
from settings_locator import SettingsLocationError
from settings_ui import SettingsLocationDialog,startup_service

LABELS={'profile':'Graphics profile','graphics':'Graphics enabled','gameplay':'Gameplay loader',
        'multi-skills':'Multi Equip Skills','elven-speed':'Elven Speed','fov':'FOV Extender',
        'dlaa':'Luma DLAA','nr':'DLSS 5','duration':'Duration multiplier','regen':'Focus regeneration',
        'fov_min':'Minimum FOV','fov_max':'Maximum FOV','modifier':'Multi-equip key',
        'toggle':'Toggle instead of hold','sound':'Equip sound','width':'Render width','height':'Render height'}
PROFILES={'RenoDX — recommended':'previous','Luma — experimental':'luma'}

class Panel(ttk.Frame):
    def __init__(self,root,service,demo=False):
        super().__init__(root,padding=18);self.pack(fill='both',expand=True)
        self.root=root;self.service=service;self.demo=demo;self.snapshot=None;self.busy=False
        self.events=queue.Queue();self.widgets={};self.loading=True;self.vars={};self._disposed=False;self._drain_job=None
        self.location_blocked=False;self._settings_dialog=None
        root.title('Shadow of War — Mod Controls '+VERSION+(' [isolated demo]' if demo else ''))
        root.geometry('960x580');root.minsize(850,520)
        style=ttk.Style(root);style.theme_use('clam')
        style.configure('.',font=('Segoe UI',10),background='#f4f6fa',foreground='#162338')
        style.configure('TFrame',background='#f4f6fa');style.configure('TLabel',background='#f4f6fa')
        style.configure('Title.TLabel',font=('Segoe UI',19,'bold'))
        style.configure('Muted.TLabel',foreground='#526078')
        style.configure('TLabelframe',padding=12);style.configure('TLabelframe.Label',font=('Segoe UI',11,'bold'))
        style.configure('TButton',padding=(10,7));style.configure('Accent.TButton',background='#2165b7',foreground='white')
        style.map('Accent.TButton',background=[('active','#164f94'),('disabled','#c5ccd6')])
        for key,value in DEFAULTS.items():
            cls=tk.BooleanVar if type(value) is bool else tk.StringVar
            self.vars[key]=cls(root,value=value)
            self.vars[key].trace_add('write',self.changed)
        self.profile_name=tk.StringVar(root,value='Current setup')
        self.profile_label=tk.StringVar(root,value=next(iter(PROFILES)))
        self.advanced=tk.BooleanVar(root,value=False);self.precise=tk.BooleanVar(root,value=False)
        view=service.base/'control-panel-view.json'
        if view.exists():
            try:
                stored=json.loads(view.read_text());self.advanced.set(bool(stored.get('experimental',False)));self.precise.set(bool(stored.get('precise',False)))
            except (ValueError,OSError):pass
        initial_height=810 if self.precise.get() else (670 if self.advanced.get() else 580)
        root.geometry(f'{min(960,root.winfo_screenwidth()-40)}x{min(initial_height,root.winfo_screenheight()-80)}')
        self.view_path=view
        self.build();self.mod_tools=ModTools(self);self.loading=False
        root.protocol('WM_DELETE_WINDOW',self.close)
        root.bind('<Control-s>',lambda e:self.save_profile())
        root.bind('<F5>',lambda e:self.refresh())
        self.bind('<Destroy>',self.disposed,add='+')
        self._drain_job=self.root.after(100,self.drain);self.refresh()

    def build(self):
        head=ttk.Frame(self);head.pack(fill='x')
        title_label=ttk.Label(head,text='Shadow of War',style='Title.TLabel');title_label.pack(side='left')
        self.files_menu=ttk.Menubutton(head,text='Files & tools ▾');self.files_menu.pack(side='right')
        folders_button=ttk.Button(head,text='Mods & folders...',command=lambda:self.mod_tools.show());folders_button.pack(side='right',padx=7)
        menu=tk.Menu(self.files_menu,tearoff=False);self.files_menu['menu']=menu
        for label,action in [('Show APP LAUNCHER',lambda:self.open_path(Path(__file__).resolve().parent)),
             ('Find / repair settings location...',self.setup_settings),
             ('Saved profiles',lambda:self.open_path(self.service.base/'saved-profiles')),
             ('Settings & recovery folder',lambda:self.open_path(self.service.base)),
             ('Open RHI graphics manager',self.open_rhi),('Steam texture-pack controls',self.open_textures),
             ('Read setup guide',lambda:self.open_path(self.service.base/'LUMA-START-HERE.txt')),
             ('Resource use & manager transfer',self.about)]:menu.add_command(label=label,command=action)
        self.applied=tk.StringVar(value='Reading installed files…')
        ttk.Label(self,textvariable=self.applied,style='Muted.TLabel',wraplength=880).pack(anchor='w',pady=(3,9))
        bar=ttk.Frame(self);bar.pack(fill='x',pady=(0,12))
        ttk.Label(bar,text='Saved setup').pack(side='left',padx=(0,8))
        self.profile_combo=ttk.Combobox(bar,textvariable=self.profile_name,width=26)
        self.profile_combo.pack(side='left',fill='x',expand=True)
        ttk.Button(bar,text='Load to preview',command=self.load_profile).pack(side='left',padx=6)
        ttk.Button(bar,text='Save profile file',command=self.save_profile).pack(side='left')
        ttk.Label(self,text='Changes stay in preview until you choose Apply. Saved files keep working after this window closes.',
            style='Muted.TLabel',wraplength=880).pack(anchor='w',pady=(0,9))
        scrollhost=ttk.Frame(self);scrollhost.pack(fill='both',expand=True)
        self.canvas=tk.Canvas(scrollhost,highlightthickness=0,background='#f4f6fa')
        scroll=ttk.Scrollbar(scrollhost,orient='vertical',command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        self.body=ttk.Frame(self.canvas);item=self.canvas.create_window((0,0),window=self.body,anchor='nw')
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(item,width=e.width))
        self.body.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<MouseWheel>',lambda e:self.canvas.yview_scroll(-int(e.delta/120),'units'))
        columns=ttk.Frame(self.body);columns.pack(fill='x');columns.columnconfigure((0,1),weight=1,uniform='main')
        graphics=ttk.LabelFrame(columns,text='Graphics');graphics.grid(row=0,column=0,sticky='nsew',padx=(0,7))
        self.check(graphics,'graphics','Enable graphics mods').pack(anchor='w')
        combo=ttk.Combobox(graphics,textvariable=self.profile_label,values=list(PROFILES),state='readonly',width=29)
        combo.pack(fill='x',pady=7);combo.bind('<<ComboboxSelected>>',self.change_graphics)
        ttk.Label(graphics,text='Official UHD textures: installed\nTexture on/off is owned by Steam DLC.',style='Muted.TLabel').pack(anchor='w',pady=(0,5))
        ttk.Checkbutton(graphics,text='Show experimental controls',variable=self.advanced,command=self.toggle_view).pack(anchor='w')
        self.experimental=ttk.Frame(graphics)
        self.check(self.experimental,'dlaa','DLAA at 100% render resolution').pack(anchor='w',pady=(5,0))
        self.check(self.experimental,'nr','DLSS 5 neural rendering').pack(anchor='w')
        ttk.Label(self.experimental,text='Luma faulted during shutdown. Keep the trial off pending diagnosis. True DLSS SR is unavailable.',
            foreground='#8a4300',wraplength=325).pack(anchor='w',pady=(5,0))
        gameplay=ttk.LabelFrame(columns,text='Gameplay');gameplay.grid(row=0,column=1,sticky='nsew',padx=(7,0))
        self.check(gameplay,'gameplay','Enable gameplay loader').pack(anchor='w',pady=(0,5))
        for key,(name,_) in MODS.items():
            row=ttk.Frame(gameplay);row.pack(fill='x',pady=2)
            self.check(row,key,name).pack(side='left')
            ttk.Button(row,text='Settings...',command=lambda key=key:self.mod_tools.floating(key)).pack(side='right')
        ttk.Label(gameplay,text='With the loader off, selected plugins stay configured but do not run.',style='Muted.TLabel',wraplength=325).pack(anchor='w',pady=(7,0))
        viewbar=ttk.Frame(self.body);viewbar.pack(fill='x',pady=(10,4))
        ttk.Checkbutton(viewbar,text='Show precise settings',variable=self.precise,command=self.toggle_view).pack(side='left')
        ttk.Button(viewbar,text='Recommended preview',command=self.recommended).pack(side='right')
        ttk.Button(viewbar,text='All mods off — preview',command=self.all_off).pack(side='right',padx=6)
        self.precise_frame=ttk.LabelFrame(self.body,text='Exact saved settings')
        self.precise_frame.columnconfigure((1,3),weight=1)
        fields=[('duration','Ability duration ×',0,10,0.05),('regen','Focus regeneration ×',-1,1,0.05),
                ('fov_min','Minimum FOV',40,70,1),('fov_max','Maximum FOV',40,70,1),
                ('width','Render width (pixels)',640,8192,1),('height','Render height (pixels)',640,8192,1)]
        for i,(key,label,lo,hi,step) in enumerate(fields):
            row=i//2;col=(i%2)*2
            ttk.Label(self.precise_frame,text=label).grid(row=row,column=col,sticky='w',padx=(0,7),pady=4)
            field=ttk.Spinbox(self.precise_frame,from_=lo,to=hi,increment=step,textvariable=self.vars[key],width=11)
            field.grid(row=row,column=col+1,sticky='ew',padx=(0,14),pady=4)
        ttk.Label(self.precise_frame,text='Multi-equip modifier').grid(row=3,column=0,sticky='w',pady=4)
        self.key_label=tk.StringVar(value='Left Ctrl')
        keybox=ttk.Combobox(self.precise_frame,textvariable=self.key_label,values=list(KEYS),state='readonly',width=14)
        keybox.grid(row=3,column=1,sticky='ew',padx=(0,14));keybox.bind('<<ComboboxSelected>>',lambda e:self.vars['modifier'].set(KEYS[self.key_label.get()]))
        self.check(self.precise_frame,'toggle','Press to toggle (otherwise hold)').grid(row=3,column=2,columnspan=2,sticky='w')
        self.check(self.precise_frame,'sound','Play multi-equip sound').grid(row=4,column=0,columnspan=2,sticky='w',pady=(4,0))
        ttk.Label(self.precise_frame,text='Menus: Delete = graphics · F12 = gameplay',style='Muted.TLabel').grid(row=4,column=2,columnspan=2,sticky='w')
        self.bottom=ttk.Frame(self);self.bottom.pack(side='bottom',fill='x',pady=(12,0))
        self.notice=tk.StringVar(value='')
        ttk.Label(self.bottom,textvariable=self.notice,wraplength=870,foreground='#8a4300').pack(anchor='w',pady=(0,7))
        actions=ttk.Frame(self.bottom);actions.pack(fill='x')
        ttk.Button(actions,text='Refresh files',command=self.refresh).pack(side='left')
        ttk.Button(actions,text='Manager transfer...',command=self.export).pack(side='left',padx=6)
        ttk.Button(actions,text='Review changes',command=self.preview).pack(side='right',padx=(6,0))
        self.apply_button=ttk.Button(actions,text='Apply & keep files',style='Accent.TButton',command=self.apply)
        self.apply_button.pack(side='right')
        self.dirty=tk.StringVar(value='')
        ttk.Label(self.bottom,textvariable=self.dirty,style='Muted.TLabel').pack(anchor='w',pady=(7,0))
        self.toggle_view(save=False)
        try:from GameToolAppMenus import AppMenus
        except ModuleNotFoundError as error:
            if error.name!='GameToolAppMenus':raise
            sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
            from GameToolAppMenus import AppMenus
        compact_tools=tk.Menu(self.root,tearoff=False)
        compact_tools.add_command(label='Mods & folders…',command=lambda:self.mod_tools.show())
        compact_tools.add_cascade(label='Locations & help',menu=menu)
        self.chrome=AppMenus(head,root=self.root,preference=self.service.base/'ui-chrome.json',title=title_label,
                             original_controls=(self.files_menu,folders_button),tools_menu=compact_tools,status=self.notice.set)
        self.chrome.checkbutton('Show experimental controls',self.advanced,self.toggle_view)
        self.chrome.checkbutton('Show precise settings',self.precise,self.toggle_view)

    def check(self,parent,key,text):
        cb=ttk.Checkbutton(parent,text=text,variable=self.vars[key],command=lambda:self.dependency(key));self.widgets[key]=cb;return cb
    def dependency(self,key):
        if key=='nr' and self.vars['nr'].get():self.vars['dlaa'].set(True)
        if key=='dlaa' and not self.vars['dlaa'].get():self.vars['nr'].set(False)
        self.changed()
    def change_graphics(self,e=None):
        profile=PROFILES[self.profile_label.get()];self.vars['profile'].set(profile)
        if profile=='previous':self.vars['dlaa'].set(False);self.vars['nr'].set(False)
        else:self.advanced.set(True)
        self.toggle_view();self.changed()
    def toggle_view(self,save=True):
        if self.advanced.get():self.experimental.pack(fill='x',pady=(0,3))
        else:self.experimental.pack_forget()
        if self.precise.get():self.precise_frame.pack(fill='x',pady=(4,0))
        else:self.precise_frame.pack_forget()
        if save:
            height=810 if self.precise.get() else (670 if self.advanced.get() else 580)
            self.root.geometry(f'{max(850,self.root.winfo_width())}x{min(height,self.root.winfo_screenheight()-70)}')
            try:atomic(self.view_path,json_bytes({'experimental':self.advanced.get(),'precise':self.precise.get()}))
            except OSError as e:self.notice.set(str(e))
    def values(self):
        return {k:(v.get() if type(DEFAULTS[k]) is bool else (int(v.get()) if k in ('width','height') and v.get().isdigit() else v.get())) for k,v in self.vars.items()}
    def set_values(self,v):
        self.loading=True
        for k,val in v.items():self.vars[k].set(val)
        self.profile_label.set(next(n for n,p in PROFILES.items() if p==v['profile']))
        self.key_label.set(next((n for n,p in KEYS.items() if p==v['modifier']),'Left Ctrl'))
        if v['profile']=='luma':self.advanced.set(True)
        self.loading=False;self.toggle_view(save=False);self.changed()
    def changed(self,*_):
        if self.loading or self.snapshot is None:return
        try:
            changes=self.service.preview(self.values(),self.snapshot)
            self.dirty.set(f'{len(changes)} pending change(s). Apply writes native INIs + last-applied-profile.json.' if changes else 'Applied files match this preview. No resident manager is needed during play.')
            self.apply_button.configure(state='normal' if changes and not self.busy and not self.location_blocked else 'disabled')
        except Exception as e:self.dirty.set(str(e));self.apply_button.configure(state='disabled')
        for k in ('dlaa','nr'):self.widgets[k].configure(state='normal' if self.vars['profile'].get()=='luma' else 'disabled')
    def run(self,fn,done):
        if self.busy:return
        self.busy=True;self.apply_button.configure(state='disabled');self.notice.set('Working…')
        def worker():
            try:self.events.put((done,fn(),None))
            except Exception as e:self.events.put((done,None,e))
        threading.Thread(target=worker,daemon=True).start()
    def drain(self):
        if self._disposed:return
        try:
            while True:
                done,result,error=self.events.get_nowait();self.busy=False
                if error:
                    self.notice.set(str(error))
                    if isinstance(error,SettingsLocationError):self.location_blocked=True;self.setup_settings(error.report)
                    else:messagebox.showerror('Action needs attention',str(error),parent=self.root)
                else:self.notice.set('');done(result)
                self.changed()
                for editor in self.mod_tools.editors.values():
                    if editor.winfo_exists():editor.update_status()
        except queue.Empty:pass
        if not self._disposed and self.winfo_exists():self._drain_job=self.root.after(100,self.drain)
    def disposed(self,event):
        if event.widget is self:
            self._disposed=True
            if self._drain_job:
                try:self.root.after_cancel(self._drain_job)
                except tk.TclError:pass
    def refresh(self):
        if self.busy:return
        def done(data):
            self.location_blocked=False;self.snapshot=data;self.set_values(data['values'])
            self.show_applied(data)
            self.notice.set('Close the game, Steam and RHI before Apply. Saving/exporting files is available now.' if data['blocked'] else 'Game-file switching is available. Every Apply keeps recovery.')
            self.profile_combo.configure(values=self.service.profile_names())
        self.run(self.service.read,done)
    def setup_settings(self,report=None):
        if self._settings_dialog is not None and self._settings_dialog.winfo_exists():
            self._settings_dialog.lift();return
        roots=[self.service.base/'demo-local-appdata'] if self.demo else None
        def selected(path):
            old=copy.deepcopy(self.snapshot);draft=self.values()
            def done(data):
                self.location_blocked=False;self.snapshot=data;merged=copy.deepcopy(data['values'])
                if old:
                    for field in DEFAULTS:
                        if draft[field]!=old['values'][field]:merged[field]=draft[field]
                self.set_values(merged);self.show_applied(data)
                self.notice.set('Settings location found and saved. Pending preview edits are preserved.')
            self.run(self.service.read,done)
        self._settings_dialog=SettingsLocationDialog(self.root,self.service.base,report,on_selected=selected,roots=roots,allow_external=not self.demo)
    def show_applied(self,data):
        v=data['values'];active=[MODS[k][0] for k in MODS if v['gameplay'] and v[k]]
        graphics=('RenoDX' if v['profile']=='previous' else 'Luma trial') if v['graphics'] else 'Graphics off'
        self.applied.set('Applied: '+graphics+' · '+(', '.join(active) if active else 'Gameplay off'))
    def preview(self):
        if not self.snapshot:return
        try:changes=self.service.preview(self.values(),self.snapshot)
        except Exception as e:return messagebox.showerror('Check values',str(e),parent=self.root)
        self.text_window('Review pending file changes','\n'.join(changes) if changes else 'No changes. Applied settings already match this preview.')
    def apply(self):
        if not self.snapshot or self.busy or self.location_blocked:return
        desired=self.values();snapshot=copy.deepcopy(self.snapshot)
        def done(result):self.notice.set(result['message']);self.refresh()
        self.run(lambda:self.service.apply(desired,snapshot),done)
    def apply_mod(self,key,callback=None):
        if not self.snapshot or self.busy or self.location_blocked:return
        snapshot=copy.deepcopy(self.snapshot);draft=self.values();fields=EDIT_FIELDS[key]
        desired=copy.deepcopy(snapshot['values'])
        for field in fields:desired[field]=draft[field]
        def job():return self.service.apply(desired,snapshot),self.service.read()
        def done(result):
            applied,data=result;self.snapshot=data;self.show_applied(data);merged=copy.deepcopy(data['values'])
            for field in DEFAULTS:
                if field not in fields and draft[field]!=snapshot['values'][field]:merged[field]=draft[field]
            self.set_values(merged)
            self.notice.set('Applied this mod. Other preview edits remain pending. '+applied['message'])
            if callback:callback()
        self.run(job,done)
    def save_profile(self):
        if self.busy or not self.snapshot:return
        try:
            p=self.service.save_profile(self.profile_name.get(),self.values())
            self.profile_combo.configure(values=self.service.profile_names());self.notice.set('Saved profile file: '+str(p))
        except Exception as e:messagebox.showerror('Profile not saved',str(e),parent=self.root)
    def load_profile(self):
        if self.busy:return
        try:self.set_values(self.service.load_profile(self.profile_name.get()));self.notice.set('Profile loaded to preview. Apply is still required to change game files.')
        except Exception as e:messagebox.showerror('Profile not loaded',str(e),parent=self.root)
    def recommended(self):
        v=copy.deepcopy(DEFAULTS)
        if self.snapshot:
            for k in ('width','height'):v[k]=self.snapshot['values'][k]
        self.set_values(v)
    def all_off(self):
        v=self.values();v['graphics']=False;v['gameplay']=False;self.set_values(v)
    def export(self):
        self.mod_tools.show('manager')
    def open_path(self,p):
        if self.demo:return self.notice.set('Demo: external file/app opening is disabled.')
        try:
            p=Path(p)
            if not p.exists():raise FileNotFoundError('This location does not exist yet: '+str(p))
            os.startfile(p)
        except Exception as e:messagebox.showerror('Cannot open',str(e),parent=self.root)
    def open_rhi(self):
        if not self.demo:subprocess.Popen([r'C:\Program Files\RHI\RHI.exe'])
    def open_textures(self):
        if not self.demo:subprocess.Popen([r'C:\Program Files (x86)\Steam\steam.exe','steam://gameproperties/356190/dlc'])
    def about(self):
        self.text_window('Manager resources & Vortex transfer',
            'This window writes files and can be closed before play. It is not injected into the game and has no background service. Installed graphics/gameplay mods have their own runtime cost.\n\nVortex has a Shadow of War extension and can deploy original archives. Our export prepares those archives and current settings, but does not transfer ownership or install another loader. Keep one owner per file and one DLL loader. Graphics remain under RHI/reviewed profiles.\n\nPersistent files: native mod INIs, saved-profiles/*.json, last-applied-profile.json and dated recovery folders. Save profile does not apply it.\n\nSources:\nhttps://www.nexusmods.com/site/mods/375\nhttps://github.com/Nexus-Mods/Vortex/blob/master/docs/mod-management/EXTERNAL-CHANGES.md')
    def text_window(self,title,text):
        win=tk.Toplevel(self.root);win.title(title);win.geometry('730x360');win.transient(self.root)
        box=tk.Text(win,wrap='word',padx=14,pady=14,font=('Segoe UI',10));box.pack(fill='both',expand=True);box.insert('1.0',text);box.configure(state='disabled')
        ttk.Button(win,text='Close',command=win.destroy).pack(pady=8)
    def close(self):
        if self.busy:return messagebox.showinfo('Working','Wait for the current file operation to finish.',parent=self.root)
        if self.snapshot:
            try:pending=bool(self.service.preview(self.values(),self.snapshot))
            except Exception:pending=True
            if pending and not messagebox.askyesno('Close preview?','Close without applying pending changes? Saved profile files will remain.',parent=self.root):return
        self.root.destroy()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--workspace',type=Path,default=Path(__file__).parent)
    parser.add_argument('--demo',action='store_true');args=parser.parse_args()
    try:from GameToolWindowsApp import Session
    except ModuleNotFoundError as error:
        if error.name!='GameToolWindowsApp':raise
        sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
        from GameToolWindowsApp import Session
    session=Session('shadow',args.workspace)
    if not session.primary:return 0
    root=tk.Tk()
    session.attach(root)
    try:
        service=startup_service(root,args.workspace,DemoService if args.demo else ControlService)
        if service is None:root.destroy();return 0
    except Exception as e:root.withdraw();messagebox.showerror('Cannot open mod controls',str(e),parent=root);root.destroy();return 1
    Panel(root,service,args.demo);root.mainloop();return 0
if __name__=='__main__':raise SystemExit(main())
