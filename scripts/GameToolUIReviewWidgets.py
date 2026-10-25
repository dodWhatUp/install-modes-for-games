"""Reusable review-only UI patterns over the existing compact controls."""
import tkinter as tk
from tkinter import ttk
from GameToolCompactUI import Selector,FlowToolbar,ScrollableFrame,TableLayout

class WindowPin(ttk.Checkbutton):
    """An independent window-manager preference; no focus loop or input hook."""
    def __init__(self,parent,window,value=False,on_change=lambda value:None):
        self.window,self.on_change=window,on_change;self.value=tk.BooleanVar(window,value=bool(value))
        super().__init__(parent,text='Always on top',variable=self.value,command=self.apply)
        self.apply(save=False)
    def apply(self,save=True):
        self.window.attributes('-topmost',self.value.get())
        if save:self.on_change(self.value.get())

class Section(ttk.Frame):
    def __init__(self,parent,title,on_hide):
        super().__init__(parent,style='Review.Card.TFrame',padding=12)
        head=ttk.Frame(self,style='Review.Card.TFrame');head.pack(fill='x')
        ttk.Label(head,text=title,style='Review.Section.TLabel').pack(side='left')
        ttk.Button(head,text='× Hide',style='Review.Subtle.TButton',command=on_hide).pack(side='right')
        self.body=ttk.Frame(self,style='Review.Card.TFrame');self.body.pack(fill='both',expand=True,pady=(8,0))

class Visibility(ttk.Menubutton):
    def __init__(self,parent,callback):
        super().__init__(parent,text='Show/Hide sections',style='Review.TMenubutton')
        self.menu=tk.Menu(self,tearoff=False);self.configure(menu=self.menu);self.callback=callback;self.variables={}
    def set_sections(self,sections,hidden):
        self.menu.delete(0,'end');self.variables={}
        for key,label in sections:
            var=tk.BooleanVar(self,value=not hidden(key));self.variables[key]=var
            self.menu.add_checkbutton(label='Show '+label,variable=var,command=lambda k=key,v=var:self.callback(k,not v.get()))
        self.menu.add_separator();self.menu.add_command(label='Show all sections',command=self.restore)
    def restore(self):
        for key,var in self.variables.items():var.set(True);self.callback(key,False)

class ResourcePane(ttk.Frame):
    def __init__(self,parent,*,on_select,on_folder,on_open,on_copy,on_refresh):
        super().__init__(parent,style='Review.Card.TFrame')
        ttk.Label(self,text='Component / file / location',style='Review.Card.TLabel').pack(anchor='w')
        self.selector=Selector(self,on_select=on_select);self.selector.pack(fill='x',pady=5)
        self.path=tk.StringVar(self);ttk.Label(self,textvariable=self.path,style='Review.Muted.TLabel',wraplength=760).pack(anchor='w')
        bar=FlowToolbar(self);bar.pack(fill='x',pady=6);self.actions={}
        for label,action in [('Open location',on_folder),('Open selected item',on_open),('Copy path',on_copy),('Refresh files',on_refresh)]:self.actions[label]=bar.add(label,action)
        box=ttk.Frame(self,style='Review.Card.TFrame');box.pack(fill='both',expand=True)
        self.tree=ttk.Treeview(box,columns=('name','kind','size'),show='headings',height=7)
        for key,width in [('name',450),('kind',90),('size',100)]:self.tree.heading(key,text=key.title());self.tree.column(key,width=width)
        self.tree.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(box,command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set);self.layout=TableLayout(self.tree)
        self.summary=tk.StringVar(self,value='Select a location and use Refresh files to read its current state.')
        ttk.Label(self,textvariable=self.summary,style='Review.Card.TLabel',wraplength=780).pack(anchor='w',pady=(7,0))
    def set_resources(self,rows,selected=None):
        self.selector.set_choices([(r['id'],r['label']+('' if r['exists'] else ' — unavailable')) for r in rows]);self.selector.select(selected or (rows[0]['id'] if rows else None))
    def show_resource(self,row):
        self.path.set(str(row['path'])+('' if row['exists'] else ' • not present'))
        for key,button in self.actions.items():button.configure(state='normal' if row['exists'] else 'disabled')
    def display(self,result):
        self.tree.delete(*self.tree.get_children())
        for row in result['observation']['entries']:self.tree.insert('','end',values=(row['name'],row['kind'],'—' if row['bytes'] is None else f"{row['bytes']:,}"))
        d=result['delta'];self.summary.set(f"{len(result['observation']['entries'])} entries • +{len(d['added'])} added • {len(d['changed'])} changed • {len(d['removed'])} removed"+(' • partial listing' if d['partial'] else '')+'\n'+result['observation']['observed_utc'])
    def close(self):self.layout.close()

class SchemaEditor(ttk.Frame):
    def __init__(self,parent,schema,variables):
        super().__init__(parent,style='Review.Card.TFrame');self.columnconfigure(1,weight=1);self.widgets={}
        for i,field in enumerate(schema):
            ttk.Label(self,text=field['label'],style='Review.Card.TLabel').grid(row=i,column=0,sticky='w',padx=(0,20),pady=6)
            var=variables[field['id']]
            if field['type']=='bool':widget=ttk.Checkbutton(self,text='Enabled',variable=var,style='Review.TCheckbutton')
            elif field['type']=='enum':widget=ttk.Combobox(self,textvariable=var,values=field['choices'],state='readonly')
            else:widget=ttk.Spinbox(self,textvariable=var,from_=field['min'],to=field['max'],increment=1 if field['type']=='int' else .1)
            widget.grid(row=i,column=1,sticky='ew',pady=6)
            self.widgets[field['id']]=widget

def theme(root,dark=False,zoom=100):
    palette=({'bg':'#111821','card':'#1d2734','ink':'#ecf2f9','muted':'#b4c2d3','accent':'#86bfff'} if dark else
             {'bg':'#edf1f7','card':'#ffffff','ink':'#172c46','muted':'#54657b','accent':'#dceaff'})
    style=ttk.Style(root);style.theme_use('clam');size=round(10*zoom/100);font=('Segoe UI' if root.tk.call('tk','windowingsystem')=='win32' else 'DejaVu Sans',size)
    style.configure('.',font=font,foreground=palette['ink'],background=palette['bg'])
    style.configure('TFrame',background=palette['card']);style.configure('TLabel',background=palette['card'],foreground=palette['ink'])
    style.configure('TButton',background=palette['accent'],foreground='#142b45',padding=(8,5));style.configure('TLabelframe',background=palette['card']);style.configure('TLabelframe.Label',background=palette['card'],foreground=palette['ink'])
    for name in ('TEntry','TCombobox','TSpinbox'):
        style.configure(name,fieldbackground=palette['card'],foreground=palette['ink'],insertcolor=palette['ink'])
        style.map(name,fieldbackground=[('readonly',palette['card'])],foreground=[('readonly',palette['ink'])],selectbackground=[('focus','#315c8c')],selectforeground=[('focus','#ffffff')])
    style.configure('Treeview',background=palette['card'],fieldbackground=palette['card'],foreground=palette['ink'],rowheight=round(26*zoom/100));style.configure('Treeview.Heading',background=palette['bg'],foreground=palette['ink'])
    style.map('Treeview',background=[('selected','#315c8c')],foreground=[('selected','#ffffff')])
    root.configure(bg=palette['bg']);style.configure('Review.TFrame',background=palette['bg']);style.configure('Review.Card.TFrame',background=palette['card'])
    for name,bg,fg,weight in [('Review.TLabel','bg','ink','normal'),('Review.Card.TLabel','card','ink','normal'),('Review.Muted.TLabel','card','muted','normal'),('Review.Section.TLabel','card','ink','bold'),('Review.Title.TLabel','bg','ink','bold')]:style.configure(name,background=palette[bg],foreground=palette[fg],font=(font[0],size+(4 if 'Title' in name else 0),weight))
    for name in ('Review.TButton','Review.Subtle.TButton','Review.TMenubutton'):
        style.configure(name,padding=(9,6),font=font,foreground='#142b45',background=palette['accent'])
    style.configure('Review.TCheckbutton',font=font,foreground=palette['ink'],background=palette['card'])
    return palette,font
