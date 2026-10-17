"""Read embedded Strategic V3 data without executing HTML/JavaScript.

Keeps family, variant, context, limitations and source evidence. Labels are not
native action identifiers. Empty target/deferred records never become patches.
"""
from __future__ import annotations
from html.parser import HTMLParser
import hashlib
from pathlib import Path
import re
from .deps import strict_json,require,json_new,read_json,object_hash,contained,local_lock

class _Data(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=False);self.inside=False;self.parts=[];self.count=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='script' and attrs.get('id')=='map-data':
            require(attrs.get('type')=='application/json','PLANNER_INVALID','map-data must be inert JSON.')
            self.inside=True;self.count+=1
    def handle_endtag(self,tag):
        if tag=='script':self.inside=False
    def handle_data(self,data):
        if self.inside:self.parts.append(data)

def extract(raw:bytes) -> dict:
    require(type(raw) is bytes and 0<len(raw)<=8*1024*1024,'SIZE_LIMIT','Planner must fit in eight MiB.')
    parser=_Data();parser.feed(raw.decode('utf-8-sig'));parser.close()
    require(parser.count==1,'PLANNER_INVALID','Expected exactly one map-data JSON block.')
    data=strict_json(''.join(parser.parts));maps=data.get('maps')
    require(type(maps) is list and len(maps)<=100,'PLANNER_INVALID','Invalid map collection.')
    variants=[];games=set();assignments=0
    for m in maps:
        if m.get('name')=='Shared SPARSE6':continue
        vs=m.get('strategic',{}).get('variants',[])
        require(type(vs) is list and len(vs)<=100,'PLANNER_INVALID','Invalid strategic variants.')
        for v in vs:
            entries=[]
            for key,a in v.get('assignments',{}).items():
                require(key==a.get('target_output'),'PLANNER_INVALID','Assignment target mismatch.')
                entries.append({'label':a.get('en',''),'target_key':key,'source_key':a.get('original_output'),
                                'evidence':a.get('evidence'),'applied':False})
            assignments+=len(entries);games.add(m['name'])
            variant={'game':m['name'],'map_id':m['id'],'family':m['family'],'character':v.get('character',''),
                     'input_preset':v.get('mode',''),'context':v.get('context',''),
                     'constraints':v.get('constraints',[]),'assignments':entries,
                     'deferred':[{'label':c.get('label'),'status':c.get('status'),'reason':c.get('reason')}
                                 for c in v.get('catalog',[]) if not c.get('target_output')]}
            variant['variant_id']=object_hash({k:variant[k] for k in ('map_id','family','character','input_preset','context')})[:20]
            variants.append(variant)
    result={'schema_version':1,'source_sha256':hashlib.sha256(raw).hexdigest(),
            'planner_revision':data.get('planner_revision'),'source_policy':data.get('strategic_policy'),
            'pending_or_source_corrections':data.get('audit_corrections'),
            'games':len(games),'variants_count':len(variants),'assignments_count':assignments,
            'variants':variants,'native_action_translation':'REQUIRES_REVIEWED_GAME_RECIPE',
            'native_profiles_changed':False,'native_files_generated':False}
    require(len({v['variant_id'] for v in variants})==len(variants),'PLANNER_INVALID','Variant identities collide.')
    return result

def cached_extract(source:Path,data_dir:Path) -> dict:
    from .core import snapshot
    raw=snapshot(source);digest=hashlib.sha256(raw).hexdigest()
    root=Path(data_dir)/'keybinds'/'planner-cache';path=contained(root,digest+'.json')
    with local_lock(Path(data_dir)/'keybinds','.keybind-ops.lock'):
        if path.exists():
            record=read_json(path,8*1024*1024)
            require(record['payload']['source_sha256']==digest and object_hash(record['payload'])==record['payload_sha256'],
                    'CACHE_CORRUPT','Cached extraction changed; no reconstruction or silent replacement.')
            return {'cache_hit':True,**record['payload']}
        payload=extract(raw);json_new(path,{'payload':payload,'payload_sha256':object_hash(payload)})
    return {'cache_hit':False,**payload}
