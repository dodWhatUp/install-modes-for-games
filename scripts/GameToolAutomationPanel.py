"""Native, visible approval and AI data-sharing controls. No automatic effects."""
from __future__ import annotations
import json
import sys
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GameToolCompactUI import FlowToolbar, ScrollableFrame, TableLayout
from GameToolAutomation import AutomationService, capabilities
from game_mod_ops.safety import ModError, json_new, read_json

VERSION = "0.1.0"

class AutomationPanel(ttk.Frame):
    def __init__(self, parent, service, status=None, peer_busy=None):
        super().__init__(parent)
        self.service, self.shared_status = service, status
        self.peer_busy = peer_busy or (lambda: False)
        self.tool_snapshot=lambda: {}
        self.worker=None; self.messages=queue.Queue(); self._closed=False; self._poll=None
        self.watch=tk.BooleanVar(self,value=False)
        self.allow_client_requests=tk.BooleanVar(self,value=False)
        self.state=tk.StringVar(self,value='AI requests are proposals. Nothing executes on arrival.')
        self.body=ScrollableFrame(self,min_width=420);self.body.pack(fill='both',expand=True)
        content=self.body.body
        ttk.Label(content,text='AI & automation',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(content,textvariable=self.state,wraplength=880).pack(anchor='w',pady=(4,8))
        tools=FlowToolbar(content);tools.pack(fill='x')
        self.buttons={}
        for caption,action in [('Refresh requests',self.refresh),('Import AI request',self.import_request),
                               ('Copy AI context',self.copy_context),('Save AI context',self.save_context),
                               ('Share report summary',self.share_report),('Share tool status',self.share_tools),('Copy client setup',self.copy_client_setup),('Capabilities',self.show_capabilities)]:
            self.buttons[caption]=tools.add(caption,action)
        ttk.Checkbutton(content,text='Refresh proposals while this app is open (never execute automatically)',
                        variable=self.watch,command=self.toggle_watch).pack(anchor='w',pady=6)
        ttk.Checkbutton(content,text='Include proposal submission in copied client setup (local approval still required)',
                        variable=self.allow_client_requests).pack(anchor='w',pady=(0,6))
        box=ttk.Frame(content);box.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(box,columns=('operation','status','id'),show='headings',height=7)
        for c,w in [('operation',170),('status',220),('id',230)]:
            self.tree.heading(c,text=c.title());self.tree.column(c,width=w)
        self.tree.pack(side='left',fill='both',expand=True)
        scroll=ttk.Scrollbar(box,command=self.tree.yview);scroll.pack(side='right',fill='y')
        self.tree.configure(yscrollcommand=scroll.set);self.layout=TableLayout(self.tree)
        self.tree.bind('<<TreeviewSelect>>',self.show_selected)
        actions=FlowToolbar(content);actions.pack(fill='x',pady=7)
        self.buttons['Approve selected']=actions.add('Approve selected',self.approve)
        self.buttons['Reject selected']=actions.add('Reject selected',self.reject)
        self.buttons['Stop active operation']=actions.add('Stop active operation',self.stop)
        self.output=tk.Text(content,wrap='word',height=11);self.output.pack(fill='both',expand=True)
        self.write(capabilities())
        self.bind('<Destroy>',self._destroy,add='+')
        # No filesystem mutation, refresh loop, provider or network is started.

    @property
    def busy(self): return bool(self.worker and self.worker.is_alive())
    def set_state(self,text):
        self.state.set(text)
        if self.shared_status is not None:self.shared_status.set(text)
    def write(self,value):
        self.output.configure(state='normal');self.output.delete('1.0','end')
        self.output.insert('end',json.dumps(value,ensure_ascii=False,indent=2));self.output.configure(state='disabled')
    def safe(self,action):
        try:return action()
        except (ModError,ValueError,OSError) as error:
            self.write({'status':getattr(error,'code','LOCAL_OPERATION_REFUSED'),
                        'message':'No automatic retry. Review the selected request or source.'})
            self.set_state('Operation refused. Existing evidence retained.')
    def refresh(self):
        def go():
            selected=self.tree.selection();self.tree.delete(*self.tree.get_children())
            for row in self.service.list_requests():
                ident=row['request_id'];self.tree.insert('', 'end', iid=ident,
                     values=(row.get('operation','unknown'),row['status'],ident))
            if selected and self.tree.exists(selected[0]):self.tree.selection_set(selected[0])
        self.safe(go)
    def selected(self):
        ids=self.tree.selection()
        if not ids:raise ModError('SELECTION_REQUIRED','Select one request.')
        return self.service.request_status(ids[0])
    def show_selected(self,_event=None): self.safe(lambda:self.write(self.selected()))
    def show_capabilities(self):self.write(capabilities())
    def client_setup(self):
        args=['-B',str(Path(__file__).resolve().with_name('GameToolAI.py')),
              '--data-dir',str(self.service.data_dir)]
        if self.allow_client_requests.get():args.append('--allow-requests')
        args.append('stdio')
        # pythonw has no usable standard I/O on Windows; use its sibling console
        # interpreter only when it exists. Never download or register a runtime.
        command=Path(sys.executable)
        if command.name.lower()=='pythonw.exe':
            console=command.with_name('python.exe')
            if not console.is_file():raise ModError('RUNTIME_REQUIRED','A console Python interpreter is required for stdio.')
            command=console
        return {'mcpServers':{'unified-game-tools':{'command':str(command),'args':args}}}
    def copy_client_setup(self):
        def go():
            value=self.client_setup();self.write(value)
            self.clipboard_clear();self.clipboard_append(json.dumps(value,ensure_ascii=False,indent=2))
            self.set_state('Local-client setup copied. Contains private machine paths; do not publish. No client or server was configured or started.')
        self.safe(go)
    def copy_context(self):
        def go():
            raw=json.dumps(self.service.context(),ensure_ascii=False,indent=2)
            self.write(json.loads(raw));self.clipboard_clear();self.clipboard_append(raw)
            self.set_state('Sanitized context copied. Nothing was sent to an AI service.')
        self.safe(go)
    def save_context(self):
        path=filedialog.asksaveasfilename(parent=self,title='Save a NEW AI context packet',defaultextension='.json')
        if path:self.safe(lambda:(json_new(Path(path),self.service.context()),
                           self.set_state('Sanitized packet saved locally. No upload or AI call.')))
    def import_request(self):
        path=filedialog.askopenfilename(parent=self,title='Choose a data-only AI request JSON',filetypes=[('JSON','*.json')])
        if not path:return
        def go():
            value=read_json(Path(path),32768)
            if not isinstance(value,dict) or set(value)!={'operation','arguments','request_id'}:
                raise ModError('INVALID_ARGUMENTS','Import only operation, arguments and request_id.')
            self.write(self.service.propose(**value));self.refresh()
            self.set_state('Proposal imported, not approved or executed.')
        self.safe(go)
    def share_report(self):
        path=filedialog.askopenfilename(parent=self,title='Choose an existing saved provider report',filetypes=[('Saved reports','*.json *.csv')])
        if not path:return
        if messagebox.askyesno('Share selected summary?',
            'Make ONLY provider metrics, definitions, sample coverage and the source hash available to the local AI interface?\n'
            'The original file, its path and raw settings are excluded. No network request is made.',parent=self):
            def go():
                self.write(self.service.share_report_local(Path(path)))
                self.set_state('Selected summary shared with the local interface; no external AI call.')
            self.safe(go)
    def share_tools(self):
        if messagebox.askyesno('Share tool status?',
            'Share only the known stock tool IDs, installed/running states, file versions and the original observation time?\n'
            'No paths, custom tools, settings, process IDs or sensor values are shared. No new provider query occurs.',parent=self):
            def go():
                self.write(self.service.share_tool_status_local(self.tool_snapshot()))
                self.set_state('Tool status summary shared locally. It is a saved observation, not live measurement.')
            self.safe(go)
    def approve(self):
        if self.busy or self.peer_busy():self.set_state('Another mod operation is active.');return
        def go():
            row=self.selected();self.write(row)
            if row['status']!='AWAITING_LOCAL_APPROVAL':
                self.set_state('This request is not pending; it will not be replayed.');return
            detail=json.dumps(row['arguments'],ensure_ascii=False,indent=2)
            if not messagebox.askyesno('Approve this exact action?',
                row['operation']+'\n\n'+detail+'\n\nDownload limit when applicable: 128 MiB, 40 requests, 300 seconds.\n'
                'No game, benchmark, recording, driver or input action.',parent=self):return
            self.set_state('Executing approved action; Stop requests cancellation at a safe boundary.')
            def work():
                try:result=self.service.approve_local(row['request_id'],row['request_sha256'],busy_guard=self.peer_busy)
                except Exception as error:result={'status':getattr(error,'code','UNKNOWN_EFFECTS_RECONCILE')}
                self.messages.put(result)
            self.service.cancel.clear()  # Before worker start, so a later Stop cannot be cleared by the worker.
            self.worker=threading.Thread(target=work,name='Hub-approved-automation',daemon=False)
            self.worker.start();self.schedule()
        self.safe(go)
    def reject(self):
        if self.busy:return
        def go():
            row=self.selected();self.write(self.service.reject_local(row['request_id'],row['request_sha256']));self.refresh()
        self.safe(go)
    def stop(self):
        self.service.stop();self.watch.set(False)
        self.set_state('Cancellation requested. Completed work is retained; no automatic resubmission.')
    def schedule(self):
        if self._poll is None and not self._closed:self._poll=self.after(200,self.poll)
    def toggle_watch(self):
        if self.watch.get():self.refresh();self.schedule()
    def poll(self):
        self._poll=None
        if self._closed:return
        try:
            while True:
                self.write(self.messages.get_nowait());self.refresh()
                self.set_state('Action returned. Review item statuses; a returned request is not proof of installation.')
        except queue.Empty:pass
        if self.watch.get():self.refresh()
        if self.busy or self.watch.get():self._poll=self.after(1000,self.poll)
    def can_close(self):
        if self.busy:self.stop();return False
        return True
    def close(self):
        self._closed=True;self.service.stop()
        if self._poll is not None:
            try:self.after_cancel(self._poll)
            except tk.TclError:pass
            self._poll=None
        self.layout.close();self.body.close()
    def _destroy(self,event):
        if event.widget is self and not self._closed:self.close()
