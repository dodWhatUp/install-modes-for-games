"""Real Tk mod browsing and floating settings in a private guest X display."""
import copy,json,sys,time,tkinter as tk,zipfile
from pathlib import Path
from PIL import ImageGrab
from control_service import DemoService,DEFAULTS
from mod_panel import Panel

base=Path(sys.argv[1]);out=Path(sys.argv[2]);base.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
root=tk.Tk();service=DemoService(base);panel=Panel(root,service,demo=True);checks=[]
def callback_error(kind,error,tb):raise error.with_traceback(tb)
root.report_callback_exception=callback_error
def check(condition,name):
    assert condition,name
    checks.append(name)
def pump():
    until=time.monotonic()+15
    while panel.busy or panel.snapshot is None:
        root.update();time.sleep(.04)
        if time.monotonic()>until:raise AssertionError('UI worker did not finish')
    root.update()
def shot(name):root.update();ImageGrab.grab().save(out/name)
pump();tools=panel.mod_tools;tools.show();root.update()
check(len(tools.items)==9,'Installed mod/DLC resources are discoverable in one browser')
tools.mod_name.set('FOV');tools.filter_mods();tools.commit_selection();root.update()
check(tools.selected=='fov','One editable selector supports search and commitment')
check(service.values==DEFAULTS,'Browsing does not apply files')
tools.mod_name.set('no matching fixture');tools.filter_mods();tools.commit_selection()
check(tools.selected=='fov','No-result search preserves selection')
tools.render_mod();check(tools.mod_name.get()=='FOV Extender','Cancel/render restores the selected label')
tools.read_page();pump();check('AUTHOR DOCUMENTATION' in tools.details.get('1.0','end'),'Author information can be read inside the app')
opened=[];panel.open_path=lambda p:opened.append(Path(p))
tools.folder_name.set('Mod settings');tools.update_folder();tools.open_folder()
check(opened[-1]==tools.current()['locations']['Mod settings'],'Open folder uses the selected mod location')
tools.window.geometry('700x560');tools.render_mod();root.update();shot('mod-library.png')
floating=tools.floating('fov');root.update()
check(floating==tools.floating('fov'),'Reopening settings reuses the same floating window')
floating.topmost.set(True);floating.set_topmost();root.update()
check(service.values==DEFAULTS,'Always-on-top is only a view preference')
floating.topmost.set(False);floating.set_topmost()
floating.entries['fov_min'].delete(0,'end');floating.entries['fov_min'].insert(0,'50');root.update()
check(float(panel.vars['fov_min'].get())==50,'Floating edit shares the main preview')
check(service.values['fov_min']==45,'Floating edits do not auto-apply')
panel.vars['duration'].set('7');root.update();floating.apply();pump()
check(service.values['fov_min']==50,'Apply this mod commits its settings')
check(service.values['duration']==2,'Apply this mod leaves unrelated game settings unchanged')
check(float(panel.vars['duration'].get())==7,'Unrelated pending preview edits survive a per-mod Apply')
panel.vars['fov'].set(False);root.update();floating.apply();pump()
check('FOV Extender' not in panel.applied.get(),'Per-mod disable refreshes the applied-status summary')
panel.vars['fov'].set(True);root.update();floating.apply();pump()
check('FOV Extender' in panel.applied.get(),'Per-mod reenable refreshes the applied-status summary')
panel.vars['fov_min'].set('71');root.update()
check(str(floating.apply_button.cget('state'))=='disabled','Floating editor validates the original bounds')
panel.vars['fov_min'].set('50');panel.vars['fov_max'].set('65');root.update()
panel.profile_name.set('Floating setup');panel.save_profile();root.update()
check((base/'saved-profiles/Floating setup.json').exists(),'Floating preview can persist as a normal profile file')
floating.geometry('480x340');root.update();shot('floating-settings.png');floating.destroy();root.update()
check(float(panel.vars['fov_max'].get())==65 and service.values['fov_max']==60,'Closing a floating editor retains preview without applying it')
check(not floating.traces,'Closing removes variable callbacks')
tools.show('manager');root.update();tools.prepare();pump()
check(tools.latest is not None and (tools.latest/'Shadow of War Manager Files.zip').is_file(),'Preparation creates a persistent package ZIP')
profile=json.loads((tools.latest/'profile.json').read_text())
check(profile['duration']==2 and profile['fov_max']==60,'Export uses applied values, not unrelated pending preview')
tools.open_export_folder();tools.open_package()
check(opened[-2:]==[tools.latest,tools.latest/'Shadow of War Manager Files.zip'],'Folder and package open actions remain separate')
tools.window.geometry('650x540');root.update();shot('manager-transfer-small.png')
check(tools.prepare_button.winfo_viewable(),'Prepare remains discoverable in the compact manager panel')
check(service.values['duration']==2,'Preparation does not deploy or apply preview')
tools.floating('elven-speed');root.update();shot('floating-elven-speed.png')
root.destroy()
result={'passed':len(checks),'checks':checks,'scope':'Real Tk and demo files in isolated Linux Xvfb; no host game/manager/browser actions'}
(out/'mod-tools-gui-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
