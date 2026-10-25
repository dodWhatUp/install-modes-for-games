"""Settings recovery UI for first open and an already-running controller."""
from pathlib import Path
import os,queue,threading,tkinter as tk
from tkinter import ttk,filedialog
from settings_locator import SettingsLocationError,resolve_settings,save_location,scan_settings

class SettingsLocationDialog(tk.Toplevel):
    def __init__(self,parent,workspace,report=None,on_selected=None,roots=None,startup=False,allow_external=True):
        super().__init__(parent);self.base=Path(workspace);self.roots=roots;self.on_selected=on_selected
        self.accepted=None;self.busy=False;self.events=queue.Queue();self.disposed=False
        self.allow_external=allow_external
        self.title('Mod Control - Find settings location');self.geometry('880x580');self.minsize(650,500)
        if not startup:self.transient(parent)
        body=ttk.Frame(self,padding=16);body.pack(fill='both',expand=True)
        ttk.Label(body,text='Find and repair the settings location',font=('Segoe UI',14,'bold')).pack(anchor='w')
        ttk.Label(body,text='The controller can rebuild its saved location from an existing valid render.cfg. Your game settings stay in place.',wraplength=800).pack(anchor='w',pady=(8,12))
        actions=ttk.Frame(body);actions.pack(fill='x')
        self.find_button=ttk.Button(actions,text='Find automatically',command=self.find);self.find_button.pack(side='left')
        self.use_button=ttk.Button(actions,text='Use selected file',command=self.use_selected);self.use_button.pack(side='left',padx=7)
        self.browse_button=ttk.Button(actions,text='Choose render.cfg...',command=self.browse);self.browse_button.pack(side='left')
        self.status=tk.StringVar();ttk.Label(body,textvariable=self.status,wraplength=800).pack(anchor='w',pady=10)
        listing=ttk.Frame(body);listing.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(listing,columns=('path','state'),show='headings',selectmode='browse',height=6)
        self.tree.heading('path',text='Detected file');self.tree.heading('state',text='Validation')
        self.tree.column('path',width=560,minwidth=300);self.tree.column('state',width=150,minwidth=100,stretch=False)
        scroll=ttk.Scrollbar(listing,command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right',fill='y');self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.selection)
        self.detail=tk.StringVar();ttk.Label(body,textvariable=self.detail,wraplength=800,style='Muted.TLabel').pack(anchor='w',pady=10)
        ttk.Label(body,text='If no native settings exist yet, open the game in Steam and complete its first setup, then choose Find automatically.',wraplength=800).pack(anchor='w',pady=(0,9))
        bottom=ttk.Frame(body);bottom.pack(fill='x')
        ttk.Button(bottom,text='Open game in Steam',command=self.open_steam).pack(side='left')
        ttk.Button(bottom,text='Close',command=self.close).pack(side='right')
        self.protocol('WM_DELETE_WINDOW',self.close)
        self.bind('<Destroy>',self.cleanup);self.after_id=self.after(80,self.drain)
        self.show_report(report if report is not None else scan_settings(self.base,self.roots))
        body.bind('<Configure>',lambda e:self.wrap_labels(body,e.width))
    @staticmethod
    def wrap_labels(body,width):
        for child in body.winfo_children():
            if isinstance(child,ttk.Label) and int(child.cget('wraplength') or 0)>0:child.configure(wraplength=max(240,width-40))
    def show_report(self,report):
        self.report=report;self.tree.delete(*self.tree.get_children())
        self.candidates=report.get('candidates',[])
        for index,c in enumerate(self.candidates):
            state=f"Valid: {c['width']} x {c['height']}" if c['valid'] else 'Needs review'
            self.tree.insert('', 'end',iid=str(index),values=(c['path'],state))
        state=report.get('status')
        self.status.set('Several different valid files were found. Select the one this game uses.' if state=='ambiguous' else
                        'No valid native settings were found yet. Search again or choose an existing file.' if state=='missing' else
                        'A valid settings location is available. Find automatically can rebuild its saved mapping.')
        self.use_button.configure(state='disabled');self.detail.set('Only the expected game settings locations are searched.')
    def selection(self,event=None):
        selected=self.tree.selection()
        if not selected:return
        c=self.candidates[int(selected[0])];self.detail.set(c['path']+'\n'+c['source']+(' | Verified native settings' if c['valid'] else ' | '+c.get('reason','Invalid file')))
        self.use_button.configure(state='normal' if c['valid'] and not self.busy else 'disabled')
    def run(self,fn):
        if self.busy:return
        self.busy=True;self.find_button.configure(state='disabled');self.use_button.configure(state='disabled');self.browse_button.configure(state='disabled');self.status.set('Checking settings locations...')
        def work():
            try:self.events.put((fn(),None))
            except Exception as e:self.events.put((None,e))
        threading.Thread(target=work,daemon=True).start()
    def find(self):self.run(lambda:resolve_settings(self.base,roots=self.roots))
    def use_selected(self):
        selected=self.tree.selection()
        if not selected:return
        c=self.candidates[int(selected[0])]
        if c['valid']:self.run(lambda:save_location(self.base,c['path']))
    def browse(self):
        path=filedialog.askopenfilename(parent=self,title='Choose the existing game render.cfg',filetypes=[('Shadow of War native settings','render.cfg')])
        if path:self.run(lambda:save_location(self.base,path))
    def drain(self):
        if self.disposed:return
        try:
            result,error=self.events.get_nowait();self.busy=False
            self.find_button.configure(state='normal');self.browse_button.configure(state='normal')
            if error:
                if isinstance(error,SettingsLocationError) and error.report:self.show_report(error.report)
                self.status.set(str(error));self.selection()
            else:
                self.accepted=Path(result['path']);callback=self.on_selected;self.destroy()
                if callback:callback(self.accepted)
                return
        except queue.Empty:pass
        self.after_id=self.after(80,self.drain)
    def open_steam(self):
        if os.name=='nt' and self.allow_external:os.startfile('steam://nav/games/details/356190')
        else:self.status.set('Steam opening is available in the Windows installation. No game was launched.')
    def close(self):
        if self.busy:return self.status.set('Wait for the current location check to finish.')
        self.destroy()
    def cleanup(self,event):
        if event.widget is self:
            self.disposed=True
            if self.after_id:
                try:self.after_cancel(self.after_id)
                except tk.TclError:pass

def startup_service(root,workspace,factory,roots=None):
    while True:
        try:return factory(workspace)
        except SettingsLocationError as error:
            root.withdraw();dialog=SettingsLocationDialog(root,workspace,error.report,roots=roots,startup=True)
            root.wait_window(dialog)
            if dialog.accepted is None:return None
            root.deiconify()
