"""Bounded local control finder: reviewed metadata, never commands or file contents."""
from __future__ import annotations
import difflib,queue,re,threading,unicodedata
import tkinter as tk
from tkinter import ttk
from GameToolUIReviewModel import PAGES,MANAGERS,TARGETS
from GameToolUIReviewWidgets import WindowPin

SCOPES=('This page','Selected game','All connected games')
TOPICS=('Any topic','Graphics','Gameplay','Camera','Files','Programs','Profiles','Reports','Interface')
KINDS=('Any kind','Setting','Switch','Function','Location','Page')
GROUPS=('Graphics','Camera & render size','Gameplay & mod options')
STOP=set('a an the to for of in on at is it how where find show me setting settings option options control controls i want can my this with and or please את של לי אני איך איפה רוצה אפשר הגדרות הגדרה למצוא'.split())
# Search vocabulary is explicitly curated. It does not infer unsupported features.
CONCEPTS=(('always on top','pin','keep visible','stay visible','floating','above other windows','חלון צף','תמיד למעלה','להשאיר פתוח'),
 ('fov','field of view','camera','zoom','שדה ראייה','מצלמה'),
 ('multi skills','multi equip','multiple abilities','simultaneous','same time','more abilities','more skills','יכולות במקביל','כישורים'),
 ('graphics','visuals','image quality','גרפיקה','איכות תמונה'),
 ('refresh','reload','rescan','updated files','רענון','לרענן'),
 ('location','folder','directory','path','תיקייה','תיקיות','מיקום'),
 ('export','handoff','transfer','manager','ייצוא','להעביר'),
 ('profile','preset','פרופיל'),('search','find','locate control','חיפוש','לחפש'),
 ('resolution','render size','width','height','רזולוציה'),
 ('duration','ability time','משך יכולת'),('focus','regeneration','regen','התחדשות'),
 ('movement','speed','run faster','sprint','מהירות','תנועה'),
 ('keyboard','modifier','hotkey','keybind','מקש','מקשים'),
 ('sound','audio','equip sound','צליל','קול'))
MEANINGS={
 'profile':('Graphics','Choose the reviewed graphics stack; availability and compatibility remain controller-owned.'),
 'graphics':('Graphics','Enable or disable the reviewed graphics component.'),
 'dlaa':('Graphics','Experimental Luma DLAA toggle. This is not proof of working DLSS SR or DLSS 5.'),
 'nr':('Graphics','Experimental neural rendering toggle; runtime delivery remains unverified.'),
 'gameplay':('Gameplay','Enable or disable the existing gameplay mod loader.'),
 'multi-skills':('Gameplay','Equip multiple skills or abilities at the same time.'),
 'elven-speed':('Gameplay','Movement speed option supplied by Elven Speed.'),
 'duration':('Gameplay','Adjust ability duration.'),'regen':('Gameplay','Adjust focus regeneration.'),
 'modifier':('Gameplay','Keyboard modifier used for multi-equip.'),'toggle':('Gameplay','Choose press-to-toggle behavior.'),
 'sound':('Gameplay','Control equip sound.'),'fov':('Camera','Enable the camera field of view extender.'),
 'fov_min':('Camera','Minimum camera field of view.'),'fov_max':('Camera','Maximum camera field of view.'),
 'width':('Graphics','Render resolution width.'),'height':('Graphics','Render resolution height.')}

def normalize(text):return ' '.join(re.findall(r'[^\W_]+',unicodedata.normalize('NFKC',str(text)).casefold(),flags=re.UNICODE))
def group_for(field):
    ident=field['id']
    return GROUPS[0] if ident in {'profile','graphics','dlaa','nr'} else GROUPS[1] if ident in {'fov','fov_min','fov_max','width','height'} else GROUPS[2]
def section_for(schema,field):return 'settings-'+str(list(dict.fromkeys(group_for(f) for f in schema)).index(group_for(field)))
def row(label,page,section,kind,topic,description,**extra):
    return dict(label=label,page=page,section=section,kind=kind,topic=topic,description=description,**extra)

def catalog(model,scope,page,game_id,instance):
    """Only declared locations and typed control schemas; no recursive content scan."""
    rows=[];warnings=[]
    pages=[page] if scope==SCOPES[0] else list(PAGES)
    for p in pages:
        rows.append(row(PAGES[p],p,None,'Page','Interface','Open this preview page.'))
        for label,section,action,topic,description in [
            ('Refresh files','locations','refresh','Files','Read bounded file changes while preserving drafts.'),
            ('Open location','locations','folder','Files','Select a component and open its containing folder.'),
            ('Open selected item','locations','item','Files','Open the selected existing file or component.'),
            ('Copy path','locations','copy','Files','Copy the selected component path.'),
            ('Add location','locations','add-location','Files','Connect an existing folder only to this preview.'),
            ('Prepare files','handoff','export','Programs','Prepare a private export or handoff for the selected program; no deployment.'),
            ('Open prepared folder','handoff','export-folder','Files','Inspect the existing prepared handoff.'),
            ('Open selected program','handoff','program','Programs','Open the explicitly chosen installed program.'),
            ('Locate program','handoff','locate-program','Programs','Choose an existing program for this preview connection.')]:
            if p!='review':rows.append(row(label,p,section,'Function',topic,description,action_id=action,aliases=' '.join(MANAGERS[k] for k in TARGETS.get(p,[])) if action=='export' else ''))
        if p=='mods':
            for label,section,action,topic,desc in [('Preview changes','draft','preview','Profiles','Compare this draft against the applied files.'),('Apply through current controller','draft','apply','Profiles','Changes the selected game only after explicit confirmation.'),('Floating editor','draft','floating','Interface','Keep an independently pinned settings window open while using another window.'),('Reset draft to applied','draft','reset','Profiles','Reset this draft to the last read applied values.'),('Save parallel profile','profiles','save-profile','Profiles','Save a preview profile without applying it.'),('Load into draft','profiles','load-profile','Profiles','Load a saved profile into this draft.')]:rows.append(row(label,p,section,'Function',topic,desc,action_id=action))
        try:
            for resource in model.resources(p,instance):
                if p!='review':rows.append(row(resource['label'],p,'locations','Location','Files','Known location: '+str(resource['path'])+(' (unavailable)' if not resource['exists'] else ''),resource_id=resource['id']))
        except Exception as error:warnings.append(PAGES[p]+': '+str(error))
    # Global display controls are discoverable even on a page without game settings.
    for label,action,desc in [('Always on top','pin','Keep this window above other ordinary windows while you work elsewhere.'),('Dark theme','dark','Change only this preview appearance.'),('Text zoom','zoom','Adjust preview text scaling.'),('Show/Hide sections','show-hide','Reveal hidden cards without disabling their features.'),('Game selection','game','Choose a connected game; typing filters the available names.'),('Installation selection','installation','Choose the relevant connected installation.'),('Find settings & functions','find','Search by exact control name, purpose, type or topic.')]:rows.append(row(label,page,None,'Switch' if action in {'pin','dark'} else 'Function','Interface',desc,action_id=action))
    if scope!=SCOPES[0] or page=='mods':
        count=0
        for game in model.games():
            if scope!=SCOPES[2] and game['game_id']!=game_id:continue
            for inst in game['instances']:
                ident=inst['instance_id']
                if scope==SCOPES[0] and ident!=instance:continue
                if count>=64:warnings.append('Only the first 64 connected installations are indexed.');break
                count+=1
                try:
                    state=model.inspect(ident);schema=state.get('schema',[])
                    if not schema:warnings.append(game['name']+' / '+ident+': no reviewed settings connection.');continue
                    for field in schema[:32]:
                        topic,desc=MEANINGS.get(field['id'],('Gameplay','Typed control declared by this installation’s reviewed support pack.'))
                        rows.append(row(field['label'],'mods',section_for(schema,field),'Switch' if field['type']=='bool' else 'Setting',topic,desc,field_id=field['id'],group=group_for(field),game_id=game['game_id'],game_name=game['name'],instance=ident,value=state['values'].get(field['id']),value_type=field['type'],aliases=' '.join(map(str,field.get('choices',[])))+' '+' '.join(str(field.get(k,'')) for k in ('file','section','key'))))
                except Exception as error:warnings.append(game['name']+' / '+ident+': '+str(error))
    for index,item in enumerate(rows):
        item['key']=str(index);item['breadcrumb']=' › '.join(filter(None,[item.get('game_name'),item.get('instance'),PAGES[item['page']],item.get('group') or item.get('section'),item['label']]))
    return rows,warnings

def search(rows,query,kind='Any kind',topic='Any topic',limit=250):
    query=normalize(query)[:240];terms=[t for t in query.split() if t not in STOP][:24]
    concepts=[{normalize(x) for x in group} for group in CONCEPTS]
    hits=[]
    for item in rows:
        if kind!=KINDS[0] and item['kind']!=kind:continue
        if topic!=TOPICS[0] and item['topic']!=topic:continue
        body=normalize(' '.join(str(item.get(k,'')) for k in ['label','field_id','description','aliases','breadcrumb','kind','topic']))
        words=set(body.split());score=0;reasons=[];remaining=[]
        for group in concepts:
            query_aliases=[alias for alias in group if ' '+alias+' ' in ' '+query+' ']
            if query_aliases and any(' '+alias+' ' in ' '+body+' ' for alias in group):
                score+=4;reasons.append('Related purpose: '+max(query_aliases,key=len));remaining.extend(' '.join(query_aliases).split())
        for term in terms:
            if term in remaining:continue
            if term in body:score+=6 if term in normalize(item['label']) else 2
            elif len(term)>=4 and any(difflib.SequenceMatcher(None,term,word).ratio()>=.84 for word in words if len(word)>=4):score+=1;reasons.append('Similar spelling: '+term)
            else:score=-1;break
        if score<0:continue
        hit=dict(item,match='; '.join(dict.fromkeys(reasons)) or ('Name / metadata match' if terms else 'Browse indexed controls'),score=score)
        hits.append(hit)
    hits.sort(key=lambda r:(-r['score'],r['label'].casefold(),r.get('instance','')))
    return hits[:limit],len(hits)

class Finder(tk.Toplevel):
    def __init__(self,app,scope=SCOPES[0]):
        super().__init__(app.root);self.app=app;self.rows=[];self.hits={};self.closed=False;self.generation=0;self.events=queue.Queue();self.jobs=0;self.debounce=None
        self.title('Find settings & functions');self.geometry('880x620');self.minsize(540,400)
        frame=ttk.Frame(self,padding=12,style='Review.TFrame');frame.pack(fill='both',expand=True);frame.columnconfigure(0,weight=1);frame.rowconfigure(5,weight=1)
        head=ttk.Frame(frame);head.grid(row=0,column=0,sticky='ew');self.pin=WindowPin(head,self,app.model.view.setdefault('window_pins',{}).get('finder',False),lambda value:app.save_pin('finder',value));self.pin.pack(side='right')
        ttk.Label(head,text='Find settings & functions',style='Review.Section.TLabel').pack(side='left')
        bar=ttk.Frame(frame);bar.grid(row=1,column=0,sticky='ew',pady=8);bar.columnconfigure(0,weight=1);self.query=tk.StringVar(self);self.entry=ttk.Entry(bar,textvariable=self.query);self.entry.grid(row=0,column=0,sticky='ew');self.entry.bind('<Return>',lambda _:self.go())
        self.scope=tk.StringVar(self,value=scope);box=ttk.Combobox(bar,values=SCOPES,textvariable=self.scope,state='readonly',width=21);box.grid(row=0,column=1,padx=(8,0));box.bind('<<ComboboxSelected>>',lambda _:self.reindex())
        self.advanced=tk.BooleanVar(self);ttk.Checkbutton(frame,text='Advanced filters',variable=self.advanced,command=self.toggle_advanced).grid(row=2,column=0,sticky='w')
        self.filters=ttk.Frame(frame);self.filters.columnconfigure(1,weight=1);self.filters.columnconfigure(3,weight=1);self.kind=tk.StringVar(self,value=KINDS[0]);self.topic=tk.StringVar(self,value=TOPICS[0])
        for column,(label,var,values) in enumerate([('Type',self.kind,KINDS),('Relevant to',self.topic,TOPICS)]):
            ttk.Label(self.filters,text=label).grid(row=0,column=column*2,padx=(0,6));b=ttk.Combobox(self.filters,textvariable=var,values=values,state='readonly',width=12);b.grid(row=0,column=column*2+1,sticky='ew',padx=(0,10));b.bind('<<ComboboxSelected>>',lambda _:self.update_results())
        ttk.Button(self.filters,text='Reset filters',command=self.reset_filters).grid(row=1,column=3,sticky='e',pady=(4,0))
        ttk.Label(frame,text='Try “more abilities at the same time”, “camera”, “Vortex”, or an exact switch name. Enter reveals a result; it never runs the function.',wraplength=760,style='Review.Muted.TLabel').grid(row=4,column=0,sticky='ew',pady=8)
        table=ttk.Frame(frame);table.grid(row=5,column=0,sticky='nsew');self.tree=ttk.Treeview(table,columns=('label','kind','where'),show='headings',height=5)
        for name,label,width in [('label','Control / function',230),('kind','Type',80),('where','Where it is',460)]:self.tree.heading(name,text=label);self.tree.column(name,width=width,minwidth=55)
        self.tree.pack(side='left',fill='both',expand=True);scroll=ttk.Scrollbar(table,command=self.tree.yview);scroll.pack(side='right',fill='y');self.tree.configure(yscrollcommand=scroll.set);self.tree.bind('<<TreeviewSelect>>',self.describe);self.tree.bind('<Double-1>',lambda _:self.go());self.tree.bind('<Return>',lambda _:self.go())
        self.tree.bind('<Configure>',self.table_layout)
        self.detail=tk.StringVar(self);ttk.Label(frame,textvariable=self.detail,wraplength=780,style='Review.Card.TLabel').grid(row=6,column=0,sticky='ew',pady=8)
        self.status=tk.StringVar(self);ttk.Label(frame,textvariable=self.status,wraplength=780,style='Review.Muted.TLabel').grid(row=7,column=0,sticky='ew')
        actions=ttk.Frame(frame);actions.grid(row=8,column=0,sticky='ew',pady=(8,0));self.reveal_button=ttk.Button(actions,text='Reveal control',command=self.go);self.reveal_button.pack(side='left');ttk.Button(actions,text='Refresh index',command=self.reindex).pack(side='left',padx=8);ttk.Button(actions,text='Close',command=self.close).pack(side='right')
        self.query.trace_add('write',self.schedule);self.bind('<Escape>',lambda _:self.close());self.protocol('WM_DELETE_WINDOW',self.close);self.bind('<Configure>',self.wrap);self._poll=self.after(60,self.poll);self.reindex();self.entry.focus_set()
    def wrap(self,event):
        if event.widget!=self:return
        stack=list(self.winfo_children())
        while stack:
            item=stack.pop();stack.extend(item.winfo_children())
            if isinstance(item,ttk.Label) and int(item.cget('wraplength') or 0)>0:item.configure(wraplength=max(260,event.width-55))
    def toggle_advanced(self):
        if self.advanced.get():self.filters.grid(row=3,column=0,sticky='ew',pady=6)
        else:self.filters.grid_remove();self.reset_filters()
    def table_layout(self,event):
        width=max(300,event.width-4)
        for key,size in [('label',max(130,int(width*.28))),('kind',90),('where',max(90,width-max(130,int(width*.28))-90))]:
            if self.tree.column(key,'width')!=size:self.tree.column(key,width=size,stretch=False)
    def reset_filters(self):self.kind.set(KINDS[0]);self.topic.set(TOPICS[0]);self.update_results()
    def schedule(self,*_):
        if self.debounce:self.after_cancel(self.debounce)
        self.debounce=self.after(120,self.update_results)
    def reindex(self):
        if self.jobs:self.reindex_pending=True;self.status.set('Index refresh is running; the latest scope will follow.');return
        self.reindex_pending=False
        self.generation+=1;token=self.generation;context=(self.scope.get(),self.app.page,self.app.game_id,self.app.instance);self.jobs+=1;self.status.set('Reading known controls and locations…');self.rows=[];self.update_results()
        def work():
            try:self.events.put((token,catalog(self.app.model,*context),None))
            except Exception as error:self.events.put((token,None,str(error)))
        threading.Thread(target=work,name='UI-review-search',daemon=False).start()
    def poll(self):
        if self.closed:return
        try:
            while True:
                token,result,error=self.events.get_nowait();self.jobs-=1
                if token!=self.generation:continue
                if error:self.status.set(error);continue
                self.rows,self.warnings=result;self.update_results()
        except queue.Empty:pass
        if not self.jobs and self.reindex_pending:self.reindex()
        self._poll=self.after(60,self.poll)
    def update_results(self):
        self.debounce=None;selected=self.tree.selection();hits,total=search(self.rows,self.query.get(),self.kind.get(),self.topic.get());self.hits={r['key']:r for r in hits};self.tree.delete(*self.tree.get_children());self.detail.set('')
        for item in hits:self.tree.insert('','end',iid=item['key'],values=(item['label'],item['kind'],item['breadcrumb']))
        if selected and selected[0] in self.hits:self.tree.selection_set(selected[0]);self.describe()
        if self.jobs:return
        warnings=getattr(self,'warnings',[]);self.status.set(f'{total} matches • {len(self.rows)} indexed items'+(' • showing first 250' if total>250 else '')+(' • '+str(len(warnings))+' unavailable connections: '+'; '.join(warnings)[:400] if warnings else '')+(' • Try a shorter phrase, a different scope or Reset filters.' if not total else '')+' • Local metadata search')
    def describe(self,_event=None):
        ids=self.tree.selection()
        if not ids:return
        item=self.hits[ids[0]];value='\nApplied value: '+str(item['value']) if 'value' in item else '';draft=self.app.model.view.get('drafts',{}).get(item.get('instance'),{})
        if item.get('field_id') in draft:value+=' • Saved draft: '+str(draft[item['field_id']])
        self.detail.set(item['description']+value+'\n'+item['match']+'\n'+item['breadcrumb'])
    def go(self):
        ids=self.tree.selection()
        if ids:self.app.safe(lambda:self.app.reveal_result(self.hits[ids[0]]))
    def close(self):
        if self.jobs:self.status.set('The bounded index read is finishing. Close again when it returns.');return False
        self.closed=True;self.after_cancel(self._poll)
        if self.debounce:self.after_cancel(self.debounce)
        self.destroy();return True
