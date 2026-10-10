#!/usr/bin/env python3
"""Create NEW native-structure R6 candidates from an unchanged R5 delivery profile.
No live app access; no import; no backup restore. Python standard library only.
The native input schema is inherited from the supplied 2.0.2 backup and checked.
"""
import argparse, copy, datetime, hashlib, json, re, uuid
from pathlib import Path

SPECIAL={'Esc':'Escape','Space':'Space','Enter':'Enter','Tab':'Tab','Backspace':'Backspace','Caps Lock':'CapsLock','Page Up':'PageUp','Page Down':'PageDown','Home':'Home','End':'End','Insert':'Insert','Delete':'Delete','Up Arrow':'ArrowUp','Down Arrow':'ArrowDown','Left Arrow':'ArrowLeft','Right Arrow':'ArrowRight','Minus':'Minus','Equals':'Equal','Backtick':'Backquote','Left Bracket':'BracketLeft','Right Bracket':'BracketRight','Comma':'Comma','Period':'Period','Slash':'Slash','Backslash':'Backslash','Semicolon':'Semicolon','Apostrophe':'Quote'}
MOD={'Ctrl':'ControlLeft','Shift':'ShiftLeft','Alt':'AltLeft'}
def serial(x):return (json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode()
def h(x):return hashlib.sha256(x).hexdigest()
def code(k):
 if k in SPECIAL:return SPECIAL[k]
 if re.fullmatch('[A-Z]',k):return 'Key'+k
 if re.fullmatch('[0-9]',k):return 'Digit'+k
 if re.fullmatch(r'F(?:[1-9]|1[0-2])',k):return k
 raise ValueError('Unknown output: '+k)

def build(source,design,output):
 raw=source.read_bytes();dr=design.read_bytes();base=json.loads(raw);d=json.loads(dr)
 assert base['metaData']['createdBy']=='2.0.2' and base['metaData']['device']==8
 assert base['name']=='SHARED R5 - BASIC' and base['isSoftware']
 assert d['revision']=='R6' and d['reserved_button']['id']==19
 by={b['id']:b for b in base['inputs']};pos=d['position_map'];assert len(by)==43 and len(pos)==30
 assert len(set(pos.values()))==30 and 24 not in pos.values()
 output.mkdir(parents=True,exist_ok=False)
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
 manifest={'revision':'R6','status':'FILES_GENERATED_NOT_IMPORTED','created_at':stamp,
  'source_profile_sha256':h(raw),'design_sha256':h(dr),'source_version':'2.0.2',
  'live_device_or_game_changed':False,'single_profile_import_tested':False,
  'reserved_button':19,'families':{},'warning':'Choose one family. Do not treat ZIP as backup restore. The reserved disabled key emits no keyboard hotkey.'}
 def empty(n):
  x=copy.deepcopy(by[n]);x['types']=['11','11','11'];x['label']=''
  for s in ('','Long','Double'):
   x['keyValues'+s]=['0']*4;x['metaValues'+s]=['0']*3;x['layeringProfileId'+s]=''
   for f in ['isBelkin','isToggleOnHold','isHold','isTurbo']:x[f+s]=False
   for f in ['holdTime','turboInterval']:x[f+s]=0
  for f in ['macro','longMacro','doubleMacro']:x[f]={'repeat':False,'steps':[],'v':1}
  x['sequenceTriggerSettings']={'sequenceSteps':[],'isPingPongLoop':False}
  return x
 allids={base['id']}
 for family,v in d['variants'].items():
  ids={l:str(uuid.uuid4()) for l in v['maps']};assert not set(ids.values())&allids;allids.update(ids.values())
  target_dir=output/family/'profiles';target_dir.mkdir(parents=True)
  fm={'profile_ids':ids,'profiles':[],'links':[],'layer_count':len(ids),'outputs':v['unique_logical_outputs']}
  for i,(layer,bank) in enumerate(v['maps'].items(),1):
   p=copy.deepcopy(base);p['id']=ids[layer];p['name']=v['profile_prefix']+' - '+layer
   p['profileTags']=[];p['isFavorite']=False;p['isSoftware']=True;p['systemTags']=['LAYERING']
   p['metaData']={'schemeName':base['metaData']['schemeName'],'device':8,'createdAt':stamp,'createdBy':'2.0.2',
      'changedLogs':[{'timestampt':stamp,'softwareVersion':'2.0.2','type':'created'}]}
   nb=copy.deepcopy(by)
   for vp,k in bank.items():
    n=pos[vp];x=empty(n)
    if k.startswith('LAYER:'):
     requested=k[6:]
     if layer=='BASIC':
      assert v['selectors'][requested]==n;target=requested
     else:
      assert v['selectors'][layer]==n and requested==layer;target='BASIC'
     x.update(types=['24','11','11'],layeringProfileId=ids[target],isToggleOnHold=True,isBelkin=False,
        label=target+' - HOLD' if layer=='BASIC' else 'RETURN TO BASIC')
     fm['links'].append({'source':layer,'button_id':n,'target':target})
    elif k!='UNASSIGNED':
     x['types']=['1','11','11'];x['label']=k
     if k in MOD:x['metaValues'][0]=MOD[k]
     else:x['keyValues'][0]=code(k)
    nb[n]=x
   p['inputs']=[nb[x['id']] for x in base['inputs']]
   filename=f'{i:02d}_SHARED_R6_{family}_{layer}.json';b=serial(p);(target_dir/filename).write_bytes(b)
   fm['profiles'].append({'name':p['name'],'layer':layer,'file':'profiles/'+filename,'bytes':len(b),'sha256':h(b)})
  manifest['families'][family]=fm
 (output/'MANIFEST_PRIVATE.json').write_bytes(serial(manifest))
 print(json.dumps({f: {'profiles':len(m['profiles']),'links':len(m['links'])} for f,m in manifest['families'].items()}))
 return manifest
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source-r5',type=Path,required=True);a.add_argument('--design',type=Path,required=True);a.add_argument('--output',type=Path,required=True);x=a.parse_args();build(x.source_r5,x.design,x.output)
