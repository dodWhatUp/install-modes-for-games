"""Presentation-only menus for maintained standalone apps; no operation owner."""
from __future__ import annotations
import json,os,uuid,weakref
from pathlib import Path
import tkinter as tk
from tkinter import ttk

VERSION='0.1.0'

def geometry(widget):
    manager=widget.winfo_manager()
    info=widget.pack_info() if manager=='pack' else widget.grid_info() if manager=='grid' else {}
    if manager=='pack':
        siblings=widget.master.pack_slaves();index=siblings.index(widget)
        if index+1<len(siblings):info['before']=siblings[index+1]
    return manager,{k:v for k,v in info.items() if k!='in'},info.get('in',widget.master)

def live_options(info):
    info=dict(info);before=info.get('before')
    if before is not None and (not before.winfo_exists() or before.winfo_manager()!='pack'):info.pop('before')
    return info

def restore(widget,record):
    manager,info,parent=record
    if manager=='pack':widget.pack(in_=parent,**live_options(info))
    elif manager=='grid':widget.grid(in_=parent,**info)

def hide(widget):
    if widget.winfo_manager()=='pack':widget.pack_forget()
    elif widget.winfo_manager()=='grid':widget.grid_remove()

class AppMenus:
    def __init__(self,parent,*,root,preference,title=None,original_controls=(),tools_menu=None,status=lambda value:None):
        self.root,self.parent,self.path,self.status=root,parent,Path(preference),status
        self.closed=False;self.job=None;self.fields=weakref.WeakKeyDictionary();self.groups=[]
        self.raw=self.path.read_bytes() if self.path.is_file() else None
        try:
            self.value=json.loads(self.raw) if self.raw else {'schema_version':1,'original_toolbar':False,'visibility':{}}
            if self.value.get('schema_version')!=1 or type(self.value.get('original_toolbar')) is not bool or type(self.value.get('visibility')) is not dict:raise ValueError()
            if not all(type(v) is bool for v in self.value['visibility'].values()):raise ValueError()
        except (ValueError,TypeError):
            self.value={'schema_version':1,'original_toolbar':False,'visibility':{}}
            self.status('Saved UI layout could not be read; using a session-only compact view.')
            self.raw=False
        self.original=tk.BooleanVar(root,self.value['original_toolbar'])
        self.legacy=[(widget,geometry(widget)) for widget in original_controls]
        self.title=title;self.title_font=title.cget('font') if title else None
        self.frame=ttk.Frame(parent);self.frame.pack(side='right',padx=(8,0))
        self.view=tk.Menu(root,tearoff=False);self.layout=tk.Menu(root,tearoff=False)
        self.tools=tools_menu or tk.Menu(root,tearoff=False)
        self.buttons={}
        ttk.Style(root).configure('AppChrome.TMenubutton',font=('Segoe UI',10),padding=(7,3))
        for label,menu in [('View',self.view),('Layout',self.layout),('Tools',self.tools)]:
            button=ttk.Menubutton(self.frame,text=label+' \u25be',menu=menu,style='AppChrome.TMenubutton')
            button.pack(side='left',padx=(4,0));self.buttons[label]=button
        self.layout.add_radiobutton(label='Compact toolbar',variable=self.original,value=False,command=self.changed)
        self.layout.add_radiobutton(label='Original toolbar',variable=self.original,value=True,command=self.changed)
        self.bindings=[(event,root.bind(event,callback,add='+')) for event,callback in
                       [('<Map>',self.mapped),('<Configure>',self.resized),('<Destroy>',self.destroyed)]]
        self.choice_binding=root.bind_class('TCombobox','<Map>',self.mapped,add='+')
        self.apply();self.queue()
    def save(self):
        try:
            if self.raw is False:raise ValueError('The previous UI file is preserved.')
            current=self.path.read_bytes() if self.path.exists() else None
            if current!=self.raw:raise ValueError('UI layout changed in another window; reopen before saving.')
            self.value['original_toolbar']=self.original.get()
            raw=(json.dumps(self.value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
            self.path.parent.mkdir(parents=True,exist_ok=True)
            temp=self.path.with_name(self.path.name+'.pending-'+uuid.uuid4().hex)
            try:
                with temp.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
                if (self.path.read_bytes() if self.path.exists() else None)!=current:raise ValueError('UI layout changed before saving.')
                os.replace(temp,self.path)
            finally:
                if temp.exists():temp.unlink()
            self.raw=raw
        except (ValueError,OSError) as error:self.status('UI choice is active for this session. '+str(error))
    def changed(self):self.apply();self.save()
    def apply(self):
        original=self.original.get()
        for widget,record in self.legacy:
            if not widget.winfo_exists():continue
            hide(widget)
            if original:restore(widget,record)
        if self.title:self.title.configure(font=self.title_font if original else ('Segoe UI',14,'bold'))
        for label in ('View','Tools'):
            hide(self.buttons[label])
            if not original:self.buttons[label].pack(side='left',padx=(4,0))
        # Keep the original button order when returning from the older toolbar.
        if not original:
            for label in ('View','Layout','Tools'):
                self.buttons[label].pack_forget();self.buttons[label].pack(side='left',padx=(4,0))
        self.queue()
    def visibility(self,label,widgets,key,default=True):
        widgets=list(widgets);records=[(w,geometry(w)) for w in widgets]
        variable=tk.BooleanVar(self.root,self.value['visibility'].get(key,default))
        def apply(save=True):
            for widget,record in records:
                if not widget.winfo_exists():continue
                hide(widget)
                if variable.get():restore(widget,record)
            self.value['visibility'][key]=variable.get()
            if save:self.save()
        self.view.add_checkbutton(label=label,variable=variable,command=apply)
        self.groups.append(variable);apply(False)
        return variable
    def checkbutton(self,label,variable,command):self.view.add_checkbutton(label=label,variable=variable,command=command)
    def mapped(self,event):
        if isinstance(event.widget,ttk.Combobox):self.queue()
    def resized(self,event):
        if event.widget is self.root:self.queue()
    def queue(self):
        if not self.closed and self.job is None:self.job=self.root.after_idle(self.fit)
    def fit(self):
        self.job=None
        if self.closed:return
        stack=[self.root]
        while stack:
            widget=stack.pop();stack.extend(widget.winfo_children())
            if not isinstance(widget,ttk.Combobox) or str(widget.cget('state'))!='normal':continue
            if widget not in self.fields:self.fields[widget]=(widget.cget('width'),geometry(widget))
            width,record=self.fields[widget]
            if self.original.get():
                widget.configure(width=width)
                if widget.winfo_manager()==record[0]:
                    if record[0]=='pack':widget.pack_configure(**live_options(record[1]))
                    elif record[0]=='grid':widget.grid_configure(**record[1])
            else:
                size=int(str(width));widget.configure(width=min(28,size) if size>0 else 28)
                if widget.winfo_manager()=='grid':widget.grid_configure(sticky='w')
                elif widget.winfo_manager()=='pack':widget.pack_configure(fill='none',expand=False,anchor='w')
    def destroyed(self,event):
        if event.widget is self.root:self.close()
    def close(self):
        if self.closed:return
        self.closed=True
        if self.job:
            try:self.root.after_cancel(self.job)
            except tk.TclError:pass
        for event,token in self.bindings:
            try:self.root.unbind(event,token)
            except tk.TclError:pass
        self.bindings=[]
        try:self.root._unbind(('bind','TCombobox','<Map>'),self.choice_binding)
        except tk.TclError:pass
