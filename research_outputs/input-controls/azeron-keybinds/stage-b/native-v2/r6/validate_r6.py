#!/usr/bin/env python3
"""Independent readback of generated native files. No app/device actions."""
import argparse,collections,hashlib,json,zipfile
from pathlib import Path

def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def validate(source,design,root,original):
 base=load(source);d=load(design);man=load(root/'MANIFEST_PRIVATE.json');by={x['id']:x for x in base['inputs']}
 assert sha(source)==man['source_profile_sha256'] and sha(design)==man['design_sha256']
 pos=d['position_map'];visible=set(pos.values());seenids=set();out=[]
 inv={'Escape':'Esc','Space':'Space','Enter':'Enter','Tab':'Tab','Backspace':'Backspace','CapsLock':'Caps Lock','PageUp':'Page Up','PageDown':'Page Down','Home':'Home','End':'End','Insert':'Insert','Delete':'Delete','ArrowUp':'Up Arrow','ArrowDown':'Down Arrow','ArrowLeft':'Left Arrow','ArrowRight':'Right Arrow','Minus':'Minus','Equal':'Equals','Backquote':'Backtick','BracketLeft':'Left Bracket','BracketRight':'Right Bracket','Comma':'Comma','Period':'Period','Slash':'Slash','Backslash':'Backslash','Semicolon':'Semicolon','Quote':'Apostrophe'}
 mod={'ControlLeft':'Ctrl','ShiftLeft':'Shift','AltLeft':'Alt'}
 source_sha=sha(original)
 prior_r5={load(p)['id'] for p in source.parent.glob('*.json')}
 assert len(prior_r5)==4, 'Expected complete R5 source family in source directory'
 with zipfile.ZipFile(original) as z:
  oldprofiles=[json.loads(z.read(n)) for n in z.namelist() if '/profile_' in n and n.endswith('.json')]
  originals={p['id'] for p in oldprofiles}
  masks={ 'NUMBERS':('LAYER - 1 NUMBER',[38,13,18]), 'MENUS':('LAYER - 1 MENU',[7,11,16]), 'TOOLS':('LAYER - 1 MOD KEYS',[8,12,17])}
  mask_checks=[]
  for l,(n,ids) in masks.items():
   p=next(p for p in oldprofiles if p['name']==n);b={x['id']:x for x in p['inputs']}
   assert all(b[i]['types']==['11','11','11'] for i in ids)
   mask_checks.append({'layer':l,'ids':ids,'source_disabled_types':True,'dormant_key_values_not_counted':True})
 for fam,v in d['variants'].items():
  m=man['families'][fam]; idset=set(m['profile_ids'].values());assert not idset&(originals|prior_r5|seenids);seenids|=idset
  counts=collections.Counter();keys=set('WASD');links=[]
  for pf in m['profiles']:
   p=load(root/fam/pf['file']);bank=pf['layer'];b={x['id']:x for x in p['inputs']}
   assert sha(root/fam/pf['file'])==pf['sha256']
   assert p['id']==m['profile_ids'][bank] and p['profileTags']==[] and p['isSoftware']
   assert len(p['inputs'])==43 and set(b)==set(by)
   for x in p['inputs']:
    for i,suffix in enumerate(['','Long','Double']):
     if x['types'][i]=='24':assert x['layeringProfileId'+suffix] in idset, 'Active reference escapes family'
   for f in base:
    if f not in ['id','name','profileTags','isFavorite','isSoftware','systemTags','metaData','inputs']:
     assert p[f]==base[f],(bank,f)
   for n,x in b.items():
    for f in ['id','pinOne','pinTwo']:assert x[f]==by[n][f]
    if n not in visible:assert x==by[n];continue
    counts['visible_cells']+=1
    assert x['types'][1:]==['11','11']
    for s in ['','Long','Double']:
     assert not x['isHold'+s] and not x['isTurbo'+s] and not x['isBelkin'+s]
     if s:assert x['keyValues'+s]==['0']*4 and x['metaValues'+s]==['0']*3 and x['layeringProfileId'+s]==''
    assert all(not x[k]['steps'] for k in ['macro','longMacro','doubleMacro'])
    assert not x['sequenceTriggerSettings']['sequenceSteps']
    vp=next(k for k,i in pos.items() if i==n);k=v['maps'][bank][vp]
    if k=='UNASSIGNED':
     assert x['types']==['11']*3 and x['keyValues']==['0']*4 and x['metaValues']==['0']*3
     assert x['layeringProfileId']=='' and not x['isToggleOnHold'];counts['disabled']+=1
    elif k.startswith('LAYER:'):
     assert x['types']==['24','11','11'] and x['isToggleOnHold']
     target=k[6:] if bank=='BASIC' else 'BASIC'
     assert x['layeringProfileId']==m['profile_ids'][target]
     assert n==v['selectors'][target if bank=='BASIC' else bank]
     links.append((bank,n,target));counts['links']+=1
    else:
     assert x['types']==['1','11','11'] and not x['isToggleOnHold']
     meta=[z for z in x['metaValues'] if z!='0'];kv=[z for z in x['keyValues'] if z!='0']
     if meta:assert len(meta)==1 and not kv;dec=mod[meta[0]]
     else:
      assert len(kv)==1
      z=kv[0];dec=z[3:] if z.startswith('Key') else z[5:] if z.startswith('Digit') else inv.get(z,z)
     assert dec==k,(fam,bank,n,dec,k);keys.add(dec);counts['keyboard_cells']+=1
   assert b[19]['types']==['11']*3 and b[19]['label']==''
  assert keys==set(d['target_outputs']) and len(keys)==78
  assert counts['visible_cells']==30*len(v['maps']) and counts['links']==2*(len(v['maps'])-1)
  for target,n in v['selectors'].items():assert ('BASIC',n,target) in links and (target,n,'BASIC') in links
  if fam=='SPARSE':
   for l,(_,ids) in masks.items():
    for i in ids:assert v['maps'][l][next(p for p,j in pos.items() if j==i)]=='UNASSIGNED'
  out.append({'family':fam,'profiles':len(v['maps']),'input_records':43*len(v['maps']),'counts':dict(counts),'unique_outputs_including_WASD':len(keys),'reserved_19_disabled_every_layer':True,'all_nonvisual_inputs_and_joystick_preserved':True,'all_metadata_pins_ids_checked':True,'cross_family_links':0,'all_43_records_active_links_checked':True,'uuid_disjoint_from_original18_and_r5':True})
 assert sha(original)==source_sha
 result={'status':'NATIVE_STRUCTURE_READBACK_PASS_NOT_IMPORT_OR_RUNTIME','revision':'R6','families':out,'source_mask_checks':mask_checks,'original_backup_sha256':source_sha,'original_profiles_unchanged_count':len(oldprofiles),'source_and_r5_readonly':True,'native_import_tested':False,'hardware_tested':False,'gameplay_tested':False,'screen_capture_used':False}
 (root/'QA_NATIVE_R6.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source-r5',type=Path,required=True);a.add_argument('--design',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--original-backup',type=Path,required=True);x=a.parse_args();validate(x.source_r5,x.design,x.output,x.original_backup)
