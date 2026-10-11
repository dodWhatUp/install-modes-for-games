#!/usr/bin/env python3
"""Read-only, bounded game input evidence collector. Python 3.9+.
Never launches a game, changes a config, reads saves, logs keys, or installs.
An explicit file path is required for each source. Output must be a NEW folder.
Collected rows are CONFIG_CANDIDATE, never automatically EFFECTIVE_VERIFIED.
"""
import argparse,datetime,hashlib,json,os,re,stat,xml.etree.ElementTree as ET
from pathlib import Path
MAX_BYTES=8_000_000
POE_SECTIONS={'ACTION_KEYS','WASD_ACTION_KEYS'}
MODE_FIELDS={
 'GENERAL':{'user_input_mode','last_selected_KBM_input_mode','auto_input_method_switching','update_action_location_after_release'},
 'UI':{'use_wasd_to_move','attack_in_place_key_stops_move','sprint_continues_with_move_input','precise_projectile_cursor_targeting','always_highlight','key_pickup'}
}
class EvidenceError(ValueError):pass

def safe_read(path):
 path=Path(path)
 if path.is_symlink() or not path.is_file():raise EvidenceError('Expected a regular non-symlink input file')
 st=path.stat()
 if st.st_size>MAX_BYTES:raise EvidenceError('Input exceeds size bound')
 with path.open('rb') as f:raw=f.read(MAX_BYTES+1)
 after=path.stat()
 if len(raw)>MAX_BYTES or (st.st_size,st.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise EvidenceError('Input changed during read or exceeds bound; inspect before retry')
 try:raw.decode('utf-8-sig')
 except UnicodeDecodeError:raise EvidenceError('Unsupported text encoding; do not guess binary conversion')
 meta={'basename':path.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'mtime_utc':datetime.datetime.fromtimestamp(st.st_mtime,datetime.timezone.utc).isoformat()}
 return raw,meta

def poe(raw):
 sections={};mode={};warnings=[];section='';seen=set()
 for line_no,line in enumerate(raw.decode('utf-8-sig').splitlines(),1):
  t=line.strip()
  if not t or t[0] in '#;':continue
  if t.startswith('[') and t.endswith(']'):section=t[1:-1];continue
  if '=' not in t:continue
  key,val=t.split('=',1);key=key.strip();val=val.strip()
  if section in POE_SECTIONS:
   if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,95}',key):warnings.append({'line':line_no,'reason':'unsupported action identifier omitted'});continue
   identity=(section,key)
   if identity in seen:raise EvidenceError('Duplicate action key in one section; no last-value guessing')
   seen.add(identity)
   # Only numeric input encodings are permitted into the receipt. Not arbitrary text.
   if not re.fullmatch(r'\d{1,5}(?:\s+\d{1,5}){0,3}',val):
    warnings.append({'section':section,'action_id':key,'line':line_no,'reason':'non-numeric encoding omitted; schema review needed'});continue
   nums=[int(x) for x in val.split()]
   sections.setdefault(section,[]).append({'action_id':key,'raw_encoding':val,'numeric_tokens':nums,'base_code_candidate':nums[0],
    'modifier_tokens_unresolved':nums[1:],'decode_status':'RAW_NOT_GAME_VALIDATED','binding_state':'UNASSIGNED_CANDIDATE' if nums==[0] else 'CONFIGURED_CANDIDATE'})
  elif section in MODE_FIELDS and key in MODE_FIELDS[section]:
   if not re.fullmatch(r'[A-Za-z0-9_.-]{1,64}',val):warnings.append({'line':line_no,'reason':'non-scalar input mode omitted'});continue
   mode.setdefault(section,{})[key]=val
 if not sections:raise EvidenceError('No supported PoE2 input sections found')
 return {'parser':'poe2_numeric_sections/v1','sections':sections,'input_mode_evidence':mode,'selected_section':None,
  'warnings':warnings,'requires':['Reconcile input mode indicators and current game context.','Confirm base-code encoding and modifier bit meanings; numeric similarity to Windows VK is not validation.','Skill slot identity is not the skill name equipped by the player.']}

def cp_json(raw):
 try:d=json.loads(raw.decode('utf-8-sig'))
 except ValueError as e:raise EvidenceError('Not valid UserSettings JSON') from e
 candidates=[];warnings=[];nodes=0
 def visit(x,path=(),depth=0):
  nonlocal nodes
  nodes+=1
  if nodes>50000 or depth>40:raise EvidenceError('JSON structure exceeds safe bound')
  if isinstance(x,dict):
   # Exact native key codes, not user names/free text. Keep metadata only when bounded.
   value=x.get('value')
   values=[value] if isinstance(value,str) else value if isinstance(value,list) and all(isinstance(y,str) for y in value) else []
   codes=[z for z in values if re.fullmatch(r'IK_[A-Za-z0-9_]{1,80}',z)]
   ident=x.get('name',x.get('id',''))
   if codes and re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.-]{0,95}',str(ident)):
    candidates.append({'option_id':str(ident),'codes':codes,'json_pointer':'/'+('/'.join(str(y).replace('~','~0').replace('/','~1') for y in path)),
      'state':'CONFIG_KEY_CODE_OBSERVED_NOT_EFFECTIVE_RESOLVED'})
   for k,y in x.items():visit(y,path+(k,),depth+1)
  elif isinstance(x,list):
   for i,y in enumerate(x):visit(y,path+(i,),depth+1)
 visit(d)
 if not candidates:warnings.append('No explicitly encoded IK_* values found; schema may differ. No default or effective key table is inferred.')
 return {'parser':'cyberpunk_explicit_ik_json/v1','key_code_records':candidates,'warnings':warnings,
  'requires':['Reconcile game build, input maps/contexts and mods; UserSettings alone may not describe complete effective behavior.','Use only declared action identifiers; this collector does not translate them to gameplay labels.']}

def cp_xml(raw):
 text=raw.decode('utf-8-sig')
 if re.search(r'<!\s*(DOCTYPE|ENTITY)',text,re.I):raise EvidenceError('XML external/internal entity declarations are not supported')
 try:root=ET.fromstring(text)
 except ET.ParseError as e:raise EvidenceError('Not valid input XML') from e
 entries=[];nodes=0
 def safe(value):return isinstance(value,str) and len(value)<=160 and bool(re.fullmatch(r'[A-Za-z0-9_./:+\- ]+',value))
 def visit(node,context=(),depth=0):
  nonlocal nodes
  nodes+=1
  if nodes>50000 or depth>40:raise EvidenceError('XML structure exceeds safe bound')
  tag=node.tag.split('}')[-1]
  name=node.attrib.get('name',node.attrib.get('id',''))
  nextcontext=context+((str(name),) if tag.lower() in {'mapping','context','action','button'} and safe(name) else ())
  codes={k:v for k,v in node.attrib.items() if re.fullmatch(r'IK_[A-Za-z0-9_]{1,80}',v)}
  if codes:entries.append({'tag':tag,'context_ids':list(context),'code_attributes':codes,'state':'XML_MAPPING_RECORD_NOT_EFFECTIVE_RESOLVED'})
  for child in node:visit(child,nextcontext,depth+1)
 visit(root)
 return {'parser':'cyberpunk_explicit_ik_xml/v1','key_code_records':entries,
  'warnings':[] if entries else ['No explicit IK_* code attributes found; do not invent a mapping.'],
  'requires':['XML mapping records are not a merged effective preset; dynamic context, bindings and mods need reconciliation.']}

def collect(specs,out,source_kind):
 if out.exists():raise FileExistsError('Refusing to overwrite an existing evidence directory')
 records=[];inputs=[]
 for kind,path in specs:
  raw,meta=safe_read(path);parsed={'poe2':poe,'cyberpunk-settings':cp_json,'cyberpunk-mapping':cp_xml}[kind](raw)
  records.append({'kind':kind,'source':meta,'evidence_scope':source_kind,'status':'CONFIG_CANDIDATE','parsed':parsed});inputs.append((Path(path),meta['sha256']))
 if not records:raise EvidenceError('Specify at least one input file; no automatic filesystem crawl')
 out.mkdir(parents=True,exist_ok=False)
 payload={'schema':'game-input-evidence/v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'scope':'Selected input fields only; private review artifact','records':records,'game_launched':False,'source_changed':False,
  'full_source_bytes_copied':False,'effective_binding_verified':False,'global_input_recording':False,'private_paths_included':False}
 (out/'INPUT_EVIDENCE.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 for path,expected in inputs:
  # Detect concurrent source changes by a second bounded read; never retry or overwrite it.
  _,now=safe_read(path)
  if now['sha256']!=expected:
   payload['source_changed']=True;payload['status']='STALE_DURING_COLLECTION';(out/'INPUT_EVIDENCE.json').write_text(json.dumps(payload,indent=2)+'\n');raise EvidenceError('Source changed; receipt marked stale. Inspect before recollection.')
 return payload
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--poe2-file',type=Path);a.add_argument('--cyberpunk-settings',type=Path);a.add_argument('--cyberpunk-mapping',type=Path,action='append',default=[]);a.add_argument('--source-kind',choices=['local-config-candidate','external-example'],default='local-config-candidate');a.add_argument('--out',type=Path,required=True);x=a.parse_args()
 specs=[]
 if x.poe2_file:specs.append(('poe2',x.poe2_file))
 if x.cyberpunk_settings:specs.append(('cyberpunk-settings',x.cyberpunk_settings))
 specs.extend(('cyberpunk-mapping',p) for p in x.cyberpunk_mapping)
 r=collect(specs,x.out,x.source_kind);print(json.dumps({'output':'INPUT_EVIDENCE.json','source_count':len(r['records']),'effective_verified':False,'source_changed':r['source_changed']}))
