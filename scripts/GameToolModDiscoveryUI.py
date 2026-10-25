"""Ranked local chooser; background inspection never connects a candidate."""
import queue,threading
import tkinter as tk
from tkinter import ttk
from GameToolFloatingWindows import show_near_pointer
from GameToolModDiscovery import ModDiscovery

class LocationChooser:
    def __init__(self,panel,*,discovery=None,auto_scan=True):
        self.panel=panel;self.game=panel.selected_game();self.discovery=discovery or ModDiscovery(panel.controls)
        self.window=tk.Toplevel(panel);self.window.title('Find '+self.game['name']);self.window.transient(panel.root)
        self.closed=False;self.generation=0;self.queue=queue.Queue();self.rows={};self.report=None;self.pending_poll=None
        body=ttk.Frame(self.window,padding=10);body.pack(fill='both',expand=True)
        self.state=tk.StringVar(self.window,value='Ready to inspect known local locations.')
        ttk.Label(body,text='Suggested locations',font=('Segoe UI',12,'bold')).pack(anchor='w')
        ttk.Label(body,textvariable=self.state,wraplength=680).pack(fill='x',pady=5)
        listing=ttk.Frame(body);listing.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(listing,columns=('rank','type','location'),show='headings',selectmode='browse',height=6)
        for name,label,width in [('rank','Match',100),('type','Found',150),('location','Game folder',410)]:
            self.tree.heading(name,text=label);self.tree.column(name,width=width,minwidth=70,stretch=name=='location')
        scroll=ttk.Scrollbar(listing,orient='vertical',command=self.tree.yview);self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
        self.tree.bind('<<TreeviewSelect>>',lambda _:self.selection())
        self.details=tk.Text(body,height=8,wrap='word',state='disabled',takefocus=True);self.details.pack(fill='both',expand=True,pady=6)
        ttk.Label(body,text='Scores describe location evidence. Mod compatibility and write access are checked separately.',wraplength=680).pack(fill='x')
        bar=ttk.Frame(body);bar.pack(fill='x',pady=(8,0))
        self.use=ttk.Button(bar,text='Use selected',command=lambda:panel.safe(self.use_selected),state='disabled');self.use.pack(side='left')
        self.refresh=ttk.Button(bar,text='Scan again',command=self.scan);self.refresh.pack(side='left',padx=5)
        browse=ttk.Menubutton(bar,text='Browse manually…');menu=tk.Menu(browse,tearoff=False);browse.configure(menu=menu)
        menu.add_command(label='Game folder…',command=lambda:panel.safe(lambda:self.manual(False)))
        if self.game['game_id']=='no-rest-for-the-wicked':menu.add_command(label='Prepared mod setup…',command=lambda:panel.safe(lambda:self.manual(True)))
        browse.pack(side='left');ttk.Button(bar,text='Close',command=self.close).pack(side='right')
        self.window.bind('<Escape>',lambda _:self.close());self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.window.minsize(570,420);self.window.bind('<Configure>',self.resize,add='+')
        show_near_pointer(self.window,panel.winfo_pointerxy(),(740,540))
        if auto_scan:self.scan()

    def resize(self,event):
        if event.widget is self.window:
            for child in self.window.winfo_children()[0].winfo_children():
                if isinstance(child,ttk.Label):child.configure(wraplength=max(420,event.width-30))

    def text(self,value):
        self.details.configure(state='normal');self.details.delete('1.0','end');self.details.insert('end',value);self.details.configure(state='disabled')

    def scan(self):
        self.generation+=1;generation=self.generation
        self.rows={};self.report=None
        for item in self.tree.get_children():self.tree.delete(item)
        self.use.state(['disabled']);self.refresh.state(['disabled']);self.state.set('Inspecting known local locations…');self.text('The scan only reads metadata and validates expected files.')
        def work():
            try:self.queue.put((generation,self.discovery.scan(self.game['game_id']),None))
            except Exception as error:self.queue.put((generation,None,str(error)))
        threading.Thread(target=work,daemon=True,name='ModLocationDiscovery').start();self.pending_poll=self.window.after(80,self.poll)

    def poll(self):
        self.pending_poll=None
        if self.closed:return
        try:generation,report,error=self.queue.get_nowait()
        except queue.Empty:self.pending_poll=self.window.after(80,self.poll);return
        if generation!=self.generation:self.pending_poll=self.window.after(80,self.poll);return
        self.refresh.state(['!disabled'])
        if error:self.state.set('Scan could not finish. Browse manually or scan again.');self.text(error);return
        self.present(report)

    def present(self,report):
        self.report=report;self.rows={}
        for item in self.tree.get_children():self.tree.delete(item)
        for i,row in enumerate(report['candidates']):
            ident=str(i);self.rows[ident]=row
            self.tree.insert('', 'end',iid=ident,values=(f"{row['confidence']} · {row['score']}/100",row['kind'],row['game_dir']))
        self.state.set(f"{len(self.rows)} location(s) found. Select one to review, then choose Use selected." if self.rows else 'No verified match found. Use Browse manually to select a location.')
        if self.rows:self.tree.selection_set('0');self.tree.focus('0');self.selection()
        else:self.use.state(['disabled']);self.text(report['scope']+'\n\n'+'\n'.join(report['warnings']))

    def selection(self):
        selected=self.tree.selection();row=self.rows.get(selected[0]) if selected else None
        self.use.state(['!disabled'] if row and row['selectable'] else ['disabled'])
        if row:
            parts=['Game: '+row['game_dir'],'Executable: '+'\n'.join(row['executables'])]
            if row.get('workspace'):parts.append('Prepared setup: '+row['workspace'])
            parts.extend(['','Why this match:']+['• '+reason for reason in row['reasons']])
            if row['issues']:parts.extend(['','File conflicts need review:']+row['issues'])
            if self.report and self.report['warnings']:parts.extend(['','Other scan notes:']+self.report['warnings'])
            self.text('\n'.join(parts))

    def use_selected(self):
        selected=self.tree.selection()
        if not selected or selected[0] not in self.rows:return
        row=self.discovery.revalidate(self.rows[selected[0]])
        connected=self.panel.use_discovered(row)
        # A cancelled ownership dialog leaves the chooser available.
        if connected:self.close()

    def manual(self,prepared):
        if self.panel.selected_game()['game_id']!=self.game['game_id']:
            from game_mod_ops.safety import ModError
            raise ModError('DISCOVERY_CONTEXT_CHANGED','The selected game changed. Close this chooser and open it again.')
        if prepared:self.panel.connect_prepared()
        else:self.panel.register()

    def close(self):
        if self.closed:return
        self.closed=True;self.generation+=1
        if self.pending_poll:self.window.after_cancel(self.pending_poll);self.pending_poll=None
        self.window.destroy()
