#!/usr/bin/env python3
"""Independent native readback + reproducible compilation. Never imports profiles."""
import argparse,collections,hashlib,json,re,tempfile,subprocess,sys,zipfile
from pathlib import Path
P=Path(__file__).parent
SPECIAL={'Escape':'Esc','Space':'Space','Enter':'Enter','Tab':'Tab','Backspace':'Backspace','CapsLock':'Caps Lock','PageUp':'Page Up','PageDown':'Page Down','Home':'Home','End':'End','Insert':'Insert','Delete':'Delete','ArrowUp':'Up Arrow','ArrowDown':'Down Arrow','ArrowLeft':'Left Arrow','ArrowRight':'Right Arrow','Minus':'Minus','Equal':'Equals','Backquote':'Backtick','BracketLeft':'Left Bracket','BracketRight':'Right Bracket','Comma':'Comma','Period':'Period','Slash':'Slash','Backslash':'Backslash','Semicolon':'Semicolon','Quote':'Apostrophe'}
MOD={'ControlLeft':'Ctrl','ShiftLeft':'Shift','AltLeft':'Alt'}
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(source,design,native,prior,output,original=None):
 d=load(design);base=load(source);m=load(native/'MANIFEST_PRIVATE.json');src={b['id']:b for b in base['inputs']}
 assert m['source_sha256']==sha(source) and m['design_sha256']==sha(design)
 seen=set();oldids=set();oldhash={}
 for root in prior:
  for f in root.rglob('*.json'):
   oldhash[str(f)]=sha(f)
   try:q=load(f)
   except (ValueError,UnicodeError):continue
   if isinstance(q,dict) and 'inputs' in q and 'id' in q:oldids.add(q['id'])
 original_count=0;original_sha=None
 if original:
  original_sha=sha(original)
  with zipfile.ZipFile(original) as z:
   for name in z.namelist():
    if '/profile_' in name and name.endswith('.json'):
     q=json.loads(z.read(name));oldids.add(q['id']);original_count+=1
 results=[];pos=d['position_map'];hidden=set(src)-set(pos.values())
 for family,v in d['variants'].items():
  fm=m['families'][family];ids=set(fm['profile_ids'].values());assert len(ids)==len(v['maps']) and not ids&(seen|oldids);seen|=ids
  stats=collections.Counter();outputs=set('WASD');actual_links=[]
  for record in fm['profiles']:
   path=native/family/record['file'];p=load(path);bank=record['layer'];b={x['id']:x for x in p['inputs']}
   assert sha(path)==record['sha256'] and path.stat().st_size==record['bytes']
   assert p['id']==fm['profile_ids'][bank] and p['name']==v['profile_prefix']+' - '+bank
   assert p['isSoftware'] and not p['profileTags'] and len(b)==43 and set(b)==set(src)
   for field in base:
    if field not in {'id','name','profileTags','isFavorite','isSoftware','systemTags','metaData','inputs'}:assert p[field]==base[field],field
   for n in hidden:assert b[n]==src[n],(family,bank,n,'nonvisual modified')
   for n,x in b.items():
    for f in ('id','pinOne','pinTwo'):assert x[f]==src[n][f]
    for i,suffix in enumerate(['','Long','Double']):
     if x['types'][i]=='24':assert x['layeringProfileId'+suffix] in ids,(family,bank,n,'external layer reference')
   for vp,k in v['maps'][bank].items():
    n=pos[vp];x=b[n];stats['digital_cells']+=1
    assert x['types'][1:]==['11','11']
    for suf in ['Long','Double']:
     assert x['keyValues'+suf]==['0']*4 and x['metaValues'+suf]==['0']*3 and not x['layeringProfileId'+suf]
     assert not x['isToggleOnHold'+suf] and not x['isHold'+suf] and not x['isTurbo'+suf]
    assert all(x[f]=={'repeat':False,'steps':[],'v':1} for f in ['macro','longMacro','doubleMacro'])
    assert x['sequenceTriggerSettings']=={'sequenceSteps':[],'isPingPongLoop':False}
    assert not x['isTurbo'] and not x['isHold'] and not x['isBelkin']
    if k=='UNASSIGNED':
     assert x['types']==['11']*3 and not x['isToggleOnHold'];assert x['keyValues']==['0']*4 and x['metaValues']==['0']*3 and not x['layeringProfileId'];stats['disabled']+=1
    elif k.startswith('LAYER:'):
     dest=k[6:] if bank=='BASIC' else 'BASIC';assert x['types']==['24','11','11'] and x['isToggleOnHold']
     assert x['layeringProfileId']==fm['profile_ids'][dest]
     assert n==v['selectors'][dest if bank=='BASIC' else bank]
     actual_links.append((bank,n,dest));stats['links']+=1
    else:
     assert x['types']==['1','11','11'] and not x['isToggleOnHold'];kv=[x for x in x['keyValues'] if x!='0'];mv=[x for x in b[n]['metaValues'] if x!='0']
     if mv:assert len(mv)==1 and not kv;decoded=MOD[mv[0]]
     else:
      assert len(kv)==1;z=kv[0]
      decoded=z[3:] if re.fullmatch('Key[A-Z]',z) else z[5:] if re.fullmatch('Digit[0-9]',z) else SPECIAL.get(z,z)
     assert decoded==k,(family,bank,n,k,decoded);outputs.add(decoded);stats['keyboard_cells']+=1
   assert b[19]['types']==['11']*3 and not b[19]['label']
   for n,key in [(5,'Ctrl'),(9,'Shift'),(14,'Space')]:
    assert v['maps'][bank][next(p for p,i in pos.items() if i==n)]==key
  assert outputs==set(d['target_outputs']) and len(outputs)==78
  assert stats['links']==2*(len(v['maps'])-1)
  for l,n in v['selectors'].items():assert ('BASIC',n,l) in actual_links and (l,n,'BASIC') in actual_links
  if family=='SPARSE6':
   for l,mask in d['source_sensitive_mask'].items():
    assert all(v['maps'][l][next(p for p,i in pos.items() if i==n)]=='UNASSIGNED' for n in mask)
  results.append({'family':family,'profiles':len(v['maps']),'input_records':43*len(v['maps']),**dict(stats),'outputs':78,'all_nonvisual_records_preserved':True,'ids_disjoint_from_priors':True,'reserved19_disabled':True,'Ctrl_Shift_Space_same_positions_all_layers':True})
 # Deterministic compiler repeat; no existing output directory is touched.
 with tempfile.TemporaryDirectory() as td:
  run=subprocess.run([sys.executable,str(P/'compile_profiles.py'),'--source',str(source),'--design',str(design),'--out',str(Path(td)/'native')],capture_output=True,text=True)
  assert run.returncode==0,run.stderr
  new=Path(td)/'native';files=sorted(native.rglob('*.json'))
  for f in files:assert f.read_bytes()==(new/f.relative_to(native)).read_bytes(),f
 assert all(sha(Path(f))==h for f,h in oldhash.items())
 result={'revision':'R8','status':'NATIVE_STRUCTURE_AND_REBUILD_PASS_NOT_RUNTIME','families':results,'profile_files':sum(x['profiles'] for x in results),'digital_cells':sum(x['digital_cells'] for x in results),'native_input_records':sum(x['input_records'] for x in results),'directed_links':sum(x['links'] for x in results),'deterministic_repeat_byte_identical':True,'prior_files_checked_unchanged':len(oldhash),'original_native_profiles_checked':original_count,'original_archive_sha256':original_sha,'native_import_tested':False,'physical_tested':False,'gameplay_tested':False,'current_live_backup':False}
 if original:assert sha(original)==original_sha
 output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--design',type=Path,required=True);a.add_argument('--native',type=Path,required=True);a.add_argument('--prior',type=Path,action='append',default=[]);a.add_argument('--output',type=Path,required=True);a.add_argument('--original',type=Path);x=a.parse_args();check(x.source,x.design,x.native,x.prior,x.output,x.original)
