"""Editable Tk choice lists that keep the caret while suggestions are open.

Presentation only: existing variables, validation, selection events and explicit
Add/Save actions retain ownership. No grab, global OS input hook or file writes.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, font

VERSION = "0.1.2"

def tab_events(window_system):
    # ISO_Left_Tab is an X11 keysym; Windows Tk rejects it during binding.
    return ('<Tab>','<Shift-Tab>')+(('<ISO_Left_Tab>',)if window_system=='x11'else())

class EditableList:
    def __init__(self,widget,owner):
        self.widget,self.owner=widget,owner;self.popup=None;self.listbox=None
        self.visible=False;self.rows=[];self.job=None;self.refresh_job=None;self.original='';self.show_all=True
        self.tag='GameToolsEditable'+str(id(self))
        widget.bindtags((self.tag,*widget.bindtags()))
        for event,callback in (('<ButtonPress-1>',self.click),('<Down>',lambda e:self.move(1)),
          ('<Up>',lambda e:self.move(-1)),('<Alt-Down>',self.toggle),('<F4>',self.toggle),
          ('<Return>',self.enter),('<KP_Enter>',self.enter),('<Escape>',self.escape),
          ('<KeyRelease>',self.typed),
          ('<<Paste>>',self.paste),('<Unmap>',lambda e:self.hide()),('<Destroy>',self.destroy)):
            widget.bind_class(self.tag,event,callback)
        for event in tab_events(str(widget.tk.call('tk','windowingsystem'))):
            widget.bind_class(self.tag,event,self.tab)
        variable=str(widget.cget('textvariable'))
        # Do not wrap another owner's variable in StringVar: its destructor
        # would unset that shared value when a transient field is destroyed.
        self.owned_variable=None
        if not variable:
            self.owned_variable=tk.StringVar(widget,value=widget.get());variable=str(self.owned_variable)
            widget.configure(textvariable=variable)
        self.variable_name=variable;self.trace=widget.register(self.changed)
        widget.tk.call('trace','add','variable',variable,'write',self.trace)
        widget.game_tools_editable_list=self
    def editable(self):return self.widget.winfo_exists()and not self.widget.instate(['disabled'])and str(self.widget.cget('state'))=='normal'
    def click(self,event):
        if not self.editable():return
        if 'arrow'in self.widget.identify(event.x,event.y):
            return self.toggle(event)
        self.widget.after_idle(self.open)
        # Native entry binding still positions the caret / selects text.
    def toggle(self,*_):
        if not self.editable():return
        if self.visible:self.hide()
        else:self.open()
        return 'break'
    def open(self,all_values=True):
        if not self.editable()or not self.widget.winfo_viewable():return
        if self.visible:return
        if self.owner.active and self.owner.active is not self:self.owner.active.hide()
        self.owner.active=self;self.original=self.widget.get();self.show_all=all_values
        if self.popup is None:
            self.popup=tk.Toplevel(self.widget,takefocus=False);self.popup.withdraw()
            self.popup.overrideredirect(True);self.popup.transient(self.widget.winfo_toplevel())
            frame=ttk.Frame(self.popup,borderwidth=1,relief='solid');frame.pack(fill='both',expand=True)
            self.listbox=tk.Listbox(frame,exportselection=False,activestyle='dotbox',takefocus=False,
              relief='flat',borderwidth=0,highlightthickness=0,font=self.widget.cget('font'))
            scroll=ttk.Scrollbar(frame,orient='vertical',command=self.listbox.yview,takefocus=False)
            self.listbox.configure(yscrollcommand=scroll.set);self.listbox.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y')
            self.listbox.bind('<ButtonPress-1>',self.pick)
            self.listbox.bind('<Motion>',self.hover)
            self.popup.bind('<FocusOut>',lambda e:self.widget.after_idle(self.check_focus))
        self.visible=True;self.refresh();self.popup.deiconify();self.popup.lift()
        self.widget.focus_set()
        self.schedule()
    def schedule(self):
        if self.job is None and self.visible:self.job=self.widget.after(120,self.poll)
    def poll(self):
        self.job=None
        if self.visible:
            if not self.editable()or not self.widget.winfo_viewable():self.hide();return
            self.refresh();self.schedule()
    def refresh(self):
        if not self.visible:return
        values=[str(v)for v in self.widget.cget('values')]
        query=''if self.show_all else self.widget.get().casefold()
        rows=[v for v in values if query in v.casefold()]
        if rows!=self.rows or self.listbox.size()==0:
            self.rows=rows;self.listbox.delete(0,'end')
            for value in rows:self.listbox.insert('end',value)
            if not rows:self.listbox.insert('end','No matches — keep typing')
            current=self.widget.get()
            if current in rows:self.highlight(rows.index(current))
            elif len(rows)==1:self.highlight(0)
        f=font.Font(root=self.widget,font=self.widget.cget('font'));line=max(18,f.metrics('linespace')+5)
        vx,vy=self.widget.winfo_vrootx(),self.widget.winfo_vrooty()
        sw,sh=self.widget.winfo_vrootwidth(),self.widget.winfo_vrootheight()
        x,y=self.widget.winfo_rootx(),self.widget.winfo_rooty();bottom=y+self.widget.winfo_height()
        below=max(0,vy+sh-bottom);above=max(0,y-vy)
        count=min(8,max(1,len(rows)));desired=count*line+4
        space=below if desired<=below or below>=above else above
        height=max(20,min(desired,space));width=min(max(self.widget.winfo_width(),230),sw)
        x=max(vx,min(x,vx+sw-width));y=bottom if space==below else y-height
        self.popup.geometry(f'{width}x{height}+{x}+{max(vy,y)}')
    def changed(self,*_):
        if self.visible:
            self.show_all=False
            if self.refresh_job is None:self.refresh_job=self.widget.after_idle(self.refresh_after_edit)
    def refresh_after_edit(self):
        self.refresh_job=None;self.refresh()
    def typed(self,event):
        if not self.editable():return
        if event.keysym in {'Escape','Return','KP_Enter','Tab','ISO_Left_Tab','Up','Down','F4'}:return
        if ((len(event.keysym)==1 or getattr(event,'char','')and event.char.isprintable())and not event.state&0x0c)or event.keysym in {'BackSpace','Delete'}:
            if not self.visible:self.open(False)
            self.show_all=False;self.refresh()
    def paste(self,event):
        if self.editable():self.widget.after_idle(lambda:self.open(False))
    def highlight(self,index):
        if self.rows:
            self.listbox.selection_clear(0,'end');self.listbox.selection_set(index)
            self.listbox.activate(index);self.listbox.see(index)
    def move(self,step):
        if not self.editable():return
        if not self.visible:self.open()
        self.refresh()
        selected=self.listbox.curselection()
        index=(selected[0]+step)if selected else(0 if step>0 else len(self.rows)-1)
        self.highlight(max(0,min(len(self.rows)-1,index)))
        return 'break'
    def hover(self,event):
        if self.rows:self.highlight(self.listbox.nearest(event.y))
    def pick(self,event):
        if self.rows:
            self.highlight(self.listbox.nearest(event.y));self.choose()
        return 'break'
    def enter(self,event):
        if self.visible and self.listbox.curselection()and self.rows:
            self.choose();return 'break'
        self.hide()
    def choose(self):
        index=self.listbox.curselection()
        if not index or not self.editable():self.hide();return
        value=self.rows[index[0]];self.hide();self.widget.set(value)
        self.widget.icursor('end');self.widget.focus_set()
        self.widget.event_generate('<<ComboboxSelected>>',when='tail')
    def escape(self,event):
        if self.visible:
            original=self.original;self.hide();self.widget.set(original)
        # Selector's existing Escape also restores its stable committed ID.
    def tab(self,event):self.hide()
    def check_focus(self):
        if not self.visible:return
        # Native readonly popdowns are Tcl widgets without a Python object.
        # Query their Tk name directly instead of focus_get()/nametowidget().
        focus=str(self.widget.tk.call('focus'))
        if focus!=str(self.widget)and not(focus and focus.startswith(str(self.popup)+'.')):self.hide()
    def hide(self):
        self.visible=False
        if self.job is not None:
            try:self.widget.after_cancel(self.job)
            except tk.TclError:pass
            self.job=None
        if self.refresh_job is not None:
            try:self.widget.after_cancel(self.refresh_job)
            except tk.TclError:pass
            self.refresh_job=None
        if self.popup is not None:
            try:self.popup.withdraw()
            except tk.TclError:pass
        if self.owner.active is self:self.owner.active=None
    def destroy(self,event):
        if event.widget is not self.widget:return
        self.hide()
        try:self.widget.tk.call('trace','remove','variable',self.variable_name,'write',self.trace)
        except tk.TclError:pass
        for sequence in self.widget.bind_class(self.tag):self.widget.unbind_class(self.tag,sequence)

class ListBehavior:
    def __init__(self,root):
        self.root=root;self.active=None
        root.bind_class('TCombobox','<Map>',self.mapped,add='+')
        root.bind_all('<ButtonPress-1>',self.outside,add='+')
        root.bind_all('<FocusIn>',self.focus,add='+')
        root.bind_all('<FocusOut>',self.focus_out,add='+')
        root.bind_all('<Configure>',self.configured,add='+')
        self.scan(root)
    def attach(self,widget):
        if not hasattr(widget,'game_tools_editable_list'):EditableList(widget,self)
        return widget.game_tools_editable_list
    def scan(self,parent):
        if isinstance(parent,ttk.Combobox):self.attach(parent)
        for child in parent.winfo_children():self.scan(child)
    def mapped(self,event):
        if isinstance(event.widget,ttk.Combobox):self.attach(event.widget)
    def outside(self,event):
        active=self.active
        if active and event.widget is not active.widget and not str(event.widget).startswith(str(active.popup)+'.'):active.hide()
    def focus(self,event):
        if self.active:self.active.check_focus()
    def focus_out(self,event):
        active=self.active
        if active:
            def check():
                if active.visible and not active.widget.tk.call('focus','-displayof',str(active.widget)):active.hide()
                elif active.visible:active.check_focus()
            active.widget.after_idle(check)
    def configured(self,event):
        if self.active and event.widget is self.active.widget.winfo_toplevel():self.active.hide()

def install(root):
    """Attach once per Tk application, including later dialogs and lazy pages."""
    root=root._root()
    if not hasattr(root,'game_tools_list_behavior'):root.game_tools_list_behavior=ListBehavior(root)
    return root.game_tools_list_behavior

def attach(widget):return install(widget).attach(widget)

def main(argv=None):
    """Launch an existing authored Tk app with this presentation adapter only.

    Used by standalone app launchers that do not import the shared CompactUI.
    No Python installation, environment, settings or native profile is changed.
    """
    import argparse,runpy,sys
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app',required=True,type=Path)
    args,remaining=parser.parse_known_args(argv)
    entry=args.app.resolve(strict=True)
    if not entry.is_file()or entry.suffix not in {'.py','.pyw'}:parser.error('Choose an existing authored Python app')
    original=tk.Tk.__init__
    def init(root,*a,**kw):
        original(root,*a,**kw);install(root)
    tk.Tk.__init__=init
    sys.argv=[str(entry),*remaining];sys.path.insert(0,str(entry.parent))
    try:runpy.run_path(str(entry),run_name='__main__')
    finally:tk.Tk.__init__=original

if __name__=='__main__':main()
