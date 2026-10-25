"""Shared native Mod Controls page; all effects go through existing services."""
from __future__ import annotations
import json,os,subprocess,sys,webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox,simpledialog
from GameToolCompactUI import FlowToolbar,ScrollableFrame,window_bounds
from GameToolModControls import ModControls,VERSION,ROOT,PACKS,ini_template,validate_pack,atomic_json
from GameToolAutomationPanel import AutomationPanel
from game_mod_ops.safety import ModError,read_json,json_new

class ControlRequests(AutomationPanel):
    def __init__(self,parent,controls,instance,status):
        self.controls,self.instance=controls,instance
        super().__init__(parent,controls.requests(instance),status)
        for label in ('Share report summary','Share tool status'):
            button=self.buttons.pop(label);button.master.buttons.remove(button);button.destroy()
        self.write(controls.inspect(instance));self.refresh()
    def copy_context(self):
        self.safe(lambda:self._copy(self.controls.inspect(self.instance)))
    def _copy(self,value):
        self.write(value);self.clipboard_clear();self.clipboard_append(json.dumps(value,indent=2))
        self.set_state('Structured context copied. No external AI call was made.')
    def client_setup(self):
        setup=self.controls.client_setup_local()
        if not self.allow_client_requests.get():
            # Pin the retained source version for a read-only client. The
            # registered proposal-enabled connection keeps its stable entry.
            setup['mcpServers']['game-tools-mods']['args']=[str(ROOT/'scripts/GameToolAI.py'),'--data-dir',str(self.controls.data_dir),'--workspaces','stdio']
        return setup
    def show_capabilities(self):self.safe(lambda:self.write(self.controls.inspect(self.instance)['capabilities']))
    def save_context(self):
        path=filedialog.asksaveasfilename(parent=self,title='Save a new structured context',defaultextension='.json')
        if path:self.safe(lambda:json_new(Path(path),self.controls.inspect(self.instance)))

class ModControlsPanel(ttk.Frame):
    def __init__(self,parent,data_dir,status=None,service=None,initial_game=None):
        super().__init__(parent,padding=10)
        self.controls=service or ModControls(data_dir);self.shared_status=status
        self.state=tk.StringVar(self,value='Select a game and installation. Opening this page does not apply settings.')
        self.game=tk.StringVar(self);self.instance=tk.StringVar(self);self.profile=tk.StringVar(self)
        self.current=None;self.observation=None;self.variables={};self.drafts={};self.floating=[];self.workbenches=[];self.ai=None;self.closed=False
        self.view_path=self.controls.root/'view.json'
        if self.view_path.is_file():
            view=read_json(self.view_path,131072)
            if type(view.get('drafts')) is dict:self.drafts=view['drafts']
            if initial_game is None:initial_game=view.get('game_id')
        self.game_rows=self.controls.games()['games'];self.game_labels={r['name']+' ['+r['game_id']+']':r for r in self.game_rows}
        header=ttk.Frame(self);header.pack(fill='x')
        ttk.Label(header,text='Mod Controls',font=('Segoe UI',16,'bold')).pack(side='left')
        ttk.Label(header,text='  '+VERSION).pack(side='left')
        choose=ttk.Frame(self);choose.pack(fill='x',pady=8);choose.columnconfigure(1,weight=1)
        ttk.Label(choose,text='Game').grid(row=0,column=0,sticky='w',padx=(0,8))
        self.game_box=ttk.Combobox(choose,textvariable=self.game,values=list(self.game_labels));self.game_box.grid(row=0,column=1,sticky='ew')
        self.game_box.bind('<<ComboboxSelected>>',self.choose_game);self.game_box.bind('<Return>',self.choose_game)
        self.game_box.bind('<KeyRelease>',lambda _:self.game_box.configure(values=[x for x in self.game_labels if self.game.get().casefold() in x.casefold()]))
        ttk.Button(choose,text='Connect game folder…',command=lambda:self.safe(self.register)).grid(row=0,column=2,padx=6)
        ttk.Label(choose,text='Installation').grid(row=1,column=0,sticky='w',pady=5)
        self.instance_box=ttk.Combobox(choose,textvariable=self.instance,state='readonly');self.instance_box.grid(row=1,column=1,sticky='ew')
        self.instance_box.bind('<<ComboboxSelected>>',lambda _:self.safe(self.load_instance))
        ttk.Button(choose,text='Refresh applied state',command=lambda:self.safe(self.refresh)).grid(row=1,column=2,padx=6)
        ttk.Label(self,textvariable=self.state,wraplength=960).pack(fill='x',anchor='w',pady=(0,8))
        self.bind('<Configure>',lambda e:self._wrap_state(e),add='+')
        self.pages=ttk.Notebook(self);self.pages.pack(fill='both',expand=True)
        self.edit=ScrollableFrame(self.pages,min_width=320);self.pages.add(self.edit,text='Settings & profiles')
        self.inspector=ttk.Frame(self.pages);self.pages.add(self.inspector,text='Inspector')
        self.links=ScrollableFrame(self.pages,min_width=320);self.pages.add(self.links,text='Folders, tools & workflows')
        self.ai_host=ttk.Frame(self.pages);self.pages.add(self.ai_host,text='AI requests')
        tools=FlowToolbar(self.edit.body);tools.pack(fill='x')
        for label,action in [('Connect controls…',self.connect),('Import control pack…',self.import_pack),('Build pack template…',self.template)]:tools.add(label,lambda a=action:self.safe(a))
        self.form=ttk.Frame(self.edit.body);self.form.pack(fill='x',pady=8)
        bar=FlowToolbar(self.edit.body);bar.pack(fill='x')
        self.action_buttons={}
        for label,action in [('Preview changes',self.preview),('Apply reviewed changes',self.apply),('Floating settings',self.float_settings),('Reset draft to applied',self.reset_draft)]:self.action_buttons[label]=bar.add(label,lambda a=action:self.safe(a))
        profiles=ttk.LabelFrame(self.edit.body,text='Saved profiles',padding=6);profiles.pack(fill='x',pady=8)
        self.profile_box=ttk.Combobox(profiles,textvariable=self.profile,state='readonly');self.profile_box.pack(fill='x')
        bar=FlowToolbar(profiles);bar.pack(fill='x',pady=4)
        bar.add('Load into preview',lambda:self.safe(self.load_profile));bar.add('Save draft profile…',lambda:self.safe(self.save_profile))
        self.preview_text=tk.Text(self.edit.body,height=7,wrap='word');self.preview_text.pack(fill='both',expand=True)
        self.inspect_text=tk.Text(self.inspector,wrap='none');self.inspect_text.pack(fill='both',expand=True)
        sb=ttk.Scrollbar(self.inspector,orient='vertical',command=self.inspect_text.yview);sb.pack(side='right',fill='y');self.inspect_text.configure(yscrollcommand=sb.set)
        self.bind('<Destroy>',self._destroy,add='+')
        if self.game_rows:
            chosen=next((label for label,row in self.game_labels.items() if row['game_id']==initial_game),next(iter(self.game_labels)))
            self.game.set(chosen);self.choose_game()
    def set_state(self,text):
        self.state.set(text)
        if self.shared_status is not None:self.shared_status.set(text)
    def _wrap_state(self,event):
        if event.widget is self:
            for child in self.winfo_children():
                if isinstance(child,ttk.Label) and str(child.cget('textvariable'))==str(self.state):child.configure(wraplength=max(280,event.width-30))
    def safe(self,action):
        try:return action()
        except (ModError,ValueError,OSError,KeyError,RuntimeError) as error:
            self.set_state(str(error));messagebox.showerror('Mod Controls needs attention',str(error),parent=self)
    def _text(self,widget,value):
        widget.configure(state='normal');widget.delete('1.0','end');widget.insert('end',json.dumps(value,indent=2,ensure_ascii=False) if not isinstance(value,str) else value);widget.configure(state='disabled')
    def selected_game(self):
        if self.game.get() not in self.game_labels:raise ModError('SELECTION_REQUIRED','Choose a game from the searchable list.')
        return self.game_labels[self.game.get()]
    def _stash(self):
        if self.current and self.variables:
            self.drafts[self.current]={k:v.get() for k,v in self.variables.items()}
        self.view_path.parent.mkdir(parents=True,exist_ok=True)
        atomic_json(self.view_path,{'schema_version':1,'game_id':self.game_labels.get(self.game.get(),{}).get('game_id'),'drafts':self.drafts})
    def choose_game(self,_event=None):
        def go():
            if not self.can_change():return
            self._stash();row=self.selected_game();instances=[i['instance_id'] for g in self.controls.games()['games'] if g['game_id']==row['game_id'] for i in g['instances']]
            self.instance_box.configure(values=instances);self.instance.set(instances[0] if instances else '');self.load_instance()
        self.safe(go)
    def can_change(self):
        if self.ai and self.ai.busy:self.instance.set(self.current);self.set_state('Wait for the current approved action before changing game.');return False
        return True
    def register(self):
        row=self.selected_game();path=filedialog.askdirectory(parent=self,title='Choose the installed '+row['name']+' game folder')
        if not path:return
        result=self.controls.register_local(row['game_id'],path);self.choose_game();self.instance.set(result['instance']['instance_id']);self.load_instance()
    def load_instance(self):
        if not self.can_change():return
        self._stash();self.current=self.instance.get() or None;self.observation=None
        for w in self.floating:
            if w.winfo_exists():w.destroy()
        self.floating=[]
        if self.ai:self.ai.close();self.ai.destroy();self.ai=None
        if not self.current:
            self.render({});self._text(self.inspect_text,{'status':'Connect an installed game folder to inspect it.'});self.build_links();self.set_state('This game has no connected installation.');return
        self.observation=self.controls.inspect(self.current);self.render(self.drafts.get(self.current,{}));self._text(self.inspect_text,self.observation);self.build_links()
        if self.observation['capabilities'].get('profiles'):
            self.ai=ControlRequests(self.ai_host,self.controls,self.current,self.shared_status);self.ai.pack(fill='both',expand=True)
            self.set_state('Applied state loaded. Drafts, profiles and previews do not change the game.')
        else:self.set_state('Inventory connected. Import a reviewed control pack to enable settings; support varies by game.')
    def refresh(self):
        self._stash();self.load_instance()
    def render(self,draft):
        for w in self.form.winfo_children():w.destroy()
        self.variables={};observation=self.observation or {};schema=observation.get('schema',[])
        for f in schema:
            value=draft.get(f['id'],observation['values'][f['id']]);self.variables[f['id']]=tk.BooleanVar(self,value=value) if f['type']=='bool' else tk.StringVar(self,value=str(value))
        self.fields(self.form)
        if not schema:ttk.Label(self.form,text='No reviewed settings are connected for this installation.',wraplength=680).pack(anchor='w')
        enabled='normal' if schema else 'disabled'
        for b in self.action_buttons.values():b.configure(state=enabled)
        if schema and not observation['capabilities']['apply']:self.action_buttons['Apply reviewed changes'].configure(state='disabled')
        self.profile_rows={r['label']+' ['+r['profile_id'][:8]+']':r for r in self.controls.profile_rows(self.current)} if schema else {}
        self.profile_box.configure(values=list(self.profile_rows));self.profile.set('')
        self._text(self.preview_text,'Review a preview before applying. Floating editors share this same draft.')
    def fields(self,parent):
        for i,f in enumerate((self.observation or {}).get('schema',[])):
            var=self.variables[f['id']];ttk.Label(parent,text=f['label']).grid(row=i,column=0,sticky='w',padx=(0,12),pady=4)
            if f['type']=='bool':widget=ttk.Checkbutton(parent,text='Enabled',variable=var)
            elif f['type']=='enum':widget=ttk.Combobox(parent,textvariable=var,values=f['choices'],state='readonly')
            else:widget=ttk.Spinbox(parent,textvariable=var,from_=f['min'],to=f['max'],increment=1 if f['type']=='int' else .1)
            widget.grid(row=i,column=1,sticky='ew',pady=4)
        parent.columnconfigure(1,weight=1)
    def desired(self):
        if not self.observation or not self.variables:raise ModError('CONTROL_CONNECTION_REQUIRED','Connect reviewed controls first.')
        result={}
        for f in self.observation['schema']:
            v=self.variables[f['id']].get()
            if f['type']=='int':v=int(v)
            elif f['type']=='number':v=float(v)
            result[f['id']]=v
        return result
    def preview(self):
        p=self.controls.preview(self.current,self.desired(),self.observation['revision']);self._text(self.preview_text,p);self.set_state(str(len(p['changes']))+' proposed changes. Applied files have not changed.');return p
    def apply(self):
        p=self.preview()
        if not p['changes']:return
        detail='\n'.join(x['id']+': '+str(x['before'])+' → '+str(x['after']) for x in p['changes'])
        if not messagebox.askyesno('Apply these exact settings?',detail+'\n\nExisting files will be backed up. Close the game and mod manager first.',parent=self):return
        result=self.controls.apply_local(self.current,self.desired(),p['revision']);self.drafts.pop(self.current,None);self.variables={};self.load_instance();self._text(self.preview_text,result);self.set_state('Settings applied and read back. Runtime/gameplay validation remains separate.')
    def reset_draft(self):
        for key,var in self.variables.items():var.set(self.observation['values'][key])
        self.drafts.pop(self.current,None);self.preview()
    def float_settings(self):
        if not self.variables:return
        win=tk.Toplevel(self);win.title('Mod Controls — '+self.selected_game()['name']);win.geometry('540x600');win.minsize(360,280)
        top=tk.BooleanVar(win,value=False);ttk.Checkbutton(win,text='Keep above other windows',variable=top,command=lambda:win.attributes('-topmost',top.get())).pack(anchor='w',padx=8,pady=4)
        body=ScrollableFrame(win,min_width=300);body.pack(fill='both',expand=True);form=ttk.Frame(body.body,padding=8);form.pack(fill='x');self.fields(form)
        ttk.Label(body.body,text='Shared draft • Use Preview and Apply in the main window.',wraplength=440).pack(anchor='w',padx=8,pady=8);self.floating.append(win)
    def load_profile(self):
        row=self.profile_rows.get(self.profile.get())
        if not row:return
        for key,value in self.controls.profile(self.current,row['profile_id'])['values'].items():self.variables[key].set(value)
        self.preview()
    def save_profile(self):
        name=simpledialog.askstring('Save profile','Profile name (letters, numbers, hyphens):',parent=self)
        if name:self.controls.save_profile_local(self.current,name,self.desired(),self.observation['revision']);self.refresh();self.set_state('Profile saved. Game files were not changed.')
    def connect(self,pack=None):
        if not self.current:raise ModError('SELECTION_REQUIRED','Connect a game folder first.')
        if pack is None:
            path=PACKS/(self.selected_game()['game_id']+'.json')
            if not path.is_file():return self.import_pack()
            pack=read_json(path,131072)
        workspace=None
        if pack['adapter']=='shadow-reviewed':
            workspace=filedialog.askdirectory(parent=self,title='Choose the existing reviewed Shadow of War controller workspace')
            if not workspace:return
        writes=messagebox.askyesno('Settings file ownership','Allow this controller to write only the declared settings?\nChoose No for a read-only connection. Keep external managers closed during writes.',parent=self)
        self.controls.connect_local(self.current,workspace=workspace,pack=pack,writes_enabled=writes);self.load_instance()
    def import_pack(self):
        path=filedialog.askopenfilename(parent=self,title='Import a data-only reviewed control pack',filetypes=[('Control pack','*.json')])
        if path:self.connect(validate_pack(read_json(Path(path),131072)))
    def template(self):
        pack=ini_template(self.selected_game()['game_id']);path=filedialog.asksaveasfilename(parent=self,title='Save a new INI control-pack template',defaultextension='.json')
        if path:json_new(Path(path),pack);self.set_state('Data-only template saved. AI can validate it; review the mod documentation and existing keys before importing.')
    def open_path(self,path):
        if not path.exists():raise ModError('LOCATION_UNAVAILABLE','This folder does not exist yet.')
        if os.name=='nt':os.startfile(path)
        else:subprocess.Popen(['xdg-open',str(path)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def build_links(self):
        parent=self.links.body
        for w in parent.winfo_children():w.destroy()
        bar=FlowToolbar(parent);bar.pack(fill='x')
        bar.add('Open game workflow',lambda:self.safe(self.open_workbench));bar.add('Find APP LAUNCHER',lambda:self.safe(self.find_launcher))
        if self.current:
            folders=ttk.LabelFrame(parent,text='Local folders',padding=6);folders.pack(fill='x',pady=6)
            for label,path in self.controls.locations_local(self.current).items():ttk.Button(folders,text=label,command=lambda p=path:self.safe(lambda:self.open_path(p))).pack(anchor='w',pady=2)
            if (self.observation or {}).get('capabilities',{}).get('manager_handoff'):
                bar=FlowToolbar(parent);bar.pack(fill='x',pady=6);bar.add('Prepare manager files',lambda:self.safe(self.prepare_manager));bar.add('Open prepared files',lambda:self.safe(lambda:self.open_path(self.controls.export_path_local(self.current))))
        tools=ttk.LabelFrame(parent,text='Existing programs',padding=6);tools.pack(fill='x',pady=6)
        for row in self.controls.tools_local():
            line=ttk.Frame(tools);line.pack(fill='x',pady=3);ttk.Label(line,text=row['name']+(' • found' if row['installed'] else ' • not connected')).pack(side='left')
            ttk.Button(line,text='Locate…',command=lambda key=row['tool_id']:self.safe(lambda:self.locate_tool(key))).pack(side='right')
            ttk.Button(line,text='Open',state='normal' if row['installed'] else 'disabled',command=lambda p=row['path']:self.safe(lambda:self.open_path(p))).pack(side='right',padx=6)
        source=ttk.LabelFrame(parent,text='Mod and adapter sources',padding=6);source.pack(fill='x',pady=6)
        urls=(self.observation or {}).get('sources',[])
        for url in urls:ttk.Button(source,text=url,command=lambda u=url:webbrowser.open(u)).pack(anchor='w',pady=2)
        if not urls:ttk.Label(source,text='Source links appear when a reviewed control pack is connected.').pack(anchor='w')
        ttk.Label(parent,text='Manager handoffs prepare files for review. Native deployment and manager profiles remain owned by their programs.',wraplength=880).pack(anchor='w',pady=6)
    def locate_tool(self,key):
        path=filedialog.askopenfilename(parent=self,title='Choose the already installed application',filetypes=[('Windows app','*.exe')])
        if path:self.controls.set_tool_local(key,Path(path));self.build_links()
    def prepare_manager(self):
        result=self.controls.prepare_manager_local(self.current,self.observation['revision']);self._text(self.preview_text,result);self.set_state('Manager files prepared. Open prepared files to review the handoff.')
    def find_launcher(self):
        root=ROOT.parent.parent if ROOT.parent.name=='versions' else ROOT
        self.open_path(root)
        self.set_state('Launcher folder opened. Use Game Mod Controls APP LAUNCHER; Open does not install or update.')
    def open_workbench(self):
        from GameToolWorkbench import Workbench
        win=tk.Toplevel(self);view=Workbench(win,self.controls.data_dir);view.load_game(self.selected_game()['game_id']);self.workbenches.append(view)
    def can_close(self):
        if self.ai and not self.ai.can_close():return False
        if any(v.model.runner.active() or v.keybind_panel.working for v in self.workbenches if not v.closed):self.set_state('A game workflow is still active. Close it from its own window.');return False
        return True
    def close(self):
        if self.closed:return
        self._stash();self.closed=True
        for v in self.workbenches:
            if not v.closed:v.close()
        if self.ai:self.ai.close()
        for w in self.floating:
            if w.winfo_exists():w.destroy()
        self.edit.close();self.links.close()
    def _destroy(self,event):
        if event.widget is self:self.close()

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--data-dir',type=Path,required=True);p.add_argument('--game-id');a=p.parse_args(argv)
    root=tk.Tk();root.title('Game Mod Controls '+VERSION)
    w,h,mw,mh=window_bounds(root.winfo_screenwidth(),root.winfo_screenheight());root.geometry(f'{w}x{h}');root.minsize(mw,mh)
    panel=ModControlsPanel(root,a.data_dir,initial_game=a.game_id);panel.pack(fill='both',expand=True)
    def close():
        if panel.can_close():panel.close();root.destroy()
    root.protocol('WM_DELETE_WINDOW',close);root.mainloop();return 0

if __name__=='__main__':raise SystemExit(main())
