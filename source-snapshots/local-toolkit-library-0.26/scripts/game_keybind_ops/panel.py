"""Embeddable operator pane: bounded worker, visible approval, Stop and history.

No network/daemon/watcher. All worker results are polled on Tk's main thread.
The owning Hub should connect its shared busy guard and cancellation lifecycle.
"""
from __future__ import annotations
import json,queue,threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk,filedialog,messagebox
from .core import Service
from .deps import read_json,Error,require
from .discovery import catalog,discover_local,windows_roots

class Panel(ttk.Frame):
    def __init__(self,master,data_dir,service=None,busy_guard=None):
        super().__init__(master,padding=10)
        self.service=service or Service(Path(data_dir));self.busy_guard=busy_guard or (lambda:False)
        self.plan=self.preview=self.items=None;self.worker=None;self.cancel=threading.Event();self.results=queue.Queue();self.closing=False
        self.controls=[]
        ttk.Label(self,text='Game Tools · Keybinds',font=('TkDefaultFont',16,'bold')).pack(anchor='w')
        ttk.Label(self,text='Locate → review native recipe → preview → stage → approve. Files verified ≠ tested in-game.').pack(anchor='w',pady=(2,8))
        row=ttk.Frame(self);row.pack(fill='x')
        self.game=tk.StringVar();games=[g['id'] for g in catalog()['games']]
        self.game_box=ttk.Combobox(row,textvariable=self.game,values=games,width=27);self.game_box.pack(side='left');self.game.set(games[0])
        self._button(row,'Locate',self.locate);self._button(row,'Register recipe…',self.register);self._button(row,'Open patch…',self.load_patch)
        row2=ttk.Frame(self);row2.pack(fill='x',pady=5)
        self.saved=tk.StringVar();self.history_box=ttk.Combobox(row2,textvariable=self.saved,width=40);self.history_box.pack(side='left')
        self._button(row2,'Refresh history',self.history);self._button(row2,'Open saved plan',self.open_saved);self._button(row2,'Inspect bindings',self.inspect)
        self.out=tk.Text(self,height=20,width=110,wrap='word',state='disabled');self.out.pack(fill='both',expand=True,pady=7)
        bar=ttk.Frame(self);bar.pack(fill='x')
        self.stage_button=self._button(bar,'Stage copies',self.stage)
        self.apply_button=self._button(bar,'Apply staged plan…',self.apply)
        self.undo_button=self._button(bar,'Prepare undo',self.undo)
        self.selective=tk.BooleanVar(value=False);ttk.Checkbutton(bar,text='Selective undo: preserve later settings',variable=self.selective).pack(side='left',padx=8)
        self.stop_button=ttk.Button(bar,text='Stop',command=self.cancel.set,state='disabled');self.stop_button.pack(side='right')
        self.status=tk.StringVar(value='No game file changed. Reviewed native recipes are required; locations alone are not enough.')
        ttk.Label(self,textvariable=self.status,wraplength=940).pack(anchor='w',pady=7)
        from .pack_panel import mount
        mount(self)
        self.sync_buttons()
    def destroy(self):
        if self.working:
            self.cancel.set()
            raise RuntimeError('Use request_close and allow the worker to reach a safe boundary before destroying this panel.')
        # Tcl variables must be released on Tk's owning thread, not during worker GC.
        for name in ('game','saved','selective','status'):
            if hasattr(self,name):setattr(self,name,None)
        super().destroy()
    def _button(self,parent,text,fn):
        b=ttk.Button(parent,text=text,command=lambda:self.run(fn));b.pack(side='left',padx=4);self.controls.append(b);return b
    @property
    def working(self):return self.worker is not None
    def sync_buttons(self):
        for b in self.controls:b.configure(state='disabled' if self.working else 'normal')
        if not self.working:
            self.stage_button.configure(state='normal' if self.preview and self.items else 'disabled')
            state=self.plan and self.plan['status']
            self.apply_button.configure(state='normal' if state=='STAGED_NOT_INSTALLED' else 'disabled')
            self.undo_button.configure(state='normal' if state and state!='STAGED_NOT_INSTALLED' else 'disabled')
        self.stop_button.configure(state='normal' if self.working else 'disabled')
    def show(self,value):
        self.out.configure(state='normal');self.out.delete('1.0','end');self.out.insert('1.0',json.dumps(value,ensure_ascii=False,indent=2));self.out.configure(state='disabled')
    def run(self,fn):
        try:
            require(not self.working,'ACTION_BUSY','This pane has an active operation.');fn()
        except (Error,OSError,ValueError,KeyError,TypeError) as e:self.error(e)
    def error(self,e):
        self.status.set(getattr(e,'code','LOCAL_OPERATION_REFUSED')+' · inspect the same operation; no automatic retry.')
        messagebox.showerror('Operation stopped',str(e),parent=self)
    def start(self,fn,done):
        require(not self.working and not self.busy_guard(),'ACTION_BUSY','Another local operation owns the host.')
        self.cancel.clear();self.status.set('Working. Stop takes effect at a safe file boundary; original backups remain retained.')
        def work():
            try:self.results.put((True,fn()))
            except Exception as e:self.results.put((False,e))
        self.worker=threading.Thread(target=work,name='GameToolsKeybinds',daemon=False)
        self.sync_buttons();self.worker.start();self.after(50,lambda:self.poll(done))
    def poll(self,done):
        try:ok,value=self.results.get_nowait()
        except queue.Empty:self.after(50,lambda:self.poll(done));return
        self.worker.join();self.worker=None
        try:
            if ok:done(value)
            else:self.error(value)
        finally:self.sync_buttons()
        if self.closing:self.winfo_toplevel().destroy()
    def request_close(self):
        if self.working:self.closing=True;self.cancel.set();self.status.set('Stopping at a safe boundary before closing.')
        else:self.winfo_toplevel().destroy()
    def locate(self):
        game=self.game.get()
        def job():
            roots,warnings=windows_roots();r=discover_local(game,roots);r['root_resolution_notes']=warnings;return r
        self.start(job,lambda v:(self.show(v),self.status.set('Candidate locations only. Multiple profiles/builds require selection, not a guess.')))
    def register(self):
        path=filedialog.askopenfilename(parent=self,title='Reviewed native binding recipe',filetypes=[('JSON','*.json')])
        if path:
            recipe=read_json(Path(path))
            # Operator-only file picker; AI cannot register a filesystem target.
            self.start(lambda:self.service.register_local(recipe),lambda v:(self.show(v),self.status.set('Registered recipe. No game file changed.')))
    def load_patch(self):
        path=filedialog.askopenfilename(parent=self,title='Field-ID binding patch',filetypes=[('JSON','*.json')])
        if not path:return
        items=read_json(Path(path))['items']
        def done(v):self.items=items;self.preview=v;self.plan=None;self.show(v);self.status.set('Preview only. Stage before applying.')
        self.start(lambda:self.service.preview(items),done)
    def stage(self):
        if not self.preview:return
        items=self.items;expected=self.preview['preview_sha256']
        def done(v):self.plan=v;self.items=self.preview=None;self.show(v);self.status.set('Staged with original backups. Not installed.')
        self.start(lambda:self.service.prepare(items,expected),done)
    def open_saved(self):
        ident=self.saved.get()
        def done(v):self.plan=v;self.items=self.preview=None;self.show(v);self.status.set(v['status'])
        self.start(lambda:self.service.status(ident),done)
    def apply(self):
        if not self.plan:return
        plan=self.service.status(self.plan['plan_id']);self.show(plan)
        if not messagebox.askyesno('Apply this exact binding plan?',
            'Close the game and its listed launcher/cloud writers. Original bytes are backed up.\n\n'
            'Replace only the listed configuration files?\n\nPlan SHA-256:\n'+plan['plan_sha256'],parent=self):return
        ident,expected=plan['plan_id'],plan['plan_sha256']
        def done(v):self.plan=v;self.show(v);self.status.set(v['status'])
        self.start(lambda:self.service.apply_local(ident,expected,authorize=lambda p:p['plan_sha256']==expected,cancel=self.cancel),done)
    def undo(self):
        if not self.plan:return
        ident=self.plan['plan_id'];selective=self.selective.get()
        def job():
            p=self.service.rollback_preview(ident,selective=True) if selective else self.service.exact_rollback_preview(ident)
            return self.service.prepare_rollback(ident,p['preview_sha256'],selective=selective)
        def done(v):self.plan=v;self.items=self.preview=None;self.show(v);self.status.set('Inverse copies staged. Apply requires separate approval.')
        self.start(job,done)
    def history(self):
        def done(v):
            self.show(v);ids=[p['plan_id'] for p in v];self.history_box['values']=ids
            if ids and self.saved.get() not in ids:self.saved.set(ids[-1])
            self.status.set('Choose a saved plan to inspect or prepare undo.')
        self.start(self.service.history,done)
    def inspect(self):self.start(self.service.context,lambda v:(self.show(v),self.status.set('Reviewed bindings only; no private paths in this context packet.')))

def attach(notebook,data_dir,*,service=None,busy_guard=None):
    panel=Panel(notebook,data_dir,service,busy_guard);notebook.add(panel,text='Keybinds');return panel

def main(data_dir):
    root=tk.Tk();root.title('Game Tools · Keybinds · Development preview');root.geometry('1050x680')
    frame=Panel(root,data_dir);frame.pack(fill='both',expand=True);root.protocol('WM_DELETE_WINDOW',frame.request_close);root.mainloop()
