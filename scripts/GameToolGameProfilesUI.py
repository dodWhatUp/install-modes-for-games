"""A simple game runtime profile page in the existing Unified application."""
from __future__ import annotations
import json, os, queue, threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import GameToolGameProfiles as api
from GameToolCompactUI import Selector, FlowToolbar, ScrollableFrame, TableLayout

VERSION = "0.2.2"

class ProfilesPanel:
    def __init__(self,parent,directory,unified,overlays,status=None,autostart=True):
        self.parent=parent;self.service=api.Profiles(directory);self.unified=unified;self.overlay=overlays
        self.status=status.set if hasattr(status,'set')else status or (lambda text:None)
        self.closed=False;self.timer=None;self.attempted_auto=None;self.last_auto_game=None
        self.native_results=queue.Queue();self.native_busy=False;self.extra_games={}
        self.native_feedback=tk.StringVar()
        self.scroll=ScrollableFrame(parent,min_width=0);self.scroll.pack(fill='both',expand=True);body=self.scroll.body
        self.summary=tk.StringVar(value='Choose a game and save its working setup.')
        self.restore=tk.BooleanVar();self.automatic=tk.BooleanVar();self.windows=tk.BooleanVar()
        self.content_header=ttk.Frame(body,padding=12,borderwidth=1,relief='solid')
        self.content_header.pack(fill='x',pady=(0,12))
        self.heading=ttk.Label(self.content_header,text='Game profiles · activation & startup',font=('Segoe UI',18,'bold'),wraplength=750)
        self.heading.pack(anchor='w',fill='x')
        self.intro=ttk.Label(self.content_header,text='Save the published setup for each game, activate or stop its Overlay and choose automatic startup.',wraplength=750)
        self.intro.pack(anchor='w',fill='x',pady=(4,6))
        self.scope_notice=ttk.Label(self.content_header,text='Runtime selection only. Apply game bindings and native profiles through their separate reviewed controls.',wraplength=750)
        self.scope_notice.pack(anchor='w',fill='x')
        for label in (self.heading,self.intro,self.scope_notice):
            label.game_tools_wrap_managed=True
        form=ttk.Frame(body);form.pack(fill='x');form.columnconfigure(1,weight=1)
        ttk.Label(form,text='Game').grid(row=0,column=0,sticky='w',padx=(0,10),pady=4)
        self.game=Selector(form,on_select=lambda _:self.refresh_profiles(),on_add=self.add_game);self.game.grid(row=0,column=1,sticky='ew',pady=4)
        ttk.Label(form,text='Saved profile').grid(row=1,column=0,sticky='w',padx=(0,10),pady=4)
        self.profile=Selector(form,on_select=lambda _:self.refresh_status(),on_add=self.save_new)
        self.profile.grid(row=1,column=1,sticky='ew',pady=4)
        ttk.Label(form,text='New setup uses').grid(row=2,column=0,sticky='w',padx=(0,10),pady=4)
        self.kind=tk.StringVar(value='Azeron / published Overlay')
        ttk.Combobox(form,textvariable=self.kind,values=('Azeron / published Overlay','reWASD / controller or other device'),state='readonly').grid(row=2,column=1,sticky='ew',pady=4)
        bar=FlowToolbar(body);bar.pack(fill='x',pady=8)
        self.buttons={}
        for label,command in [('Activate',self.activate),('Deactivate',self.deactivate),
          ('Save current setup…',self.save_new),('Update selected',self.update_selected),('Refresh status',self.refresh)]:
            self.buttons[label]=bar.add(label,command)
        self.notice=ttk.Label(body,textvariable=self.summary,wraplength=750,font=('Segoe UI',11,'bold'))
        self.notice.pack(fill='x',pady=6)
        ttk.Label(body,textvariable=self.native_feedback,wraplength=750).pack(fill='x')
        auto=ttk.LabelFrame(body,text='Automatic startup',padding=10);auto.pack(fill='x',pady=8)
        ttk.Checkbutton(auto,text='Restore active profile when Game Tools opens',variable=self.restore,command=self.save_options).pack(anchor='w')
        ttk.Checkbutton(auto,text='Use each game’s saved default when that game is focused',variable=self.automatic,command=self.save_options).pack(anchor='w')
        self.windows_button=ttk.Checkbutton(auto,text='Open Unified Game Tools when I sign in to Windows',variable=self.windows,command=self.save_windows)
        self.windows_button.pack(anchor='w')
        if os.name!='nt':self.windows_button.state(['disabled'])
        self.table=ttk.Treeview(body,columns=('component','state','detail'),show='headings',height=6)
        for name,width in [('component',150),('state',135),('detail',450)]:
            self.table.heading(name,text=name.capitalize());self.table.column(name,width=width,minwidth=85,stretch=name=='detail')
        self.table.pack(fill='both',expand=True,pady=8)
        self.table_layout=TableLayout(self.table)
        ttk.Label(body,text='Azeron Activate starts the published Overlay. reWASD Activate selects a saved setup; native Apply / Remap Off are separate reviewed controls. Game bindings and mod settings retain their owners.',wraplength=750).pack(anchor='w',pady=6)
        tools=FlowToolbar(body);tools.pack(fill='x')
        tools.add('Open Controls & Overlay',self.open_overlay)
        tools.add('Show APP LAUNCHER',self.show_launcher)
        tools.add('Show profile details',self.details)
        tools.add('reWASD controls…',self.native_controls)
        self.notice.game_tools_wrap_managed=True
        body.bind('<Configure>',lambda e:[w.configure(wraplength=max(180,e.width-48))for w in (self.heading,self.intro,self.scope_notice,self.notice)],add='+')
        self.refresh()
        self.timer=parent.after(500,self.tick)
        self.restore_timer=parent.after(350,self.restore_profile)if autostart else None
    def report(self,error):
        self.summary.set(str(error));self.status(str(error))
    def refresh(self):
        try:
            self.value,self.pin=self.service.load();self.restore.set(self.value['options']['restore_on_open'])
            self.automatic.set(self.value['options']['automatic_game_switch'])
            games=self.service.games();games.update(self.extra_games)
            old=self.game.selected_id
            self.game.set_choices(list(games.items()))
            preferred=next((p['game_id']for p in self.value['profiles']if p['id']==self.value['active_profile_id']),None)
            self.game.select(old or preferred or next(iter(games),None));self.refresh_profiles()
            if os.name=='nt':self.windows.set((api.startup_folder()/api.LAUNCHER).exists())
        except Exception as error:self.report(error)
    def refresh_profiles(self):
        self.value,self.pin=self.service.load();selected=self.profile.selected_id
        profiles=[p for p in self.value['profiles']if p['game_id']==self.game.selected_id]
        self.profile.set_choices([(p['id'],p['name']+(' (auto)'if p['automatic']else''))for p in profiles])
        if not any(p['id']==selected for p in profiles):selected=next((p['id']for p in profiles if p['automatic']),None)
        self.profile.select(selected);self.refresh_status()
    def selected(self):
        value,pin=self.service.load()
        p=next((p for p in value['profiles']if p['id']==self.profile.selected_id),None)
        api.overlay.require(p is not None,'Save or choose a game profile first')
        return p,value,pin
    def save_new(self,*_):
        try:
            api.overlay.require(self.game.selected_id is not None,'Choose a game first')
            if self.kind.get().startswith('reWASD'):self.edit_native();return
            name=simpledialog.askstring('Save game profile','Profile name',parent=self.parent)
            if name is None:return
            p=self.service.capture(self.game.selected_id,name.strip())
            self.service.put(p,self.service.load()[1]);self.profile.select(None);self.refresh()
            self.summary.set('Profile saved. Activate it to start the saved Overlay setup.')
        except Exception as error:self.report(error)
    def update_selected(self):
        try:
            p,_,pin=self.selected()
            if p.get('provider')=='rewasd':self.edit_native(p);return
            new=self.service.capture(p['game_id'],p['name'],p['id']);new['automatic']=p['automatic']
            self.service.put(new,pin);self.refresh();self.summary.set('Profile updated from the published working setup; prior version retained.')
        except Exception as error:self.report(error)
    def activate_id(self,identity):
        value,pin=self.service.load();p=next(p for p in value['profiles']if p['id']==identity)
        problems=self.service.check(p);api.overlay.require(not problems,'; '.join(problems))
        # NativeStudio owns the existing process; no new command service exists.
        if p.get('provider')!='rewasd':self.unified.engine.start(reveal=False)
        self.service.activate(identity,pin)
        if p.get('provider')!='rewasd':self.overlay.follow_layer.set(True)
        self.overlay.tick(reschedule=False)
        self.attempted_auto=identity;self.summary.set('Profile activated. Checking loaded Studio triggers and display route…')
        self.refresh_profiles()
    def activate(self):
        try:self.activate_id(self.selected()[0]['id'])
        except Exception as error:self.report(error)
    def deactivate(self):
        try:
            self.service.deactivate(self.service.load()[1]);self.overlay.tick(reschedule=False)
            self.attempted_auto=None;self.summary.set('Profiles Off. Overlay display stopped. A native reWASD remap needs its separate Remap Off control.')
            self.refresh_status()
        except Exception as error:self.report(error)
    def save_options(self):
        try:
            v,pin=self.service.load();v['options'].update(restore_on_open=self.restore.get(),automatic_game_switch=self.automatic.get())
            self.service.save(v,pin);self.status('Automatic profile options saved.')
        except Exception as error:self.report(error);self.refresh()
    def save_windows(self):
        try:
            api.startup_entry(self.unified.install_root,self.windows.get(),api.startup_folder())
            self.status('Windows sign-in startup '+('enabled.'if self.windows.get()else'disabled.'))
        except Exception as error:self.report(error);self.refresh()
    def restore_profile(self):
        self.restore_timer=None
        if self.closed:return
        try:
            v,_=self.service.load()
            if v['options']['enabled']and v['options']['restore_on_open']and v['active_profile_id']:self.activate_id(v['active_profile_id'])
        except Exception as error:self.report('Automatic restore needs attention: '+str(error))
    def refresh_status(self):
        try:
            v,_=self.service.load();active=next((p for p in v['profiles']if p['id']==v['active_profile_id']),None)
            selected=next((p for p in v['profiles']if p['id']==self.profile.selected_id),None)
            if selected and selected.get('provider')=='rewasd':
                n=selected['native'];problems=self.service.check(selected)
                rows=[('Active setup','Selected'if active and active['id']==selected['id']else'Not selected',active['name']if active else'Profiles Off'),
                  ('Mapper','reWASD',n['device_name']),
                  ('Native config','Changed / unavailable'if problems else'Pinned + backed up','; '.join(problems)or n['config_path']),
                  ('Device / slot','ID saved'if n['device_id']else'Needs device ID','Slot '+str(n['slot'])+' • native application is a separate reviewed operation'),
                  ('Automatic switching','Native owner','Configure Autodetect and Background Agent in reWASD.'),
                  ('Controller Overlay','Not prepared','Device geometry and physical button outputs still need verification. Azeron images are not reused.')]
                for row in self.table.get_children():self.table.delete(row)
                for row in rows:self.table.insert('', 'end',values=row)
                if active and active['id']==selected['id']:
                    self.summary.set('Selected: '+selected['name']+' • native remap state is unverified; use reWASD controls to review/apply.')
                else:self.summary.set('Saved: '+selected['name']+' • selecting a profile applies no native mappings.')
                return
            live=self.unified.engine.readiness()if hasattr(self.unified.engine,'readiness')else {'fresh':False}
            expected_route=str(self.service.directory/'overlay-selection.ini')
            if live.get('fresh')and os.path.normcase(live.get('route_path',''))!=os.path.normcase(expected_route):
                live=dict(live,route_enabled=False)
            result=self.overlay.result or {}
            rows=[('Active setup','On'if active else'Off',active['name']if active else'Saved profiles are retained.'),
              ('Studio','Confirmed'if live.get('fresh')else'Waiting',str(live.get('triggers','unknown'))+' loaded triggers'if live.get('fresh')else live.get('reason','Waiting for native readiness')),
              ('Overlay trigger','Ready'if live.get('overlay_trigger')and live.get('enabled')else'Needs attention','A running process alone does not prove its saved trigger loaded.'),
              ('Display route','Ready'if live.get('route_enabled')else'Needs attention','Existing Studio Hold route; no new hotkey owner.'),
              ('Native layer',result.get('layer_state','Waiting'),result.get('reason','Waiting for a fresh Azeron layer event.')),
              ('Game / native bindings','Preserved','Activation never writes game configurations or Azeron profiles.')]
            for row in self.table.get_children():self.table.delete(row)
            for row in rows:self.table.insert('', 'end',values=row)
            if active:
                if live.get('fresh')and live.get('overlay_trigger')and live.get('enabled')and live.get('route_enabled'):
                    self.summary.set('Active: '+active['name']+' • Overlay trigger and route loaded'+(' • waiting for a fresh native layer event'if result.get('layer_state')not in {'Event-tracked','Observed'}else''))
                elif live.get('fresh'):
                    self.summary.set('Needs attention: saved profile is active, but Studio has no working Hold trigger/route. Restart Studio from its controls; existing settings are retained.')
        except Exception as error:self.report(error)
    def tick(self):
        if self.timer:
            try:self.parent.after_cancel(self.timer)
            except tk.TclError:pass
            self.timer=None
        if self.closed:return
        try:
            v,_=self.service.load()
            while not self.native_results.empty():
                result=self.native_results.get_nowait();self.native_busy=False;self.native_feedback.set(result);self.status(result)
            if v['options']['enabled']and v['options']['automatic_game_switch']:
                fg=self.overlay.foreground()
                if fg and not fg.get('own'):
                    p=self.service.match(fg['exe'])
                    active=next((x for x in v['profiles']if x['id']==v['active_profile_id']),None)
                    if p and (not active or p['game_id']!=active['game_id'])and p['id']!=self.attempted_auto:
                        self.attempted_auto=p['id']
                        try:self.activate_id(p['id'])
                        except Exception as error:self.report('Automatic profile needs attention: '+str(error))
            self.refresh_status()
        except Exception as error:self.report(error)
        self.timer=self.parent.after(1000,self.tick)
    def open_overlay(self):
        self.unified.tabs.select(self.overlay.parent)
    def show_launcher(self):
        if os.name=='nt':os.startfile(str(self.unified.install_root))
    def details(self):
        try:
            p,_,_=self.selected();window=tk.Toplevel(self.parent);window.title('Saved setup details')
            text=tk.Text(window,wrap='word',width=78,height=22);text.pack(fill='both',expand=True)
            text.insert('1.0',json.dumps(p,indent=2));text.configure(state='disabled')
        except Exception as error:self.report(error)
    def add_game(self,*_):
        """An unlisted name is a draft until a controller setup is saved."""
        name=simpledialog.askstring('Game for controller setup','Game name (for a reWASD setup)',parent=self.parent)
        if name is None:return
        try:
            name=name.strip();api.overlay.label(name)
            import re
            identity=re.sub('[^a-z0-9]+','-',name.lower()).strip('-')[:65]
            api.overlay.token(identity)
            games=self.service.games()
            api.overlay.require(identity not in games or games[identity]==name,'A different game already uses this name; choose it from the list')
            self.extra_games[identity]=name;self.kind.set('reWASD / controller or other device')
            self.refresh();self.game.select(identity);self.refresh_profiles()
        except Exception as error:self.report(error)
    def edit_native(self,profile=None):
        try:
            rows=self.service.rewasd.configs()
            api.overlay.require(bool(rows),'No native .rewasd configs found. Create or export one in reWASD first.')
            game=profile['game_id']if profile else self.game.selected_id
            games=self.service.games();games.update(self.extra_games)
            game_name=profile['game_name']if profile else games[game]
            value,pin=self.service.load()
            win=tk.Toplevel(self.parent);win.title('Save reWASD game setup');win.transient(self.parent.winfo_toplevel())
            body=ttk.Frame(win,padding=14);body.pack(fill='both',expand=True);body.columnconfigure(1,weight=1)
            ttk.Label(body,text=game_name,font=('Segoe UI',12,'bold')).grid(row=0,column=0,columnspan=2,sticky='w',pady=6)
            name=tk.StringVar(value=profile['name']if profile else game_name+' — controller')
            device=tk.StringVar(value=profile['native']['device_name']if profile else'Controller')
            device_id=tk.StringVar(value=profile['native']['device_id']if profile else'')
            slot=tk.StringVar(value=str(profile['native']['slot'])if profile else'1')
            ttk.Label(body,text='Setup name').grid(row=1,column=0,sticky='w');ttk.Entry(body,textvariable=name).grid(row=1,column=1,sticky='ew',pady=4)
            ttk.Label(body,text='Native config').grid(row=2,column=0,sticky='w',padx=(0,12))
            config=Selector(body);config.grid(row=2,column=1,sticky='ew',pady=4)
            config.set_choices([(r['path'],r['label']+(' (unsupported)'if r.get('error')else''))for r in rows])
            config.select(profile['native']['config_path']if profile else rows[0]['path'])
            for i,(label,var)in enumerate((('Device name',device),('reWASD device ID',device_id)),3):
                ttk.Label(body,text=label).grid(row=i,column=0,sticky='w',padx=(0,12));ttk.Entry(body,textvariable=var).grid(row=i,column=1,sticky='ew',pady=4)
            ttk.Label(body,text='Native slot').grid(row=5,column=0,sticky='w')
            ttk.Combobox(body,textvariable=slot,values=('1','2','3','4'),state='readonly').grid(row=5,column=1,sticky='w',pady=4)
            ttk.Label(body,text='Device ID is optional for saving. In reWASD, right-click your device → Copy device ID. Paste that value, not its USB VID/PID. Saving makes a private byte-exact backup and changes no native mappings.',wraplength=520).grid(row=6,column=0,columnspan=2,sticky='w',pady=10)
            notice=tk.StringVar();ttk.Label(body,textvariable=notice,wraplength=520).grid(row=7,column=0,columnspan=2,sticky='w')
            def save():
                try:
                    p=self.service.capture_rewasd(game,game_name,name.get().strip(),config.selected_id,device.get().strip(),device_id.get(),int(slot.get()),profile['id']if profile else None)
                    self.service.put(p,pin);win.destroy();self.profile.select(p['id']);self.refresh()
                    self.summary.set('reWASD setup saved and backed up. No native remap applied.')
                except Exception as error:notice.set(str(error))
            bar=FlowToolbar(body);bar.grid(row=8,column=0,columnspan=2,sticky='ew',pady=8)
            bar.add('Save setup',save);bar.add('Open reWASD',self.open_native);bar.add('Cancel',win.destroy)
            win.minsize(580,380)
        except Exception as error:self.report(error)
    def open_native(self):
        try:
            from GameToolRewasd import open_native
            open_native()
        except Exception as error:self.report(error)
    def open_native_profile(self,identity):
        """Navigate to the existing reviewed owner; selecting applies nothing."""
        value,_=self.service.load()
        p=next((x for x in value['profiles']if x['id']==identity and x.get('provider')=='rewasd'),None)
        api.overlay.require(p is not None,'Saved reWASD setup is missing; refresh the controller preference')
        self.refresh()
        self.game.select(p['game_id']);self.refresh_profiles()
        self.profile.select(p['id']);self.refresh_status()
        self.native_controls()
    def native_controls(self):
        try:
            p,_,_=self.selected();api.overlay.require(p.get('provider')=='rewasd','Choose a saved reWASD setup first')
            win=tk.Toplevel(self.parent);win.title('reWASD controls');body=ttk.Frame(win,padding=14);body.pack(fill='both',expand=True)
            n=p['native']
            ttk.Label(body,text=p['name'],font=('Segoe UI',12,'bold')).pack(anchor='w')
            ttk.Label(body,text=n['device_name']+' • slot '+str(n['slot'])+'\n'+n['config_path'],wraplength=580).pack(anchor='w',pady=8)
            ttk.Label(body,text='Save / Activate only selects this setup in Game Tools. Apply below sends this exact config to reWASD. Remap Off affects only the linked native device; closing this window does not turn remapping off.',wraplength=580).pack(anchor='w',pady=6)
            bar=FlowToolbar(body);bar.pack(fill='x')
            bar.add('Review Apply to slot…',lambda:self.review_native(p,'apply'))
            bar.add('Review Remap Off…',lambda:self.review_native(p,'off'))
            bar.add('Edit saved setup…',lambda:self.edit_native(p));bar.add('Open reWASD',self.open_native)
            ttk.Label(body,text='Automatic setup: in reWASD choose this config and slot → Autodetect (Radar) → add the actual game executable → Save. Enable Background Agent and its startup/restore options as needed. Review Remove applied config on exit. Game Tools does not create a second native remap switcher or alter Steam Input.',wraplength=580).pack(anchor='w',pady=10)
            ttk.Label(body,text='Physical controller buttons, extra buttons, Shift layers and Steam exclusion need a real device check. A successful command alone does not prove gameplay or Overlay readiness.',wraplength=580).pack(anchor='w',pady=6)
            bar2=FlowToolbar(body);bar2.pack(fill='x')
            bar2.add('Preview saved native config',lambda:self.preview_native(p));bar2.add('Close',win.destroy)
        except Exception as error:self.report(error)
    def preview_native(self,p):
        try:
            row=self.service.rewasd.check(p['native']);win=tk.Toplevel(self.parent);win.title('Native config preview — read only')
            text=tk.Text(win,wrap='word',width=78,height=24);text.pack(fill='both',expand=True)
            text.insert('1.0',row['raw'].decode('utf-8-sig'));text.configure(state='disabled')
        except Exception as error:self.report(error)
    def review_native(self,p,action):
        try:
            api.overlay.require(not self.native_busy,'A native operation is still running; wait for its result')
            current,_,_=self.selected();api.overlay.require(current==p,'Saved profile selection changed; reopen reWASD controls')
            proposal=self.service.rewasd.preview(p['native'],action)
            text=('Apply this exact config to the linked device slot?'if action=='apply'else'Turn remapping Off for this linked device (all its slots)?')
            text+='\n\nDevice: '+proposal['device']+'\nDevice ID: '+p['native']['device_id']+'\nSlot: '+str(proposal['slot'])+'\nConfig: '+proposal['config']+'\nSHA-256: '+proposal['sha256']+'\n\nOriginal config files are retained. Verify native output in reWASD afterward.'
            if not messagebox.askokcancel('Review reWASD operation',text,parent=self.parent):return
            self.native_busy=True;self.summary.set('Sending the reviewed operation to reWASD…')
            def run():
                try:
                    self.service.rewasd.execute_reviewed(p['native'],action,proposal,confirmed=True)
                    result='reWASD accepted '+action+'. Physical output remains unverified; check the controller in reWASD.'
                except Exception as error:result='reWASD operation needs attention: '+str(error)
                self.native_results.put(result)
            threading.Thread(target=run,daemon=True).start()
        except Exception as error:self.report(error)
    def close(self):
        self.closed=True
        if self.timer:self.parent.after_cancel(self.timer);self.timer=None
        if self.restore_timer:self.parent.after_cancel(self.restore_timer);self.restore_timer=None
        self.table_layout.close()
        self.scroll.close()
