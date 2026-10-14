"""Optional Tk pane. Mount in a verified Tk host; never monkey-patch an unknown Hub.
Network runs only after a local click/confirmation. No listener, service or auto-start.
"""
from __future__ import annotations
import json
import os
import queue
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from .cli import DEFAULT_RECIPE
from .recipes import load_recipe, plan
from .safety import ModError, require
from .workflow import Job, default_data, acquire, import_archive, stage
from .umm import inventory
try:
    from GameToolCompactUI import FlowToolbar, TableLayout
except ImportError:
    FlowToolbar = TableLayout = None

class ModWorkflowPanel(ttk.Frame):
    def __init__(self, parent, recipe_path=DEFAULT_RECIPE, data_root=None):
        super().__init__(parent, padding=10)
        self.recipe_path, self.data_root = Path(recipe_path), Path(data_root or default_data())
        self.recipe = load_recipe(self.recipe_path)
        self.job, self.worker = None, None
        self.peer_busy = lambda: False
        self.cancel_event = threading.Event()
        self.messages = queue.Queue()
        self.mode = tk.StringVar(value='real-time')
        self.status = tk.StringVar(value='Planning only. Nothing downloaded, installed or enabled.')
        self.checks = {}
        top = ttk.Frame(self); top.pack(fill='x')
        ttk.Label(top, text=self.recipe['name']).pack(side='left', padx=(0,15))
        ttk.Combobox(top, textvariable=self.mode, values=['real-time','turn-based'], state='readonly', width=13).pack(side='left')
        ttk.Button(top, text='Use preset', command=self.use_preset).pack(side='left', padx=4)
        ttk.Button(top, text='Open existing job', command=self.open_job).pack(side='right')
        box = ttk.LabelFrame(self, text='Choose items for a NEW plan', padding=6); box.pack(fill='x', pady=8)
        for i, item in enumerate(self.recipe['items']):
            var = tk.BooleanVar(value=item['id'] in self.recipe['presets'].get('real-time', []))
            self.checks[item['id']] = var
            ttk.Checkbutton(box, text=item['name'], variable=var).grid(row=i//3, column=i%3, sticky='w', padx=7)
        bar = FlowToolbar(self) if FlowToolbar else ttk.Frame(self); bar.pack(fill='x')
        for text, fn in [('Create plan',self.create_plan), ('Download selected plan',self.download),
                         ('Import archive',self.import_one), ('Stage selected',self.stage_one),
                         ('Official page',self.open_page), ('Inspect game',self.inspect_game)]:
            if FlowToolbar: bar.add(text, fn)
            else: ttk.Button(bar, text=text, command=fn).pack(side='left', padx=(0,3))
        if FlowToolbar: bar.add('Cancel transfer', self.cancel_event.set)
        else: ttk.Button(bar, text='Cancel transfer', command=self.cancel_event.set).pack(side='right')
        self.tree = ttk.Treeview(self, columns=('order','name','version','status'), show='headings', height=9)
        for name, width in [('order',40),('name',210),('version',160),('status',300)]:
            self.tree.heading(name, text=name.title()); self.tree.column(name,width=width,stretch=name in {'name','status'})
        self.tree.pack(fill='both', expand=True, pady=8)
        self.tree.bind('<<TreeviewSelect>>', self.show_details)
        self.column_layout = TableLayout(self.tree) if TableLayout else None
        ttk.Label(self, textvariable=self.status, wraplength=980).pack(fill='x')
        self.details = tk.Text(self,height=8,wrap='word'); self.details.pack(fill='both',expand=True,pady=(8,0))
        self.set_details({'notice':'This pane is mounted in the current Hub source. Downloaded or staged files are NOT installed. New-folder installation is a separate guarded CLI action; UMM loader setup remains in its official installer. AI requests use the same jobs and require local approval.'})
        self.refresh()
        self._poll_handle = self.after(150,self.poll)
        self.bind('<Destroy>', self.on_destroy, add='+')
    def on_destroy(self, event):
        if event.widget is self:
            self.cancel_event.set()
            try: self.after_cancel(self._poll_handle)
            except tk.TclError: pass
    def set_details(self, obj):
        self.details.configure(state='normal'); self.details.delete('1.0','end')
        self.details.insert('end', obj if isinstance(obj,str) else json.dumps(obj,indent=2,ensure_ascii=False))
        self.details.configure(state='disabled')
    def idle(self):
        if self.peer_busy() or self.worker and self.worker.is_alive():
            messagebox.showinfo('Operation active','Cancel the current operation and let it finish before changing jobs.',parent=self)
            return False
        return True
    def use_preset(self):
        if not self.idle(): return
        for ident,var in self.checks.items(): var.set(ident in self.recipe.get('presets',{}).get(self.mode.get(),[]))
        self.status.set('Preset changed for the next plan only; the existing job is unchanged.')
    def create_plan(self):
        if not self.idle(): return
        try:
            p = plan(self.recipe,[i for i,v in self.checks.items() if v.get()],self.mode.get())
            self.job = Job.create(self.data_root,p)
            self.status.set('Plan saved. No network or installation action. Job: '+str(self.job.path))
            self.set_details({'plan_sha256':p['plan_sha256'],'warnings':p['warnings']}); self.refresh()
        except ModError as e: self.set_details(e.record())
    def open_job(self):
        if not self.idle(): return
        folder = filedialog.askdirectory(title='Select an existing workflow job folder',parent=self)
        if not folder: return
        try:
            j = Job(Path(folder)); require(j.plan['game_id']==self.recipe['game_id'],'GAME_MISMATCH','Open this job with its matching recipe.')
            self.job=j; self.refresh(); self.status.set('Existing job opened without rerunning any action.')
        except (ModError,OSError) as e: self.set_details(e.record() if isinstance(e,ModError) else {'status':'OPEN_FAILED'})
    def selected(self):
        selection=self.tree.selection()
        if not selection: raise ModError('SELECTION_REQUIRED','Select one item in the table.')
        return selection[0]
    def refresh(self):
        previous=self.tree.selection(); self.tree.delete(*self.tree.get_children())
        items=self.job.plan['items'] if self.job else self.recipe['items']
        for n,item in enumerate(items,1):
            state=self.job.latest(item['id'])['status'] if self.job else 'NOT_PLANNED'
            self.tree.insert('', 'end', iid=item['id'], values=(n,item['name'],item.get('display_version',''),state))
        if previous and self.tree.exists(previous[0]): self.tree.selection_set(previous[0])
    def show_details(self,_event=None):
        try:
            ident=self.selected()
            item=self.job.item(ident) if self.job else next(i for i in self.recipe['items'] if i['id']==ident)
            self.set_details({'name':item['name'],'source':item['download_page'],'warnings':item.get('warnings',[]),
                              'operation':self.job.latest(ident) if self.job else 'not planned'})
        except ModError: pass
    def run(self, fn, label):
        if not self.idle(): return
        self.cancel_event.clear(); self.status.set(label)
        def worker():
            try: self.messages.put(fn())
            except ModError as e: self.messages.put(e.record())
            except Exception: self.messages.put({'status':'UNEXPECTED_FAILURE','message':'Inspect the current job. No automatic retry was made.'})
        self.worker=threading.Thread(target=worker,name='ModWorkflow-explicit-action',daemon=False);self.worker.start()
    def download(self):
        if not self.job or not self.idle(): return
        if messagebox.askyesno('Download this plan?', 'Allow up to 128 MiB, 40 requests and 5 minutes from official providers?\nThis downloads only. Nexus authorization may still be required.',parent=self):
            self.run(lambda: acquire(self.job,allow_network=True,nexus_key=os.environ.get('NEXUS_MODS_API_KEY'),cancel=self.cancel_event),'Downloading the selected immutable plan. No installation.')
    def import_one(self):
        if not self.job or not self.idle(): return
        try: ident=self.selected()
        except ModError as e: self.set_details(e.record());return
        file=filedialog.askopenfilename(title='Select original official mod ZIP',filetypes=[('ZIP archives','*.zip')],parent=self)
        if file and messagebox.askyesno('Confirm source','Did this original archive come from the selected author’s official download?',parent=self):
            self.run(lambda: import_archive(self.job,ident,Path(file),confirmed_source=True),'Validating and copying the original archive privately.')
    def stage_one(self):
        if not self.job or not self.idle(): return
        try: ident=self.selected()
        except ModError as e: self.set_details(e.record());return
        self.run(lambda: stage(self.job,ident),'Staging privately; no game files will be changed.')
    def open_page(self):
        try:
            ident=self.selected();item=self.job.item(ident) if self.job else next(i for i in self.recipe['items'] if i['id']==ident)
            # A deliberate local click only. No script controls the browser or intercepts authentication.
            webbrowser.open(item['download_page'],new=2)
        except ModError as e:self.set_details(e.record())
    def inspect_game(self):
        if not self.idle():return
        folder=filedialog.askdirectory(title='Choose the Kingmaker installation folder (read only)',parent=self)
        if folder:self.run(lambda:inventory(Path(folder)),'Reading existing game/mod metadata; no changes.')
    def poll(self):
        try:
            while True:
                result=self.messages.get_nowait();self.set_details(result)
                self.status.set('Operation finished. Review the explicit status; downloaded or staged does not mean installed.')
                self.refresh()
        except queue.Empty:pass
        self._poll_handle = self.after(150,self.poll)
    def can_close(self):
        """Host must call this before destroying the pane; transfer exits after I/O timeout."""
        if self.worker and self.worker.is_alive():
            self.cancel_event.set()
            self.status.set('Cancellation requested. Keep this window open until the active request returns (bounded I/O timeout).')
            return False
        return True


def attach(notebook, recipe_path=DEFAULT_RECIPE, data_root=None):
    """Supported source-level integration seam. Does not alter existing tabs or settings."""
    pane=ModWorkflowPanel(notebook,recipe_path,data_root)
    notebook.add(pane,text='Mods')
    return pane


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--recipe',type=Path,default=DEFAULT_RECIPE);p.add_argument('--data-dir',type=Path)
    a=p.parse_args();root=tk.Tk();root.title('Game Tool Hub — Mod Workflows 0.1.1 preview')
    root.geometry('1100x650');pane=ModWorkflowPanel(root,a.recipe,a.data_dir);pane.pack(fill='both',expand=True)
    root.protocol('WM_DELETE_WINDOW',lambda:root.destroy() if pane.can_close() else None)
    root.mainloop()
