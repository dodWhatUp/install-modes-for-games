#!/usr/bin/env python3
"""Read-only before/after comparison for the two unchanged R8 families.
Supports exact native profile JSON, a list of profiles, a {'profiles': [...]} review
collection, and the known v2 backup ZIP. No app/store writes or imports occur.
A result describes the supplied snapshots, NOT their freshness or actual runtime.
"""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
from safe_io import ReviewError, canonical, read_regular, sha, strict_json, new_output, write_report, timestamp

APPROVED = {
 'CORE5': {'zip_sha256':'d4e3bb2b744e783a0172d6b8466b85bbc9d57c80c975f4af0cdeb7167d03ab0a','count':5},
 'SPARSE6': {'zip_sha256':'cc6d8368ec8c64cdc0ea1e69060779d8c4227fa6b9f9e1b1c7bc7d8ea2d0db33','count':6}
}
SLOTS=('', 'Long', 'Double')
PROFILE_MEMBER = re.compile(r'^storage/DevicesStorage/[^/]+/ProfileStorage/profile_[^/]+\.json$')


def bounded_zip(raw):
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
        infos=z.infolist()
        if len(infos)>1024 or len({i.filename for i in infos})!=len(infos):
            raise ReviewError('Too many archive entries or duplicate paths.')
        total=0; data={}
        for item in infos:
            name=item.filename;p=PurePosixPath(name)
            if '\\' in name or ':' in name or p.is_absolute() or '..' in p.parts or stat.S_ISLNK(item.external_attr>>16):
                raise ReviewError('Unsafe archive path or symlink.')
            if item.flag_bits&1:raise ReviewError('Encrypted archives need a supported route.')
            if item.is_dir():continue
            total+=item.file_size
            if item.file_size>8_000_000 or total>48_000_000:raise ReviewError('Expanded archive exceeds bound.')
            data[name]=z.read(item)
        z.close();return data
    except (zipfile.BadZipFile, RuntimeError, OSError) as e:
        raise ReviewError('Unusable archive; no repair or retry was attempted.') from e


def validate_profile(p):
    if not isinstance(p,dict) or not isinstance(p.get('id'),str) or not p['id'] or not isinstance(p.get('name'),str):
        raise ReviewError('Not a supported native profile object.')
    if not isinstance(p.get('inputs'),list) or not 1<=len(p['inputs'])<=256:
        raise ReviewError('Native input list is missing or unsupported.')
    if type(p.get('isSoftware')) is not bool:raise ReviewError('Profile does not declare SOFTWARE/onboard state.')
    ids=[]
    for b in p['inputs']:
        if not isinstance(b,dict) or type(b.get('id')) is not int:raise ReviewError('Invalid native button ID.')
        ids.append(b['id'])
        if not isinstance(b.get('types'),list) or len(b['types'])!=3:raise ReviewError('Unsupported native gesture slots.')
        for k,suffix in enumerate(SLOTS):
            if b['types'][k]=='24' and not isinstance(b.get('layeringProfileId'+suffix),str):
                raise ReviewError('Active Layering slot lacks a string target.')
    if len(set(ids))!=len(ids):raise ReviewError('Duplicate native button IDs.')


def profile_objects(obj):
    if isinstance(obj,dict) and 'inputs' in obj:profiles=[obj]
    elif isinstance(obj,list):profiles=obj
    elif isinstance(obj,dict) and set(obj).issubset({'profiles','snapshot_scope','created_utc'}) and isinstance(obj.get('profiles'),list):profiles=obj['profiles']
    else:raise ReviewError('Unsupported export wrapper; no recursive profile guessing.')
    if not 1<=len(profiles)<=256:raise ReviewError('Invalid profile count.')
    for p in profiles:validate_profile(p)
    return profiles


def snapshot(path):
    raw,meta=read_regular(Path(path),16_000_000)
    auxiliary={};manifest=None
    if raw[:2]==b'PK':
        members=bounded_zip(raw)
        native=[n for n in members if PROFILE_MEMBER.fullmatch(n)]
        if native:
            profiles=[strict_json(members[n]) for n in sorted(native)]
            auxiliary={n:sha(b) for n,b in members.items() if not PROFILE_MEMBER.fullmatch(n)}
            kind='KNOWN_V2_BACKUP_PROFILE_FILES'
            for p in profiles:validate_profile(p)
        elif 'MANIFEST_PRIVATE.json' in members:
            manifest=strict_json(members['MANIFEST_PRIVATE.json']);kind='CANDIDATE_DELIVERY'
            try:
                refs=manifest['data']['profiles'];names=[r['file'] for r in refs]
                if len(names)!=len(set(names)):raise ReviewError('Duplicate manifest profile path.')
                profiles=[]
                for row in refs:
                    b=members[row['file']]
                    if sha(b)!=row['sha256'] or len(b)!=row['bytes']:raise ReviewError('Manifest mismatch; do not import.')
                    p=strict_json(b);validate_profile(p);profiles.append(p)
                if set(n for n in members if n.startswith('profiles/') and n.endswith('.json'))!=set(names):
                    raise ReviewError('Unlisted profile file in delivery.')
            except (KeyError,TypeError) as e:raise ReviewError('Unrecognized candidate manifest.') from e
        else:raise ReviewError('Unsupported ZIP layout; not a native profile backup or family delivery.')
    else:profiles=profile_objects(strict_json(raw));kind='EXPLICIT_NATIVE_PROFILE_REVIEW_JSON'
    counts=Counter(p['id'] for p in profiles)
    if any(n!=1 for n in counts.values()):raise ReviewError('Duplicate profile IDs make the snapshot ambiguous.')
    return {'meta':meta,'format':kind,'profiles':profiles,'auxiliary_sha256':auxiliary,'manifest':manifest}


def expected(path,family):
    result=snapshot(path)
    if result['meta']['sha256']!=APPROVED[family]['zip_sha256']:raise ReviewError('Candidate is not the pinned R8 family. Reconcile before import.')
    if len(result['profiles'])!=APPROVED[family]['count']:raise ReviewError('Unexpected family size.')
    if result['manifest'].get('family')!=family:raise ReviewError('Wrong family selected.')
    return result


def op_object(p, names=None):
    """Conservative operational view. Ignore only identity and enumerated UI/time metadata.
    Preserve all unknown operational fields, joystick, pins, timing and gesture slots.
    Translate ACTIVE Layering IDs to unique names only when a complete snapshot provides them.
    """
    q=copy.deepcopy(p)
    for f in ['id','name','isFavorite','profileTags','systemTags']:q.pop(f,None)
    metadata=q.get('metaData')
    if isinstance(metadata,dict):
        for f in ['createdAt','createdBy','changedLogs']:metadata.pop(f,None)
    q['inputs']=sorted(q['inputs'],key=lambda b:b['id'])
    for b in q['inputs']:
        b.pop('label',None)
        if names is not None:
            for i,s in enumerate(SLOTS):
                if b['types'][i]=='24':
                    target=b.get('layeringProfileId'+s,'')
                    b['layeringProfileId'+s]=names.get(target,'UNRESOLVED_ID:'+target)
    return q


def name_map(profiles):
    counts=Counter(p['name'] for p in profiles)
    return {p['id']:'UNIQUE_NAME:'+p['name'] for p in profiles if counts[p['name']]==1}


def field_diffs(a,b,path='',limit=40):
    results=[]
    def visit(x,y,p):
        if len(results)>=limit:return
        if type(x)!=type(y):results.append(p or '/');return
        if isinstance(x,dict):
            for k in sorted(set(x)|set(y)):
                np=p+'/'+str(k)
                if k not in x or k not in y:results.append(np)
                else:visit(x[k],y[k],np)
                if len(results)>=limit:return
        elif isinstance(x,list):
            if len(x)!=len(y):results.append(p+'/length')
            for i,(v,w) in enumerate(zip(x,y)):visit(v,w,p+'/'+str(i))
        elif x!=y:results.append(p or '/')
    visit(a,b,path);return results


def active_links(profiles):
    by={p['id']:p for p in profiles};links=[]
    for p in profiles:
        for b in p['inputs']:
            for i,s in enumerate(SLOTS):
                if b['types'][i]=='24':
                    target=b.get('layeringProfileId'+s,'')
                    links.append({'profile_id':p['id'],'profile_name':p['name'],'button_id':b['id'],
                        'gesture_slot':i,'target_id':target,'target_name':by[target]['name'] if target in by else None,
                        'target_resolves_in_supplied_snapshot':target in by,'toggle_on_hold':b.get('isToggleOnHold'+s)})
    return links


def compare_family(wanted,current,family):
    cp=current['profiles'];wp=wanted['profiles'];ids={p['id']:p for p in cp};cnames=name_map(cp);wnames=name_map(wp)
    rows=[]
    for p in wp:
        same_name=[x for x in cp if x['name']==p['name']];same_id=ids.get(p['id'])
        result={'name':p['name'],'candidate_id':p['id'],'current_id':None,'status':None,'different_fields':[]}
        if same_id is not None and same_id['name']!=p['name']:
            result['status']='ID_COLLISION_DIFFERENT_NAME_STOP'
        elif len(same_name)>1:
            result['status']='DUPLICATE_NAMES_STOP'
        elif same_id is None and not same_name:
            result['status']='NOT_PRESENT'
        else:
            actual=same_id if same_id is not None else same_name[0];result['current_id']=actual['id']
            before=op_object(p,wnames);after=op_object(actual,cnames)
            if before==after:
                result['status']='ALREADY_MATCHES' if actual['id']==p['id'] else 'MATCHES_WITH_REMAPPED_ID'
                result['metadata_or_label_differences']=canonical(p)!=canonical(actual)
            else:
                result['status']='EXISTING_DIFFERENT_STOP';result['different_fields']=field_diffs(before,after)
        rows.append(result)
    stats=Counter(x['status'] for x in rows)
    if any(x.endswith('_STOP') for x in stats):decision='STOP_RECONCILE_EXISTING_STATE'
    elif stats.get('NOT_PRESENT',0)==len(rows):decision='ALL_ABSENT_IMPORT_REMAINS_A_SEPARATE_ACTION'
    elif stats.get('NOT_PRESENT',0):decision='PARTIAL_PRESENCE_RECONCILE_BEFORE_ANY_IMPORT'
    else:decision='FAMILY_MATCHES_SUPPLIED_SNAPSHOT_DO_NOT_REIMPORT'
    candidate_ids={r['current_id'] for r in rows if r['current_id']}
    related_links=[x for x in active_links(cp) if x['profile_id'] in candidate_ids]
    return {'family':family,'decision':decision,'rows':rows,'counts':dict(stats),'matched_family_links':related_links,
            'native_runtime_verified':False,'physical_verified':False,'import_executed':False}


def preservation(before,after,family):
    """Never excuse a change to a pre-existing native profile, including a selected-family profile."""
    ai={p['id']:p for p in after['profiles']};rows=[]
    for p in before['profiles']:
        actual=ai.get(p['id'])
        if actual is None:status='MISSING_AFTER_STOP'
        elif canonical(actual)==canonical(p):status='UNCHANGED'
        elif op_object(actual)==op_object(p):status='METADATA_ONLY_DIFFERENCE_REVIEW'
        else:status='OPERATIONAL_CHANGE_STOP'
        rows.append({'profile_id':p['id'],'name':p['name'],'status':status,
                     'different_fields':[] if actual is None or status=='UNCHANGED' else field_diffs(p,actual)})
    oldids={p['id'] for p in before['profiles']}
    additions=[{'id':p['id'],'name':p['name']} for p in after['profiles'] if p['id'] not in oldids]
    aux_before=before['auxiliary_sha256'];aux_after=after['auxiliary_sha256']
    auxiliary={'comparable':bool(aux_before and aux_after),'changed_members':[]}
    if auxiliary['comparable']:
        auxiliary['changed_members']=[n for n in sorted(set(aux_before)|set(aux_after)) if aux_before.get(n)!=aux_after.get(n)]
    return {'prior_profiles':rows,'added_profiles':additions,'all_prior_profile_json_values_equal':all(x['status']=='UNCHANGED' for x in rows),
            'all_prior_operational_fields_preserved':all(x['status'] in {'UNCHANGED','METADATA_ONLY_DIFFERENCE_REVIEW'} for x in rows),
            'auxiliary_files':auxiliary,'scope':'Only supplied export files. No live state or full-store restore approval follows.'}


def run(candidate,current,family,out,before=None,snapshot_scope='user-export-not-live-verified'):
    want=expected(candidate,family);now=snapshot(current);old=snapshot(before) if before else None
    report={'schema':'azeron-native-review/v1','created_utc':timestamp(),'status':'READ_ONLY_SNAPSHOT_REVIEW',
      'snapshot_scope':snapshot_scope,'candidate_source':want['meta'],'current_source':now['meta'],
      'current_format':now['format'],'current_profile_count':len(now['profiles']),
      'family_review':compare_family(want,now,family),'current_unresolved_links':[x for x in active_links(now['profiles']) if not x['target_resolves_in_supplied_snapshot']],
      'preservation':preservation(old,now,family) if old else None,
      'limits':['Not an importer or editor; source files are never written.',
               'Profile names/IDs are private review data; do not commit receipts to public Git.',
               'Declared snapshot scope does not establish current Windows state.',
               'Metadata/label differences are separated; unknown operational fields are compared conservatively.',
               'All supplied profiles are considered, not only the proposed family.'],
      'native_import_tested':False,'device_input_tested':False,'gameplay_tested':False}
    # Verify selected snapshot bytes are still the same before writing a result.
    for path,meta in [(candidate,want['meta']),(current,now['meta'])]+([(before,old['meta'])] if old else []):
        if read_regular(Path(path),16_000_000)[1]['sha256']!=meta['sha256']:raise ReviewError('Snapshot changed before report publication.')
    write_report(new_output(out),'NATIVE_REVIEW.json',report);return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--current',type=Path,required=True);p.add_argument('--family',choices=list(APPROVED),required=True)
    p.add_argument('--before',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--snapshot-scope',choices=['historical-backup','user-export-not-live-verified','synthetic-test'],default='user-export-not-live-verified')
    a=p.parse_args()
    try:r=run(a.candidate,a.current,a.family,a.out,a.before,a.snapshot_scope)
    except (ReviewError,OSError) as e:raise SystemExit('STOP: '+str(e))
    print(json.dumps({'decision':r['family_review']['decision'],'profiles_read':r['current_profile_count'],'report':'NATIVE_REVIEW.json','live_verified':False}))
