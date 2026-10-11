#!/usr/bin/env python3
"""Compile additive Azeron 2.0.2 candidates from an exact supplied native source.
No live import/store editing. Repeated identical inputs give identical UUIDs.
"""
import argparse,copy,datetime,hashlib,json,re,uuid
from pathlib import Path
KEYS={'Esc':'Escape','Space':'Space','Enter':'Enter','Tab':'Tab','Backspace':'Backspace','Caps Lock':'CapsLock','Page Up':'PageUp','Page Down':'PageDown','Home':'Home','End':'End','Insert':'Insert','Delete':'Delete','Up Arrow':'ArrowUp','Down Arrow':'ArrowDown','Left Arrow':'ArrowLeft','Right Arrow':'ArrowRight','Minus':'Minus','Equals':'Equal','Backtick':'Backquote','Left Bracket':'BracketLeft','Right Bracket':'BracketRight','Comma':'Comma','Period':'Period','Slash':'Slash','Backslash':'Backslash','Semicolon':'Semicolon','Apostrophe':'Quote'}
MOD={'Ctrl':'ControlLeft','Shift':'ShiftLeft','Alt':'AltLeft'}
NS=uuid.UUID('76e27431-a2fd-4a29-935c-15dd09ebeb55')
def sha(b):return hashlib.sha256(b).hexdigest()
def dump(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def code(k):
 if k in KEYS:return KEYS[k]
 if re.fullmatch('[A-Z]',k):return 'Key'+k
 if re.fullmatch('[0-9]',k):return 'Digit'+k
 if re.fullmatch(r'F(?:[1-9]|1[0-2])',k):return k
 raise ValueError('unsupported keyboard output: '+k)
def compile(source,design,out):
 if out.exists():raise FileExistsError('New output directory required; refusing overwrite')
 raw=source.read_bytes();dr=design.read_bytes();base=json.loads(raw);d=json.loads(dr)
 if base.get('metaData',{}).get('createdBy')!='2.0.2' or base['metaData']['device']!=8 or not base['isSoftware']:raise ValueError('Source schema/model mismatch')
 if d['revision']!='R8' or len(d['position_map'])!=30:raise ValueError('Design mismatch')
 by={b['id']:b for b in base['inputs']};assert len(by)==43
 stamp='2026-10-11T00:00:00.000Z' # Revision date, not a live observation timestamp.
 fingerprint=sha(raw)+':'+sha(dr)
 manifest={'revision':'R8','status':'GENERATED_NOT_IMPORTED','source_sha256':sha(raw),'design_sha256':sha(dr),'native_source_version':'2.0.2','uuid_policy':'uuid5 over namespace/source/design/family/layer','families':{},'live_changes':False}
 out.mkdir(parents=True)
 def empty(n):
  x=copy.deepcopy(by[n]);x['types']=['11']*3;x['label']=''
  for s in ('','Long','Double'):
   x['keyValues'+s]=['0']*4;x['metaValues'+s]=['0']*3;x['layeringProfileId'+s]=''
   for k in ['isBelkin','isToggleOnHold','isHold','isTurbo']:x[k+s]=False
   for k in ['holdTime','turboInterval']:x[k+s]=0
  for k in ['macro','longMacro','doubleMacro']:x[k]={'repeat':False,'steps':[],'v':1}
  x['sequenceTriggerSettings']={'sequenceSteps':[],'isPingPongLoop':False};return x
 for family,v in d['variants'].items():
  ids={l:str(uuid.uuid5(NS,fingerprint+':'+family+':'+l)) for l in v['maps']};folder=out/family/'profiles';folder.mkdir(parents=True)
  fm={'profile_ids':ids,'profiles':[],'links':[]}
  for i,(layer,bank) in enumerate(v['maps'].items(),1):
   p=copy.deepcopy(base);p.update(id=ids[layer],name=v['profile_prefix']+' - '+layer,profileTags=[],isFavorite=False,isSoftware=True,systemTags=['LAYERING'])
   p['metaData']={'schemeName':base['metaData']['schemeName'],'device':8,'createdAt':stamp,'createdBy':'2.0.2','changedLogs':[{'timestampt':stamp,'softwareVersion':'2.0.2','type':'created'}]}
   nb=copy.deepcopy(by)
   for pos,k in bank.items():
    n=d['position_map'][pos];x=empty(n)
    if k.startswith('LAYER:'):
     target=k[6:] if layer=='BASIC' else 'BASIC'
     assert n==v['selectors'][target if layer=='BASIC' else layer]
     x.update(types=['24','11','11'],layeringProfileId=ids[target],isToggleOnHold=True,label=(target+' - HOLD' if layer=='BASIC' else 'RETURN TO BASIC'))
     fm['links'].append({'source':layer,'button_id':n,'target':target})
    elif k!='UNASSIGNED':
     x['types']=['1','11','11'];x['label']=k
     if k in MOD:x['metaValues'][0]=MOD[k]
     else:x['keyValues'][0]=code(k)
    nb[n]=x
   p['inputs']=[nb[b['id']] for b in base['inputs']]
   b=dump(p);filename=f'{i:02d}_SHARED_R8_{family}_{layer}.json';(folder/filename).write_bytes(b)
   fm['profiles'].append({'layer':layer,'name':p['name'],'file':'profiles/'+filename,'sha256':sha(b),'bytes':len(b)})
  manifest['families'][family]=fm
 (out/'MANIFEST_PRIVATE.json').write_bytes(dump(manifest));return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--design',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args();r=compile(x.source,x.design,x.out);print({k:len(v['profiles']) for k,v in r['families'].items()})
