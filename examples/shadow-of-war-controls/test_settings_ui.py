"""First-open and in-app settings recovery with real Tk in the isolated guest."""
from pathlib import Path
import json,sys,time,tkinter as tk
from PIL import ImageGrab
from control_service import DemoService
from mod_panel import Panel
from settings_locator import RELATIVE,resolve_settings,scan_settings
from settings_ui import SettingsLocationDialog,startup_service
from test_settings_locator import config

base=Path(sys.argv[1]).resolve();base.mkdir(parents=True,exist_ok=True);out=Path(sys.argv[2]);checks=[]
def check(condition,name):
    assert condition,name
    checks.append(name)
def error(kind,value,tb):raise value.with_traceback(tb)
def root_new():
    root=tk.Tk();root.report_callback_exception=error;return root
def put(path,data=None):path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(config() if data is None else data);return path
def pump(root,condition):
    deadline=time.monotonic()+15
    while not condition():
        root.update();time.sleep(.04)
        if time.monotonic()>deadline:raise AssertionError('Settings UI did not finish')
    root.update()

root=root_new();workspace=base/'first-open';workspace.mkdir();local=base/'first-local';local.mkdir()
def factory(workspace):return resolve_settings(workspace,roots=[local])
def first_setup():
    dialogs=[w for w in root.winfo_children() if isinstance(w,SettingsLocationDialog)]
    check(len(dialogs)==1,'Missing settings open a recovery window instead of terminating the app')
    dialog=dialogs[0];dialog.geometry('650x500');root.update();ImageGrab.grab().save(out/'settings-location-missing.png')
    native=put(local/RELATIVE);dialog.find_button.invoke()
root.after(180,first_setup)
result=startup_service(root,workspace,factory,roots=[local])
check(result is not None and result['status']=='found','First-open retry continues after automatic recovery')
check((workspace/'control-panel-paths.json').exists(),'The app builds its own persistent path mapping')
check((local/RELATIVE).read_bytes()==config(),'Automatic setup leaves native game settings unchanged')
root.destroy()

root=root_new();workspace=base/'conflict';workspace.mkdir();local=base/'conflict-local';local.mkdir()
one=put(local/'Packages/A/LocalCache/Local'/RELATIVE);two=put(local/'Packages/B/LocalCache/Local'/RELATIVE,config(2560,1440))
dialog=SettingsLocationDialog(root,workspace,scan_settings(workspace,[local]),roots=[local],allow_external=False)
root.update();check('Several' in dialog.status.get(),'Conflicting valid files receive a clear choice')
check(str(dialog.use_button.cget('state'))=='disabled','No conflicting file is selected automatically')
dialog.tree.selection_set('1');dialog.selection();root.update()
check(str(dialog.use_button.cget('state'))=='normal','A validated candidate can be explicitly selected')
ImageGrab.grab().save(out/'settings-location-choice.png');dialog.use_button.invoke();pump(root,lambda:not dialog.winfo_exists())
check(dialog.accepted is not None and json.loads((workspace/'control-panel-paths.json').read_text())['native_config_path']==str(dialog.accepted),'Selected file is persisted and read back')
check(one.read_bytes()==config() and two.read_bytes()==config(2560,1440),'Choosing a location changes neither candidate config')
root.destroy()

root=root_new();workspace=base/'still-missing';workspace.mkdir()
dialog=SettingsLocationDialog(root,workspace,roots=[],allow_external=False);dialog.find_button.invoke()
pump(root,lambda:not dialog.busy)
check(dialog.winfo_exists() and 'No valid' in dialog.status.get(),'An unsuccessful search stays in the recovery UI with an actionable message')
check(not (workspace/'control-panel-paths.json').exists(),'Failed search does not invent a path mapping')
dialog.close();root.destroy()

root=root_new();workspace=base/'cancel';workspace.mkdir()
def cancel_setup():
    next(w for w in root.winfo_children() if isinstance(w,SettingsLocationDialog)).close()
def missing_factory(workspace):return resolve_settings(workspace,roots=[])
root.after(100,cancel_setup)
check(startup_service(root,workspace,missing_factory,roots=[]) is None,'Cancelling first-open setup exits cleanly')
root.destroy()

root=root_new();workspace=base/'pending';workspace.mkdir();service=DemoService(workspace);panel=Panel(root,service,demo=True)
pump(root,lambda:panel.snapshot is not None and not panel.busy)
panel.vars['duration'].set('7');native=put(workspace/'demo-local-appdata'/RELATIVE)
panel.location_blocked=True;panel.changed();check(str(panel.apply_button.cget('state'))=='disabled','Missing settings block Apply without discarding preview')
panel.setup_settings();dialog=panel._settings_dialog;dialog.find_button.invoke()
pump(root,lambda:not dialog.winfo_exists() and not panel.busy)
check(float(panel.vars['duration'].get())==7,'Repairing the location preserves existing pending edits')
check(service.values['duration']==2,'Repairing a location does not apply game changes')
check(not panel.location_blocked,'Successful repair restores the controller state')
root.destroy()
result={'passed':len(checks),'checks':checks,'scope':'Real Tk recovery/choice/retry and disposable config mappings in isolated Linux; no game launch or native settings writes'}
(out/'settings-location-gui-results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
