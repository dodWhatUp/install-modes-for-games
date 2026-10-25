"""Actual Tk callback/render acceptance in a guest-owned Xvfb display."""
import copy, json, sys, time, tkinter as tk
from pathlib import Path
from tkinter import ttk
from PIL import ImageGrab
from control_service import DemoService, DEFAULTS
from mod_panel import Panel

base=Path(sys.argv[1]);out=Path(sys.argv[2]);base.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
root=tk.Tk();service=DemoService(base);panel=Panel(root,service,demo=True)
checks=[]
def pump():
    until=time.monotonic()+12
    while panel.busy or panel.snapshot is None:
        root.update();time.sleep(.05)
        if time.monotonic()>until:raise AssertionError('UI worker did not complete')
    root.update()
def check(condition,name):
    assert condition,name
    checks.append(name)
def button(text):
    found=[]
    def walk(w):
        if isinstance(w,ttk.Button) and w.cget('text')==text:found.append(w)
        for c in w.winfo_children():walk(c)
    walk(panel)
    assert len(found)==1,(text,len(found));return found[0]
def shot(name):
    root.update();ImageGrab.grab().save(out/name)
pump()
check(service.values==DEFAULTS,'Opening/refresh is read-only')
shot('shadow-controls-simple.png')
panel.precise.set(True);panel.toggle_view();root.update()
check(service.values==DEFAULTS,'Showing precise controls does not enable/change features')
panel.vars['duration'].set('3.5');root.update()
check(service.values['duration']==2,'Typing edits only preview')
check('pending' in panel.dirty.get(),'Pending changes are visible')
panel.profile_name.set('Guest setup');button('Save profile file').invoke();root.update()
check((base/'saved-profiles/Guest setup.json').exists(),'Saving creates a persistent profile file')
check(service.values['duration']==2,'Saving a profile does not apply it')
panel.vars['duration'].set('5');button('Load to preview').invoke();root.update()
check(float(panel.vars['duration'].get())==3.5,'Loading restores saved preview')
panel.vars['fov_min'].set('71');root.update()
check(str(panel.apply_button.cget('state'))=='disabled','Invalid bounds disable Apply')
panel.vars['fov_min'].set('45');button('Apply & keep files').invoke();pump()
check(service.values['duration']==3.5,'Apply commits selected preview and refreshes readback')
check((base/'demo-applied.json').exists(),'Applied settings remain as a file')
panel.precise.set(False);panel.toggle_view();root.update()
check(service.values['duration']==3.5,'Hiding values does not reset operation settings')
panel.precise.set(True);panel.advanced.set(True);panel.toggle_view();root.geometry('850x650');root.update()
apply=button('Apply & keep files')
check(apply.winfo_rooty()+apply.winfo_height()<=root.winfo_rooty()+root.winfo_height(),'Footer remains visible at minimum window size')
check(panel.canvas.winfo_height()>100,'Overflow stays inside a scrollable body')
shot('shadow-controls-precise-small.png')
root.geometry('960x850');root.update();shot('shadow-controls-precise.png')
view=json.loads((base/'control-panel-view.json').read_text())
check(view['precise'] and view['experimental'],'View choices persist separately from game settings')
root.destroy()
root2=tk.Tk();panel2=Panel(root2,DemoService(base),demo=True)
root=root2;panel=panel2;service=panel.service;pump()
check(panel.precise.get(),'Reopening restores saved view')
panel.profile_name.set('Guest setup');panel.load_profile();root.update()
check(float(panel.vars['duration'].get())==3.5,'Saved profile survives closing and reopening the UI')
root.destroy()
(out/'shadow-controls-gui-results.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'scope':'Real Tk widgets/callbacks/rendering inside isolated Linux Xvfb; no real game/host input'},indent=2))
print(json.dumps({'passed':len(checks),'checks':checks}))
