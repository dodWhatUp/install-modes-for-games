"""Compact alternate-look editor; image preparation never blocks live polling."""
from __future__ import annotations
import copy
import queue
import threading
import tkinter as tk
from tkinter import ttk
import GameToolOverlay as api
import GameToolOverlayAlternate as alternate
import GameToolOverlayAppearance as looks
from GameToolKeyCapture import CaptureDialog

VERSION='0.1.1'


class AlternateEditor:
    def __init__(self,parent,store,on_save=lambda:None):
        self.store,self.on_save=store,on_save
        self.value,self.expected=alternate.read(store.directory);self.registry,_=store.load()
        self.policy=looks.policy(self.registry);self.targets={};self.busy=False;self.closed=False
        self.events=queue.Queue();self.cancelled=threading.Event()
        self.window=tk.Toplevel(parent);self.window.title('Alternate overlay view — double press / combination')
        self.window.geometry(f"{min(700,parent.winfo_screenwidth()-80)}x{min(560,parent.winfo_screenheight()-100)}")
        self.window.minsize(440,360)
        footer=ttk.Frame(self.window,padding=12);footer.pack(side='bottom',fill='x');footer.columnconfigure(1,weight=1)
        region=ttk.Frame(self.window);region.pack(fill='both',expand=True);region.columnconfigure(0,weight=1);region.rowconfigure(0,weight=1)
        canvas=tk.Canvas(region,highlightthickness=0);canvas.grid(row=0,column=0,sticky='nsew')
        scroll=ttk.Scrollbar(region,orient='vertical',command=canvas.yview);scroll.grid(row=0,column=1,sticky='ns');canvas.configure(yscrollcommand=scroll.set)
        body=ttk.Frame(canvas,padding=14);body.columnconfigure(1,weight=1);item=canvas.create_window(0,0,anchor='nw',window=body)
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
        def layout(_=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            for child in body.winfo_children():
                if isinstance(child,ttk.Label) and int(child.cget('wraplength') or 0):child.configure(wraplength=max(300,body.winfo_width()-34))
        body.bind('<Configure>',layout)
        self.scopes={'Global defaults':None};self.scopes.update({g['label']+' ['+g['id']+']':g['id'] for g in self.registry['manifest']['games']})
        ttk.Label(body,text='Save settings for').grid(row=0,column=0,sticky='w',padx=(0,10))
        self.scope=tk.StringVar(self.window,value='Global defaults')
        self.scope_box=ttk.Combobox(body,state='readonly',textvariable=self.scope,values=list(self.scopes),width=56)
        self.scope_box.grid(row=0,column=1,sticky='ew');self.scope_box.bind('<<ComboboxSelected>>',lambda _:self.load_scope())
        self.inherit=tk.BooleanVar(self.window)
        self.inherit_box=ttk.Checkbutton(body,text='Use global alternate settings for this game',variable=self.inherit,command=self.refresh)
        self.inherit_box.grid(row=1,column=1,sticky='w',pady=6)
        self.enabled=tk.BooleanVar(self.window);self.double=tk.BooleanVar(self.window)
        self.enabled_box=ttk.Checkbutton(body,text='Enable alternate overlay view',variable=self.enabled)
        self.enabled_box.grid(row=3,column=0,columnspan=2,sticky='w',pady=5)
        self.double_box=ttk.Checkbutton(body,text='Double press the existing picture button (#19)',variable=self.double)
        self.double_box.grid(row=4,column=0,columnspan=2,sticky='w')
        ttk.Label(body,text='Double-press window (ms)').grid(row=5,column=0,sticky='w',pady=7)
        self.window_ms=tk.StringVar(self.window)
        self.speed=ttk.Spinbox(body,from_=150,to=600,increment=25,textvariable=self.window_ms,width=8)
        self.speed.grid(row=5,column=1,sticky='w')
        ttk.Label(body,text='300 ms default · 150–600 ms · first press remains immediate',wraplength=570).grid(row=6,column=0,columnspan=2,sticky='w')
        ttk.Label(body,text='After double press').grid(row=7,column=0,sticky='w',pady=7)
        self.behavior=tk.StringVar(self.window)
        self.behaviors={'Hold second press; release hides':'hold','Toggle look; picture button controls visibility':'toggle'}
        self.behavior_box=ttk.Combobox(body,state='readonly',textvariable=self.behavior,values=list(self.behaviors),width=48)
        self.behavior_box.grid(row=7,column=1,sticky='ew')
        ttk.Label(body,text='Held combination (optional)').grid(row=8,column=0,sticky='w',pady=7)
        inputs=ttk.Frame(body);inputs.grid(row=8,column=1,sticky='ew')
        self.chord=[];self.chord_boxes=[]
        for n in range(4):
            v=tk.StringVar(self.window);self.chord.append(v)
            box=ttk.Combobox(inputs,textvariable=v,values=['']+list(alternate.KEYS),width=13);box.grid(row=n//2,column=n%2,padx=(0,4),pady=2,sticky='ew');self.chord_boxes.append(box)
        self.capture_button=ttk.Button(inputs,text='Capture keyboard…',command=self.capture);self.capture_button.grid(row=2,column=0,columnspan=2,sticky='w',pady=5)
        ttk.Label(body,text='Choose 2–4 buttons, including Mouse Left/Right/Middle/Back/Forward. The combination shows the alternate while held. Inputs pass through; release returns to the normal look if another show button is still held.',wraplength=590).grid(row=9,column=0,columnspan=2,sticky='w',pady=(0,8))
        ttk.Label(body,text='Alternate look').grid(row=2,column=0,sticky='w',pady=6)
        self.target=tk.StringVar(self.window)
        self.target_box=ttk.Combobox(body,state='readonly',textvariable=self.target,width=52);self.target_box.grid(row=2,column=1,sticky='ew',pady=6)
        ttk.Label(body,text='Saved appearance presets are copied as snapshots. Save a preset in Appearance & presets first. The current game/layer/context remains selected.',wraplength=590).grid(row=10,column=0,columnspan=2,sticky='w',pady=8)
        self.message=tk.StringVar(self.window,value='Changes apply only when saved. Existing game/native keys stay unchanged.')
        ttk.Label(footer,textvariable=self.message,wraplength=580).grid(row=0,column=0,columnspan=2,sticky='w',pady=(0,8))
        self.save_button=ttk.Button(footer,text='Save alternate settings',command=self.commit);self.save_button.grid(row=1,column=1,sticky='e')
        self.cancel_button=ttk.Button(footer,text='Close',command=self.close);self.cancel_button.grid(row=1,column=0,sticky='w')
        self.window.protocol('WM_DELETE_WINDOW',self.close);self.window.bind('<Escape>',lambda _:self.close())
        self.load_scope()

    def load_scope(self):
        scope=self.scopes[self.scope.get()];setting=alternate.effective(self.value,scope)
        self.inherit.set(scope is not None and scope not in self.value['games'])
        self.enabled.set(setting['enabled']);self.double.set(setting['double_press']);self.window_ms.set(str(setting['window_ms']))
        self.behavior.set(next(n for n,v in self.behaviors.items() if v==setting['behavior']))
        reverse={v:k for k,v in alternate.KEYS.items()}
        for n,v in enumerate(self.chord):v.set(reverse[setting['chord'][n]] if n<len(setting['chord']) else '')
        self.targets={label:dict(kind='view',view=view) for view,label in api.VIEW_CHOICES}
        for pid,preset in self.policy['presets'].items():
            if preset['scope'] is None or preset['scope']==scope:
                label=('Global preset: ' if preset['scope'] is None else 'Game preset: ')+preset['name']+' ['+pid+']'
                self.targets[label]=dict(kind='preset',name=preset['name'],style=copy.deepcopy(preset['style']))
        selected=next((name for name,target in self.targets.items() if target==setting['target']),None)
        if selected is None:selected='Saved snapshot: '+setting['target'].get('name','alternate');self.targets[selected]=copy.deepcopy(setting['target'])
        self.target_box.configure(values=list(self.targets));self.target.set(selected);self.refresh()

    def refresh(self):
        global_scope=self.scopes[self.scope.get()] is None
        self.inherit_box.configure(state='disabled' if global_scope or self.busy else 'normal')
        state='disabled' if self.busy or (not global_scope and self.inherit.get()) else 'normal'
        for widget in [self.enabled_box,self.double_box,self.speed,self.capture_button,*self.chord_boxes]:widget.configure(state=state)
        for widget in (self.behavior_box,self.target_box):widget.configure(state='readonly' if state=='normal' else 'disabled')
        self.scope_box.configure(state='disabled' if self.busy else 'readonly')
        self.save_button.configure(state='disabled' if self.busy else 'normal')
        self.cancel_button.configure(text='Cancel preparation' if self.busy else 'Close')

    def capture(self):
        def use(label):
            keys=label.split('+');api.require(all(k in alternate.KEYS for k in keys),'Use the combination lists for this key')
            for n,v in enumerate(self.chord):v.set(keys[n] if n<len(keys) else '')
        return CaptureDialog(self.window,lambda label:self.guard(lambda:use(label)))

    def guard(self,fn):
        try:return fn()
        except (ValueError,OSError,KeyError) as error:self.message.set(str(error))

    def candidate(self):
        candidate=copy.deepcopy(self.value);scope=self.scopes[self.scope.get()]
        if scope is not None and self.inherit.get():candidate['games'].pop(scope,None)
        else:
            names=[v.get().strip() for v in self.chord if v.get().strip()]
            api.require(all(k in alternate.KEYS for k in names),'Choose combination buttons from the lists')
            setting=dict(enabled=self.enabled.get(),double_press=self.double.get(),window_ms=int(self.window_ms.get()),behavior=self.behaviors[self.behavior.get()],chord=[alternate.KEYS[n] for n in names],target=copy.deepcopy(self.targets[self.target.get()]))
            alternate.validate_rule(setting)
            if scope is None:candidate['global_rule']=setting
            else:candidate['games'][scope]=setting
        return alternate.validate(candidate)

    def commit(self):
        if self.busy:return
        candidate=self.guard(self.candidate)
        if candidate is None:return
        self.busy=True;self.cancelled.clear();self.refresh();self.message.set('Preparing alternate images… Normal overlay remains active.')
        def worker():
            try:self.events.put(('done',alternate.save(self.store,candidate,self.expected,lambda text:self.events.put(('progress',text)),self.cancelled.is_set)))
            except Exception as error:self.events.put(('error',str(error)))
        threading.Thread(target=worker,daemon=True).start();self.window.after(40,self.poll)

    def poll(self):
        if self.closed:return
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='progress':self.message.set(value)
                else:
                    self.busy=False;self.refresh()
                    if kind=='done':self.value,self.expected=value;self.message.set('Alternate settings saved. Normal appearance unchanged.');self.on_save()
                    else:self.message.set(value)
                    return
        except queue.Empty:self.window.after(40,self.poll)

    def close(self):
        if self.busy:self.cancelled.set();self.message.set('Cancelling before settings commit…');return
        self.closed=True;self.window.destroy()
