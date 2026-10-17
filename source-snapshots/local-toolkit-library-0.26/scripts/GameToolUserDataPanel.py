"""Explicit private export/import/migration view; never applies active profiles."""
from __future__ import annotations
import json
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from GameToolCompactUI import ScrollableFrame

VERSION = "0.1.1"
MODES = ("Export selected files", "Inspect / restore backup", "Inspect / migrate record")

class UserDataPanel:
    def __init__(self, parent, api, status, app_version=None):
        self.scroll = ScrollableFrame(parent)
        self.scroll.pack(fill="both",expand=True)
        parent = self.scroll.body
        self.parent, self.root, self.api, self.status = parent, parent.winfo_toplevel(), api, status
        self.app_version = app_version
        self.selections = []; self.preview = None; self.busy = False; self.closed = False
        self.messages = queue.Queue()
        self.mode = tk.StringVar(value=MODES[0]); self.source = tk.StringVar()
        self.logical = tk.StringVar(); self.destination = tk.StringVar(); self.expected = tk.StringVar()
        self.format = tk.StringVar(value="opaque")
        ttk.Label(parent, text="User data · separate from program versions", font=("Segoe UI",14,"bold")).pack(anchor="w")
        ttk.Label(parent, text="Private backups preserve exact selected bytes. Supported record formats migrate to a new copy; native profiles are not converted or activated. No network sync or cloud upload.", wraplength=750).pack(anchor="w",pady=6)
        self.mode_control = ttk.Combobox(parent,textvariable=self.mode,values=MODES,state="readonly")
        self.mode_control.pack(fill="x",pady=(0,6)); self.mode_control.bind("<<ComboboxSelected>>",self.mode_changed)
        form=ttk.Frame(parent); form.pack(fill="x"); form.columnconfigure(1,weight=1)
        self.source_label=ttk.Label(form,text="Selected source file"); self.source_label.grid(row=0,column=0,sticky="w")
        self.source_control=ttk.Combobox(form,textvariable=self.source); self.source_control.grid(row=0,column=1,sticky="ew",padx=8,pady=3)
        ttk.Button(form,text="…",width=3,command=self.browse_source).grid(row=0,column=2)
        self.logical_label=ttk.Label(form,text="Portable name"); self.logical_label.grid(row=1,column=0,sticky="w")
        self.logical_control=ttk.Entry(form,textvariable=self.logical); self.logical_control.grid(row=1,column=1,sticky="ew",padx=8,pady=3)
        self.format_control=ttk.Combobox(form,textvariable=self.format,values=("opaque","envelope"),state="readonly",width=12)
        self.format_control.grid(row=1,column=2)
        self.sha_label=ttk.Label(form,text="Expected ZIP SHA-256")
        self.sha_control=ttk.Entry(form,textvariable=self.expected)
        self.sha_label.grid(row=2,column=0,sticky="w"); self.sha_control.grid(row=2,column=1,columnspan=2,sticky="ew",padx=8,pady=3)
        self.dest_label=ttk.Label(form,text="New ZIP path"); self.dest_label.grid(row=3,column=0,sticky="w")
        ttk.Combobox(form,textvariable=self.destination).grid(row=3,column=1,columnspan=2,sticky="ew",padx=8,pady=3)
        self.selection_bar=ttk.Frame(parent); self.selection_bar.pack(fill="x",pady=5)
        ttk.Button(self.selection_bar,text="Add selected file",command=self.add_file).pack(side="left")
        ttk.Button(self.selection_bar,text="Remove from list",command=self.remove_file).pack(side="left",padx=6)
        self.table=ttk.Treeview(parent,columns=("name","format"),show="headings",height=4,selectmode="browse")
        for key,label in (("name","Portable name · only listed files are exported"),("format","Format")):
            self.table.heading(key,text=label)
        self.table.column("name",width=430,minwidth=180); self.table.column("format",width=90,stretch=False)
        self.table.pack(fill="x",pady=4)
        bar=ttk.Frame(parent); bar.pack(fill="x",pady=5)
        self.inspect_button=ttk.Button(bar,text="Preview selected export",command=self.inspect); self.inspect_button.pack(side="left")
        self.commit_button=ttk.Button(bar,text="Create private ZIP",command=self.commit,state="disabled"); self.commit_button.pack(side="left",padx=6)
        self.details=tk.Text(parent,wrap="word",height=7,font=("Segoe UI",10)); self.details.pack(fill="both",expand=True)
        self.display("Nothing selected. Existing data remains in its original location. Restore is evidence-only into a NEW directory; it never replaces or activates current settings. Future formats stay read-only.")
        self.mode_changed(); self.timer=self.root.after(100,self.tick)

    def display(self,text):
        self.details.configure(state="normal"); self.details.delete("1.0","end"); self.details.insert("1.0",text); self.details.configure(state="disabled")

    def notice(self,text):
        self.status.set(text) if hasattr(self.status,"set") else self.status(text)

    def signature(self):
        return (self.mode.get(),self.source.get(),self.logical.get(),self.format.get(),self.expected.get(),self.destination.get(),json.dumps(self.selections,sort_keys=True))

    def mode_changed(self,*_):
        self.preview=None; self.commit_button.configure(state="disabled")
        export=self.mode.get()==MODES[0]; restore=self.mode.get()==MODES[1]
        for widget in (self.logical_label,self.logical_control,self.format_control):
            widget.grid() if export else widget.grid_remove()
        for widget in (self.sha_label,self.sha_control):
            widget.grid() if restore else widget.grid_remove()
        if export:
            self.table.pack(before=self.inspect_button.master,fill="x",pady=4); self.selection_bar.pack(before=self.table,fill="x",pady=5)
        else:
            self.selection_bar.pack_forget(); self.table.pack_forget()
        self.source_label.configure(text="Selected source file" if export else "Private backup ZIP" if restore else "Shared-envelope JSON")
        self.dest_label.configure(text="New ZIP path" if export else "NEW restore directory" if restore else "NEW migrated JSON path")
        self.inspect_button.configure(text="Preview selected export" if export else "Inspect backup" if restore else "Preview migration")
        self.commit_button.configure(text="Create private ZIP" if export else "Restore NEW copy" if restore else "Save migrated NEW copy")

    def browse_source(self):
        if self.busy or self.closed:return
        path=filedialog.askopenfilename(parent=self.root,title="Select one explicit private source")
        if path:
            self.source.set(path)
            if self.mode.get()==MODES[0] and not self.logical.get():self.logical.set(Path(path).name)

    def add_file(self):
        if self.busy or self.closed:return
        row={"path":self.source.get(),"logical_path":self.logical.get(),"format":self.format.get()}
        if not row["path"] or not row["logical_path"]:self.notice("Enter a source and portable name first.");return
        if len(self.selections)>=self.api.MAX_FILES:self.notice("Selected-file limit reached.");return
        self.selections.append(row); self.table.insert("","end",values=(row["logical_path"],row["format"]))
        self.preview=None; self.commit_button.configure(state="disabled")

    def remove_file(self):
        if self.busy or self.closed:return
        selected=self.table.selection()
        if selected:
            index=self.table.index(selected[0]);self.selections.pop(index);self.table.delete(selected[0])
            self.preview=None;self.commit_button.configure(state="disabled")

    def work(self,operation,done):
        if self.busy or self.closed:return
        self.busy=True;self.inspect_button.configure(state="disabled");self.commit_button.configure(state="disabled")
        self.notice("Checking selected private files…")
        def run():
            try:self.messages.put((True,operation(),done))
            except Exception as e:self.messages.put((False,str(e),done))
        threading.Thread(target=run,daemon=True).start()

    def inspect(self):
        if self.busy or self.closed:return
        signature=self.signature(); mode,source,_,_,expected,_,_=signature
        selections=[dict(row) for row in self.selections]
        self.preview=None
        def operation():
            if mode==MODES[0]:return self.api.preview_export(selections,app_version=self.app_version)
            if mode==MODES[1]:return self.api.inspect_archive(Path(source),expected.strip() or None)
            return self.api.inspect_envelope(Path(source))
        def done(value):
            if signature!=self.signature():self.notice("Fields changed during inspection; inspect again.");return
            self.preview={"signature":signature,"result":value}
            ready=not value.get("read_only",False)
            self.commit_button.configure(state="normal" if ready else "disabled")
            lines=[value["state"],f"Files: {value.get('files','one shared record')} · bytes: {value.get('bytes','schema preview')}"]
            if mode==MODES[0]:lines += [row["logical_path"]+" · "+row["sha256"] for row in value["manifest"]["files"]]
            if mode==MODES[1]:lines += ["Archive SHA-256: "+value["archive_sha256"],"Restore unchanged bytes into a new folder only.","Recognized record migration previews: "+str(len(value["migrations"]))]
            if mode==MODES[2]:lines += ["Source SHA-256: "+value["file_sha256"],"Automatic supported conversion preview:",json.dumps(value["changes"],ensure_ascii=False)]
            lines += ["No original changed. No upload or automatic profile activation."]
            self.display("\n".join(lines));self.notice("Private data inspected; review before creating a new copy.")
        self.work(operation,done)

    def commit(self):
        if self.busy or self.closed:return
        if not self.preview or self.preview["signature"]!=self.signature():self.notice("Inspect these exact selections and paths first.");return
        mode,source,_,_,_,destination,_=self.preview["signature"];value=self.preview["result"]
        if value.get("read_only"):self.notice("Future data format is read-only.");return
        if not messagebox.askyesno("Create a new private copy", "Create the reviewed NEW copy at the entered destination? Existing files and active profiles will not be replaced. This is not cloud synchronization.",parent=self.root):return
        if self.closed or self.busy or not self.preview or self.preview["signature"]!=self.signature():
            self.notice("Selections changed during confirmation; inspect again.");return
        def operation():
            if mode==MODES[0]:return self.api.export_archive(Path(destination),value)
            if mode==MODES[1]:return self.api.restore_new_copy(Path(source),Path(destination),value["archive_sha256"],value["preview_sha256"])
            return self.api.save_migrated_copy(Path(source),Path(destination),value["file_sha256"],value["preview_sha256"])
        def done(receipt):
            self.preview=None;self.display(json.dumps(receipt,indent=2,ensure_ascii=False));self.notice("Verified new private copy created; existing profiles remain unchanged.")
        self.work(operation,done)

    def tick(self):
        if self.closed:return
        try:
            ok,value,done=self.messages.get_nowait();self.busy=False;self.inspect_button.configure(state="normal")
            if ok:done(value)
            else:self.preview=None;self.display(value);self.notice("Private data operation blocked: "+value)
        except queue.Empty:pass
        self.timer=self.root.after(100,self.tick)

    def close(self):
        if self.busy:return False
        self.closed=True;self.root.after_cancel(self.timer);self.scroll.close();return True
