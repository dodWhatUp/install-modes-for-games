"""Explicit scalar-override ownership graph with whole-instance dependency guards.
This is NOT a generic Unreal array/include/Steam-Input resolver. Packs declare the
reviewed precedence and overlapping contexts; unknown semantic owners stay blocked.
"""
from __future__ import annotations
import itertools,json
from pathlib import Path
from .deps import require,read_json,contained,slug,object_hash,Error
from .documents import Document
from .core import snapshot,sha,native_key


def instance(service,ident):
    rec=read_json(contained(service.root,'instances/'+slug(ident)+'.json'),1024*1024)
    body=rec['body'];require(body['instance_id']==ident and object_hash(body)==rec['revision'],'INSTANCE_CORRUPT','Game-instance definition changed.')
    from .packs import load_pin
    load_pin(service,body['pin'])
    for m in body['members']:
        s=service.target(m['target_id'])
        require(s['spec_sha256']==m['target_revision'] and s['spec'].get('scope_id')==ident,'TARGET_CHANGED','Instance native-field recipe differs from its reviewed pin.')
    return rec


def read_values(service,rec,overrides=None):
    overrides=overrides or {};rows=[];hashes={}
    from .packs import fingerprint
    for m in rec['body']['members']:
        ident=m['target_id'];s=service.target(ident)['spec']
        raw=overrides[ident] if ident in overrides else snapshot(contained(Path(s['root']),s['relative']))
        hashes[ident]=sha(raw);d=Document(raw,s['adapter'],s.get('encoding'));fingerprint(d,m['fingerprints'])
        fields={x['id']:x for x in s['fields']}
        for f in m['fields']:
            c=native_key(fields[f['id']],d.select(f['selector']).value)
            for ctx in f['contexts']:
                require(len(rows)<2048,'GRAPH_BUDGET','Narrow the game variant to at most 2048 native context bindings.')
                rows.append({'target_id':ident,'field_id':f['id'],'action':f['action'],'slot':f.get('slot','primary'),
                             'context':ctx,'key':c,'fallback_key':f.get('fallback_key'),'priority':m['priority'],
                             'writable':m['writable'] and not f.get('locked',False),'modifier_match':f.get('modifier_match','subset'),
                             'linked_group':f.get('linked_group','')})
    return rows,hashes


def resolved(rows):
    groups={};result=[];shadow=[]
    for r in rows:groups.setdefault((r['action'],r['slot'],r['context']),[]).append(r)
    for identity,members in groups.items():
        actual=[r for r in members if r['key']!='Inherit']
        if not actual:
            # A source-reviewed fallback is allowed only when no actual definition exists.
            actual=[{**r,'key':r['fallback_key'],'inherited':True} for r in members if r.get('fallback_key')]
        require(actual,'EFFECTIVE_UNKNOWN','No effective key or reviewed fallback is known.')
        priority=max(r['priority'] for r in actual);wins=[r for r in actual if r['priority']==priority]
        require(len(wins)==1,'OWNER_AMBIGUOUS','Two files claim equal precedence for the same action/context/slot.')
        win=wins[0];result.append(win)
        shadow.extend({**r,'status':'INHERITED' if r['key']=='Inherit' else 'SHADOWED'} for r in members if (r['target_id'],r['field_id'])!=(win['target_id'],win['field_id']))
    return result,shadow


def _key_alternatives(key):
    pieces=key.split('+');choices=[]
    for p in pieces:
        choices.append({'Ctrl':('LCtrl','RCtrl'),'Shift':('LShift','RShift'),'Alt':('LAlt','RAlt')}.get(p,(p,)))
    return [tuple(v) for v in itertools.product(*choices)]


def key_overlap(a,b):
    for x in _key_alternatives(a['key']):
        for y in _key_alternatives(b['key']):
            if x[-1]!=y[-1]:continue
            am,bm=set(x[:-1]),set(y[:-1])
            if a['modifier_match']=='exact' and b['modifier_match']=='exact':
                if am==bm:return True
            elif a['modifier_match']=='exact':
                if bm<=am:return True
            elif b['modifier_match']=='exact':
                if am<=bm:return True
            else:return True
    return False


def conflict_set(rows,exclusive):
    ex={frozenset(v) for v in exclusive};result=set();buckets={}
    # Only bindings sharing a possible base key can collide. Sided modifier keys
    # collapse to the generic bucket for comparison, not for native encoding.
    for r in rows:
        base=r['key'].split('+')[-1]
        base={'LCtrl':'Ctrl','RCtrl':'Ctrl','LShift':'Shift','RShift':'Shift','LAlt':'Alt','RAlt':'Alt'}.get(base,base)
        buckets.setdefault(base,[]).append(r)
    comparisons=0
    for group in buckets.values():
        for i,a in enumerate(group):
            for b in group[i+1:]:
                comparisons+=1
                require(comparisons<=300000,'GRAPH_BUDGET','Too many potentially overlapping bindings; narrow the reviewed scope.')
                if a['action']==b['action']:continue
                if frozenset((a['context'],b['context'])) in ex:continue
                if not key_overlap(a,b):continue
                x=(a['action'],a['slot'],a['context']);y=(b['action'],b['slot'],b['context'])
                result.add(tuple(sorted((x,y))))
    return result


def _validate_changes(before,after,rows,rec):
    old,old_shadow=resolved(before);new,new_shadow=resolved(after)
    extra=conflict_set(new,rec['body']['exclusive_contexts'])-conflict_set(old,rec['body']['exclusive_contexts'])
    require(not extra,'CROSS_FILE_COLLISION','A new effective key conflict spans files, slots or overlapping contexts.')
    changed={(r['target_id'],d['field_id']) for r in rows for d in r['diff']}
    for r in new_shadow:
        if r['status']=='SHADOWED':require((r['target_id'],r['field_id']) not in changed,'SHADOWED_CHANGE','The requested field is overridden by another file. Edit its effective owner.')
    # A linked native action group spans files as well as one file.
    groups={}
    for r in before:
        if r['linked_group']:groups.setdefault(r['linked_group'],set()).add((r['target_id'],r['field_id']))
    for values in groups.values():
        moved=values&changed
        require(not moved or moved==values,'LINKED_ACTIONS','This native linked group spans files; change the complete group.')
    for m in rec['body']['members']:
        if not m['writable']:require(not any(t==m['target_id'] for t,f in changed),'FIELD_PROTECTED','This file is a read-only source of defaults.')


def enrich_rows(service,rows,buffers):
    scope_ids={service.target(r['target_id'])['spec'].get('scope_id') for r in rows}-{None}
    for scope in sorted(scope_ids):
        rec=instance(service,scope)
        selected={r['target_id']:(a,b) for r,(a,b) in zip(rows,buffers) if service.target(r['target_id'])['spec'].get('scope_id')==scope}
        before,hashes=read_values(service,rec,{i:a for i,(a,b) in selected.items()})
        after,_=read_values(service,rec,{i:b for i,(a,b) in selected.items()})
        _validate_changes(before,after,[r for r in rows if r['target_id'] in selected],rec)
        guard={'instance_id':scope,'instance_revision':rec['revision'],'dependencies':hashes}
        for r in rows:
            if r['target_id'] in selected:r['scope_guard']=guard


def validate_guards(service,p):
    all_items=p.get('all_items',p['items']);completed=p.get('completed',0)
    after_applied={r['target_id']:r['after_sha256'] for r in all_items[:completed]}
    seen=set()
    for row in p['items']:
        scope=service.target(row['target_id'])['spec'].get('scope_id')
        if not scope:continue
        guard=row.get('scope_guard');require(guard and guard['instance_id']==scope,'GUARD_REQUIRED','Scoped targets cannot bypass their effective-binding guard.')
        if scope in seen:continue
        seen.add(scope);rec=instance(service,scope)
        require(rec['revision']==guard['instance_revision'],'INSTANCE_CHANGED','Instance definition changed after preview.')
        require(set(guard['dependencies'])=={m['target_id'] for m in rec['body']['members']},'GUARD_REQUIRED','Guard must cover every related binding file.')
        raw_running=service.process_reader();require(type(raw_running) is set,'PROCESS_STATE_UNKNOWN','The process guard did not return a known set.')
        running={x.casefold() for x in raw_running}
        for m in rec['body']['members']:
            ident=m['target_id'];s=service.target(ident)['spec']
            require(not running.intersection(x.casefold() for x in s['stopped_processes']),'PROCESS_RUNNING','A declared config/defaults writer is running.')
            expected=after_applied.get(ident,guard['dependencies'][ident])
            require(sha(snapshot(contained(Path(s['root']),s['relative'])))==expected,'DEPENDENCY_CHANGED','A related file changed. Inspect a fresh whole-game plan; no blind retry.')


def inspect_instance(service,ident,known_revision=None,offset=0,limit=100):
    require(type(offset) is int and offset>=0 and type(limit) is int and 1<=limit<=100,'PAGE_INVALID','Use offset >=0 and limit 1–100.')
    rec=instance(service,ident);rows,hashes=read_values(service,rec);active,shadow=resolved(rows)
    conflicts=conflict_set(active,rec['body']['exclusive_contexts'])
    data={'instance_id':ident,'game_id':rec['body']['game_id'],'variant_id':rec['body']['variant_id'],
          'instance_revision':rec['revision'],'pack_pin':rec['body']['pin'],'file_hashes':hashes,
          'effective_bindings':active,'shadowed_bindings':shadow,'existing_conflicts':len(conflicts),
          'semantic_model':'explicit scalar priority; no implicit includes, engine arrays or live input graph',
          'gameplay_verified':False,'private_paths_included':False}
    revision=object_hash(data)
    page={**data,'effective_bindings':active[offset:offset+limit],'shadowed_bindings':shadow[offset:offset+limit],
          'effective_total':len(active),'shadowed_total':len(shadow),
          'next_offset':offset+limit if offset+limit<max(len(active),len(shadow)) else None}
    return {'revision':revision,'unchanged':revision==known_revision,**({} if revision==known_revision else page)}


def list_instances(service,offset=0,limit=50,game_id=None):
    require(type(offset) is int and offset>=0 and type(limit) is int and 1<=limit<=100,'PAGE_INVALID','Use offset >=0 and limit 1–100.')
    root=service.root/'instances';out=[]
    for p in service._list(root,1024):
        rec=instance(service,p.stem);b=rec['body']
        if game_id is None or b['game_id']==game_id:out.append({'instance_id':b['instance_id'],'game_id':b['game_id'],'variant_id':b['variant_id'],'instance_revision':rec['revision'],'pack_pin':b['pin']})
    return {'instances':out[offset:offset+limit],'total':len(out),'next_offset':offset+limit if offset+limit<len(out) else None,'files_modified':False}


def intent_preview(service,instance_id,changes,expected_revision,*,allow_partial=False):
    """Exact semantic identities only. No fuzzy source-label guessing."""
    from .packs import validate_intent
    require(type(changes) is list and 0<len(changes)<=512,'INVALID_CHANGE','Provide 1–512 semantic action requests.')
    state=inspect_instance(service,instance_id)
    require(expected_revision==state['revision'],'INSTANCE_STALE','Native state changed since context was read.')
    rec=instance(service,instance_id);all_rows,_=read_values(service,rec);active,_=resolved(all_rows)
    selected={};missing=[];requested=set()
    for c in changes:
        validate_intent(c);ident=(c['action'],c.get('slot','primary'),c['context'])
        require(ident not in requested,'DUPLICATE_ACTION','Duplicate semantic action request.');requested.add(ident)
        winners=[r for r in active if (r['action'],r['slot'],r['context'])==ident]
        if not winners:missing.append({'action':c['action'],'context':c['context'],'slot':c.get('slot','primary'),'status':'ACTION_NOT_MAPPED'});continue
        w=winners[0]
        # A missing sparse user override can be materialized above a read-only default.
        optional=[r for r in all_rows if (r['action'],r['slot'],r['context'])==ident and r['key']=='Inherit' and r['writable'] and r['priority']>w['priority']]
        if optional:
            rank=max(x['priority'] for x in optional);choices=[x for x in optional if x['priority']==rank]
            require(len(choices)==1,'OWNER_AMBIGUOUS','Multiple sparse overrides have the same highest priority.')
            w=choices[0]
        if not w['writable']:missing.append({'action':c['action'],'context':c['context'],'status':'READ_ONLY_OWNER'});continue
        target=service.target(w['target_id']);field=next(f for f in target['spec']['fields'] if f['id']==w['field_id'])
        require(c['key'] in field['keys'],'KEY_UNSUPPORTED','Native key/chord encoding is not reviewed.')
        key=(w['target_id'],w['field_id']);prev=selected.get(key)
        require(prev is None or prev['key']==c['key'],'LINKED_CONTEXTS','One native scalar cannot receive different keys in different contexts.')
        selected[key]={'key':c['key'],'old':w['key']}
    # Ensure no hidden extra context of a shared scalar is modified by a partial intent.
    for (target,field),v in selected.items():
        if v['key']==v['old']:continue
        affected={(r['action'],r['slot'],r['context']) for r in all_rows if r['target_id']==target and r['field_id']==field}
        require(affected<=requested,'LINKED_CONTEXTS','One physical field covers additional contexts; include them explicitly.')
    if missing and not allow_partial:return {'status':'UNRESOLVED_ACTIONS','unresolved':missing,'items_request':[],'gameplay_verified':False}
    by_target={}
    for (target,field),v in selected.items():
        if v['key']!=v['old']:by_target.setdefault(target,{})[field]=v['key']
    if not by_target:return {'status':'NO_CHANGES','unresolved':missing,'items_request':[],'gameplay_verified':False}
    items=[{'target_id':t,'target_revision':service.target(t)['spec_sha256'],'changes':c} for t,c in sorted(by_target.items())]
    preview=service.preview(items)
    return {**preview,'instance_id':instance_id,'items_request':items,'unresolved':missing,'partial':bool(missing),'gameplay_verified':False}


def preset_preview(service,instance_id,preset_id,expected_revision):
    from .packs import load_pin
    rec=instance(service,instance_id);p=load_pin(service,rec['body']['pin']);slug(preset_id)
    matches=[x for x in p['presets'] if x['id']==preset_id and x['variant']==rec['body']['variant_id']]
    require(len(matches)==1,'PRESET_UNKNOWN','Choose a preset declared for this exact input variant.')
    return {**intent_preview(service,instance_id,matches[0]['changes'],expected_revision),'preset_id':preset_id}
