"""Quiet, editable choice-field icons. Icon preferences never own field values."""
from __future__ import annotations
import hashlib, json, math, os, sys, tempfile
from pathlib import Path
import tkinter as tk
from tkinter import ttk, font, messagebox

VERSION = '0.2.0'
ICONS = ('none', 'search', 'game', 'profile', 'keyboard', 'folder', 'layers', 'image', 'tools', 'star', 'shield')
LABELS = dict(none='No icon', search='Search', game='Game', profile='Profile', keyboard='Device',
              folder='Folder', layers='Layers', image='Image', tools='Settings', star='Favorite', shield='Safety')


def padding_pixels(widget, value):
    # Windows Tk can return Tcl pixel objects; int(Tcl_Obj) is unsupported.
    # Tk also owns dimensional units and the active display's pixel scale.
    parts = value if isinstance(value,(tuple,list)) else widget.tk.splitlist(str(value or '2'))
    return [widget.winfo_pixels(str(part)) for part in parts]


class IconStore:
    """Bounded, separate presentation preferences with conflict protection."""
    def __init__(self, path):
        self.path = Path(path); self.reload()

    def reload(self):
        self.raw = None
        self.value = {'schema_version': 1, 'icons': {}}; self.error = ''
        try:
            if self.path.is_symlink(): raise ValueError('Icon preferences must be a regular file.')
            if self.path.exists() and self.path.stat().st_size > 262144: raise ValueError('Icon preferences exceed their size limit.')
            self.raw = self.path.read_bytes() if self.path.exists() else None
            if self.raw is not None:
                if len(self.raw) > 262144: raise ValueError('Icon preferences exceed their size limit.')
                value = json.loads(self.raw)
                if (not isinstance(value, dict) or value.get('schema_version') != 1
                    or not isinstance(value.get('icons'), dict) or len(value['icons']) > 1500):
                    raise ValueError('Unsupported icon preferences; original retained.')
                if 'show_icons' in value and type(value['show_icons']) is not bool:
                    raise ValueError('Invalid icon visibility preference; original retained.')
                for key, row in value['icons'].items():
                    if (len(key) != 64 or any(c not in '0123456789abcdef' for c in key)
                        or not isinstance(row, dict) or row.get('icon') not in (*ICONS,'auto')
                        or row.get('position') not in ('start', 'end')):
                        raise ValueError('Invalid icon preference; original retained.')
                self.value = value
        except (OSError, ValueError, TypeError) as error: self.error = str(error)

    def save(self, key, icon, position):
        if self.error: raise ValueError(self.error)
        if icon not in (*ICONS, 'auto') or position not in ('start', 'end'): raise ValueError('Choose a valid icon and position.')
        current = self.path.read_bytes() if self.path.exists() else None
        if current != self.raw: raise ValueError('Icon preferences changed elsewhere. Reopen the picker; original retained.')
        value = dict(self.value, icons=dict(self.value['icons']))
        if icon == 'auto' and position == 'start': value['icons'].pop(key, None)
        else: value['icons'][key] = dict(value['icons'].get(key,{}),icon=icon,position=position)
        if len(value['icons']) > 1500: raise ValueError('Icon preference limit reached.')
        self._write(value)

    def save_visibility(self, visible):
        if type(visible) is not bool: raise ValueError('Choose Show or Hide field icons.')
        self._write(dict(self.value,show_icons=visible))

    def _write(self, value):
        if self.error: raise ValueError(self.error)
        current = self.path.read_bytes() if self.path.exists() else None
        if current != self.raw: raise ValueError('Icon preferences changed elsewhere. Reopen the settings; original retained.')
        raw = (json.dumps(value, indent=2)+'\n').encode('utf-8')
        if len(raw) > 262144: raise ValueError('Icon preferences exceed their size limit.')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix='.choice-icons-', suffix='.tmp', dir=self.path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream: stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            if (self.path.read_bytes() if self.path.exists() else None) != self.raw: raise ValueError('Icon preferences changed during save; original retained.')
            os.replace(temporary, self.path); self.raw, self.value = raw, value
        finally:
            if os.path.exists(temporary): os.unlink(temporary)


def drawing(root, name, size, color):
    """Small code-drawn glyphs, without emoji fonts or external image assets."""
    image = tk.PhotoImage(master=root, width=size, height=size)
    def point(v): return round(v*(size-1)/16)
    def line(*points):
        for (x0,y0),(x1,y1) in zip(points, points[1:]):
            x0,y0,x1,y1=map(point,(x0,y0,x1,y1));steps=max(abs(x1-x0),abs(y1-y0),1)
            for n in range(steps+1): image.put(color,(round(x0+(x1-x0)*n/steps),round(y0+(y1-y0)*n/steps)))
    def box(x,y,w,h): line((x,y),(x+w,y),(x+w,y+h),(x,y+h),(x,y))
    def circle(x,y,r): line(*[(x+r*math.cos(n*math.pi/12),y+r*math.sin(n*math.pi/12))for n in range(25)])
    if name=='search': circle(6.5,6.5,4.5);line((10,10),(15,15))
    elif name=='game':
        line((3,5),(13,5),(15,12),(12,13),(10,10),(6,10),(4,13),(1,12),(3,5));line((4,7),(4,10));line((2.5,8.5),(5.5,8.5));circle(11.5,7.5,.6)
    elif name=='profile': box(3,1,10,14);line((6,5),(10,5));line((6,8),(10,8));line((6,11),(10,11))
    elif name=='keyboard':
        box(1,4,14,9)
        for y in (7,9):
            for x in (4,7,10,13): line((x,y),(x,y))
        line((5,11),(11,11))
    elif name=='folder': line((1,5),(1,3),(6,3),(8,5),(15,5),(14,13),(1,13),(1,5),(15,5))
    elif name=='layers':
        line((1,5),(8,1),(15,5),(8,9),(1,5));line((1,8),(8,12),(15,8));line((1,11),(8,15),(15,11))
    elif name=='image': box(1,2,14,12);circle(11,5,1);line((2,12),(6,7),(9,11),(11,9),(14,12))
    elif name=='tools':
        for x,y in ((3,5),(8,10),(13,6)): line((x,2),(x,14));box(x-1.5,y-1.5,3,3)
    elif name=='star': line(*[(8+(7 if n%2==0 else 3)*math.cos(-math.pi/2+n*math.pi/5),8+(7 if n%2==0 else 3)*math.sin(-math.pi/2+n*math.pi/5))for n in range(11)])
    elif name=='shield': line((2,2),(8,1),(14,2),(13,9),(8,15),(3,9),(2,2));line((5,7),(7,9),(11,5))
    else: # An empty outlined slot, with a small unobtrusive add mark.
        box(3,3,10,10);line((6,8),(10,8));line((8,6),(8,10))
    return image


def field_label(widget):
    explicit = getattr(widget, 'game_tools_icon_role', '')
    if explicit: return explicit
    info = widget.grid_info() if widget.winfo_manager() == 'grid' else {}
    siblings = widget.master.winfo_children(); candidates = []
    for child in siblings:
        if not isinstance(child, (ttk.Label, tk.Label)): continue
        if info:
            other = child.grid_info()
            if other and other.get('row') == info.get('row') and int(other.get('column',0)) < int(info.get('column',0)):
                candidates.append((int(other['column']),str(child.cget('text'))))
        elif siblings.index(child) < siblings.index(widget): candidates.append((siblings.index(child),str(child.cget('text'))))
    return max(candidates, default=(0,''))[1]


def automatic(label):
    label = label.casefold()
    for words, icon in ((('find','search'),'search'), (('new setup uses','input device','provider'),'keyboard'), (('game',),'game'), (('profile','setup'),'profile'),
        (('device','azeron','rewasd','keyboard'),'keyboard'), (('folder','location','installation'),'folder'),
        (('layer','group','context'),'layers'), (('image','picture'),'image'), (('tool','layout','interface'),'tools')):
        if any(word in label for word in words): return icon
    return 'none'


class FieldIcon:
    def __init__(self, manager, widget):
        self.manager, self.widget = manager, widget
        self.base = self.style_name = ''; self.job = None; self.tooltip = None; self.tip_job = None
        self.button = tk.Button(widget.master, text='Change icon', relief='flat', bd=0, padx=2, pady=0,
            highlightthickness=1, takefocus=True, cursor='hand2', command=self.pick)
        self.button.bind('<Enter>', self.tip); self.button.bind('<Leave>', self.hide_tip)
        self.bindings = [(event,widget.bind(event,callback,add='+')) for event,callback in (
            ('<Configure>',self.queue),('<<ThemeChanged>>',self.queue),('<<ComboboxSelected>>',self.queue),('<Map>',self.queue),
            ('<Unmap>',lambda _:self.button.place_forget()),('<Destroy>',self.destroy),
            ('<Alt-i>',lambda _:self.pick()))]
        self.trace = None;self.variable = ''
        self.bind_variable()
        widget.game_tools_choice_icon = self; self.queue()

    def bind_variable(self):
        variable = str(self.widget.cget('textvariable'))
        if not variable or variable == self.variable: return
        if self.trace:
            try:self.widget.tk.call('trace','remove','variable',self.variable,'write',self.trace)
            except tk.TclError:pass
        self.trace_name = self.widget.register(self.queue);self.variable = variable
        self.widget.tk.call('trace','add','variable',variable,'write',self.trace_name);self.trace = self.trace_name

    def context(self):
        w = self.widget; label = field_label(w)
        scope = getattr(w, 'game_tools_icon_key', '')
        if not scope:
            markers = getattr(getattr(w._root(),'game_tools_feedback',None),'markers',None)
            record = getattr(markers,'records',{}).get(str(w))
            if record: scope = record[2]
            elif label:
                owner = w.master
                while owner.master is not None and type(owner).__module__.startswith('tkinter'): owner=owner.master
                scope = type(owner).__name__+'/'+label.casefold().strip()
            else: scope = str(w)
        text = w.get(); identity = ''
        records = getattr(w, 'records', None)
        if isinstance(records, dict): identity = next((str(k)for k,v in records.items()if v==text),'')
        elif text and text in tuple(map(str,w.cget('values'))): identity = text
        raw = self.manager.namespace+'\0'+scope+'\0'+('item:'+identity if identity else 'field')
        return hashlib.sha256(raw.encode()).hexdigest(), label, bool(identity)

    def queue(self,*_):
        if self.job is None and self.widget.winfo_exists(): self.job = self.widget.after_idle(self.sync)

    def sync(self):
        self.job = None; w = self.widget
        if not w.winfo_exists(): return
        self.bind_variable()
        style = ttk.Style(w); current = str(w.cget('style')) or 'TCombobox'
        if current != self.style_name:
            self.base = current; self.style_name = 'ChoiceIcon'+str(id(self))+'.'+current
            w.configure(style=self.style_name)
        raw_padding = style.lookup(self.base,'padding') or '2'
        padding = padding_pixels(w,raw_padding)
        if len(padding)==1: padding*=4
        elif len(padding)==2: padding*=2
        elif len(padding)==3: padding.append(padding[1])
        def apply_padding(values):
            signature = (style.theme_use(), self.style_name, tuple(values))
            if getattr(self,'_padding_signature',None) != signature:
                self._padding_signature = signature
                style.configure(self.style_name,padding=values)
        if not self.manager.show_icons.get() or w.winfo_width()<100:
            self.hide_tip()
            if w.winfo_viewable() and str(w.tk.call('focus'))==str(self.button):w.focus_set()
            self.button.place_forget();apply_padding(padding);return
        key,label,_ = self.context(); row = self.manager.store.value['icons'].get(key,{})
        name = row.get('icon','auto');name = automatic(label)if name=='auto'else name
        position = row.get('position','start')
        size = max(14,min(20,font.nametofont('TkDefaultFont',root=w).metrics('linespace')-5)); reserve = size+8
        bg = style.lookup(self.base,'fieldbackground',w.state()) or style.lookup('TEntry','fieldbackground') or '#ffffff'
        fg = style.lookup(self.base,'foreground',w.state()) or '#24364b'
        rgb = w.winfo_rgb(bg); ink = w.winfo_rgb(fg)
        color = '#'+''.join(f'{round((a*.25+b*.75)/257):02x}'for a,b in zip(rgb,ink))
        self.image = self.manager.glyph(name,size,color)
        self.button.configure(image=self.image, text='Change '+LABELS[name].lower()+' icon', bg=bg,
            activebackground=bg, highlightbackground=bg, highlightcolor=fg)
        adjusted = padding.copy();adjusted[0 if position=='start'else 2] += reserve
        apply_padding(adjusted)
        if w.winfo_viewable():
            if position=='start': self.button.place(in_=w,x=3,rely=.5,anchor='w',width=reserve-2,relheight=.88)
            else:
                width=w.winfo_width();y=w.winfo_height()//2
                arrow = [x for x in range(width-1,max(0,width-80),-1)if 'arrow'in w.identify(x,y)]
                offset = width-min(arrow)if arrow else 20
                self.button.place(in_=w,relx=1,x=-offset-3,rely=.5,anchor='e',width=reserve-2,relheight=.88)
            self.button.lift()
        if w.instate(['disabled']): self.button.configure(state='disabled')
        else: self.button.configure(state='normal')

    def tip(self,*_):
        self.hide_tip();self.tip_job=self.widget.after(650,self.show_tip)
    def show_tip(self):
        self.tip_job=None
        if not self.button.winfo_viewable():return
        self.tooltip=tk.Toplevel(self.widget);self.tooltip.overrideredirect(True)
        ttk.Label(self.tooltip,text='Change / add icon  \u00b7  Alt+I',padding=5).pack()
        self.tooltip.geometry(f'+{self.button.winfo_rootx()}+{self.button.winfo_rooty()+self.button.winfo_height()+3}')
    def hide_tip(self,*_):
        if self.tip_job:self.widget.after_cancel(self.tip_job);self.tip_job=None
        if self.tooltip:self.tooltip.destroy();self.tooltip=None
    def pick(self):
        self.hide_tip(); self.manager.pick(self);return 'break'
    def destroy(self,event):
        if event.widget is not self.widget:return
        if self.job:self.widget.after_cancel(self.job);self.job=None
        self.hide_tip()
        if self.trace:
            try:self.widget.tk.call('trace','remove','variable',self.variable,'write',self.trace)
            except tk.TclError:pass
        self.button.destroy();self.manager.fields.pop(str(self.widget),None)


class IconManager:
    def __init__(self, root):
        self.root=root;self.fields={};self.images={};self.picker=None
        self.namespace=getattr(root,'game_tools_icon_namespace',hashlib.sha256(str(Path(sys.argv[0]).resolve()).encode()).hexdigest()[:16])
        default=Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.config')))/'GameTools'/'choice-icons.json'
        self.store=IconStore(getattr(root,'game_tools_icon_path',default))
        self.show_icons=tk.BooleanVar(root,value=self.store.value.get('show_icons',True))
        self.show_icons.trace_add('write',self.visibility_changed)
        root.bind_class('TCombobox','<Map>',self.mapped,add='+');self.scan(root)
    def visibility_changed(self,*_):
        for field in list(self.fields.values()):field.queue()
    def save_visibility(self):
        wanted=self.show_icons.get()
        try:
            self.store.reload();self.store.save_visibility(wanted)
        except (ValueError,OSError)as error:
            messagebox.showwarning('Field icon display',
                'Changed for this session only. Existing preferences were retained.\n'+str(error),parent=self.root)
        self.visibility_changed()
    def glyph(self,name,size,color):
        key=name,size,color
        if key not in self.images:self.images[key]=drawing(self.root,name,size,color)
        return self.images[key]
    def mapped(self,event):
        if isinstance(event.widget,ttk.Combobox):self.attach(event.widget)
    def attach(self,widget):
        if not hasattr(widget,'game_tools_choice_icon'):self.fields[str(widget)]=FieldIcon(self,widget)
        return widget.game_tools_choice_icon
    def scan(self,parent):
        if isinstance(parent,ttk.Combobox):self.attach(parent)
        for child in parent.winfo_children():self.scan(child)
    def pick(self,field):
        if self.picker and self.picker.winfo_exists():self.picker.lift();return
        lists=getattr(self.root,'game_tools_list_behavior',None)
        if lists and lists.active:lists.active.hide()
        self.store.reload();key,label,item=field.context();row=self.store.value['icons'].get(key,{})
        win=self.picker=tk.Toplevel(field.widget);win.title('Choose icon');win.transient(field.widget.winfo_toplevel())
        win.resizable(False,False);body=ttk.Frame(win,padding=12,borderwidth=1,relief='solid');body.pack(fill='both',expand=True)
        ttk.Label(body,text='Icon for this choice'if item else'Icon for this field / empty entry',font=('Segoe UI',10,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',pady=(0,8))
        selected=tk.StringVar(win,value=row.get('icon','auto'));position=tk.StringVar(win,value=row.get('position','start'))
        for n,name in enumerate(('auto',*ICONS)):
            icon=automatic(label)if name=='auto'else name
            button=ttk.Radiobutton(body,text='Automatic'if name=='auto'else LABELS[name],image=self.glyph(icon,16,'#677589'),compound='left',
                variable=selected,value=name,padding=4)
            button.grid(row=1+n//3,column=n%3,sticky='w',padx=(0,8),pady=3)
        place=ttk.Frame(body);place.grid(row=5,column=0,columnspan=3,sticky='w',pady=8)
        ttk.Label(place,text='Position:').pack(side='left')
        for value,caption in (('start','Start'),('end','End')):ttk.Radiobutton(place,text=caption,variable=position,value=value).pack(side='left',padx=6)
        status=tk.StringVar(win,value='Text, selection and game settings stay unchanged.')
        ttk.Label(body,textvariable=status,wraplength=330).grid(row=6,column=0,columnspan=3,sticky='ew',pady=(0,8))
        def close():
            win.destroy();self.picker=None
            if field.widget.winfo_exists():field.widget.focus_set()
        def save():
            try:
                if not field.widget.winfo_exists()or field.context()[0]!=key:raise ValueError('The field selection changed. Reopen the icon picker.')
                choice=selected.get()
                self.store.save(key,choice,position.get())
                for other in list(self.fields.values()):other.queue()
                close()
            except (ValueError,OSError)as error:status.set(str(error))
        actions=ttk.Frame(body);actions.grid(row=7,column=0,columnspan=3,sticky='e')
        ttk.Button(actions,text='Cancel',command=close).pack(side='left',padx=5)
        ttk.Button(actions,text='Save icon',command=save).pack(side='left')
        win.bind('<Escape>',lambda _:close());win.protocol('WM_DELETE_WINDOW',close)
        anchor=field.button if field.button.winfo_viewable()else field.widget
        win.update_idletasks();x=anchor.winfo_rootx();y=anchor.winfo_rooty()+anchor.winfo_height()+4
        x=max(0,min(x,win.winfo_screenwidth()-win.winfo_reqwidth()-10));y=max(0,min(y,win.winfo_screenheight()-win.winfo_reqheight()-20))
        win.geometry(f'+{x}+{y}');win.lift()


def install(root):
    root=root._root()
    if not hasattr(root,'game_tools_choice_icons'):root.game_tools_choice_icons=IconManager(root)
    return root.game_tools_choice_icons


def context(widget,key,role):
    widget.game_tools_icon_key=key;widget.game_tools_icon_role=role
    install(widget).attach(widget).queue()
