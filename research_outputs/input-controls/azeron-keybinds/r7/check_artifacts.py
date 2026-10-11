#!/usr/bin/env python3
"""Independent data, source-link, palette and script-syntax checks. No browser."""
import argparse,collections,copy,hashlib,itertools,json,re,subprocess,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from jsonschema import Draft202012Validator
P=Path(__file__).parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def luminance(color):
 v=[int(color[i:i+2],16)/255 for i in (1,3,5)];v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in v]
 return sum(a*b for a,b in zip(v,[.2126,.7152,.0722]))
def contrast(a,b):
 x,y=sorted([luminance(a),luminance(b)]);return (y+.05)/(x+.05)

def check(corpus,design):
 raw=load(corpus)['records'];src={r['row']['id']:r for r in raw};a=load(P/'REVIEWED_ACTIONS_R7.json');s=load(P/'SURVEY_R7.json')
 assert a['source_corpus_sha256']==sha(corpus)==s['input_sha256'];assert a['native_design_sha256']==sha(design)
 assert len(raw)==2195 and len(set(r['row']['game'] for r in raw))==94
 assert len(a['entries'])==179 and sum(e['source_row_id'] is not None for e in a['entries'])==177
 for e in a['entries']:
  if e['source_row_id']:
   r=src[e['source_row_id']]['row'];assert e['raw_expression']==r['key'] and e['action']==r['action'] and e['context']==r['context']
   assert e['inherited_gesture']==r['gesture']
  if not e['parsing_override'] and e['source_row_id']:assert e['variants']==src[e['source_row_id']]['syntax']['variants']
  assert not e['effective_binding_verified'] and not e['physical_tested']
 assert len([g for g in a['games'] if g['status']!='KEY_TABLE_PENDING'])==8
 groups=collections.defaultdict(set)
 for r in raw:
  for v in r['variants']:
   for k in v['keys']:
    if not k.startswith('Mouse '):groups[r['row']['game']].add(re.sub(r'^(Left|Right) (Ctrl|Shift|Alt)$',r'\2',k))
 pairs=load(P/'KEY_VOCABULARY_PAIRS_R7.json')['pairs'];assert len(pairs)==94*93//2
 assert len({tuple(sorted([p['a'],p['b']])) for p in pairs})==4371
 for p in pairs:
  left,right=groups[p['a']],groups[p['b']];assert p['shared_keys']==len(left&right);assert p['union_keys']==len(left|right)
  assert p['jaccard']==round(len(left&right)/len(left|right),6)
 assert sum(f['games'] for f in s['families'])==94 and sum(f['rows'] for f in s['families'])==2195
 sem=load(P/'SEMANTIC_AND_DEMAND_REVIEW_R7.json');assert len(sem['demand_cases'])==22
 expected={'interaction':(6,21),'sprint':(6,10),'jump':(10,10),'reload':(6,6)}
 for role in sem['semantic_anchors']:assert (role['pairs_sharing_a_key'],role['pairs'])==expected[role['role']]
 soup=BeautifulSoup((P/'Azeron_R7_Action_Atlas_HE.html').read_text(),'html.parser')
 data=json.loads(soup.find('script',id='atlas-data').string);assert data['design']==load(design)
 assert all(data['actions']['entries'][i]['id']==e['id'] for i,e in enumerate(a['entries']))
 assert len(data['actions']['entries'])==179 and soup.html['lang']=='he' and soup.html['dir']=='rtl'
 assert not soup.select('script[src], iframe, img[src], form, link[href]')
 for x in data['actions']['sources']:assert x['url'].startswith('https://')
 for path in data['icons'].values():assert re.fullmatch(r'[MmZzLlHhVvCcSsQqTtAaEe0-9+.,\s-]+',path),path
 scripts=[]
 with tempfile.TemporaryDirectory() as td:
  for i,tag in enumerate(soup.find_all('script')):
   if tag.get('type')=='application/json':continue
   text=tag.string or tag.get_text();p=Path(td)/f'script{i}.js';p.write_text(text)
   r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True);assert r.returncode==0,r.stderr;scripts.append(i)
   assert not re.search(r'\b(fetch|WebSocket|XMLHttpRequest|localStorage|sessionStorage|setInterval)\b',text)
   assert not re.search(r'(keydown|keyup|keypress|navigator\.hid|navigator\.serial)',text)
 ratios={k:contrast(v['color'],'#202c40') for k,v in data['actions']['categories'].items()};assert all(v>=3 for v in ratios.values())
 assert contrast('#f1f5f9','#202c40')>=4.5
 schema=load(P/'atlas-extension.schema.json');Draft202012Validator.check_schema(schema);val=Draft202012Validator(schema)
 valid={'extension':'keymap.atlas','schema_version':1,'base_mapping_reference':'record.json','base_mapping_fingerprint':'a'*64,'display_only':True,'annotations':[{'binding_reference':'binding:14','category_id':'movement','icon_id':'jump','action_label':'Jump','aliases':[],'source_refs':['S1'],'evidence':'PUBLISHED_SCOPED','execution_policy':'NONE'}]};val.validate(valid)
 bad=[]
 def failure(edit):
  x=copy.deepcopy(valid);edit(x);assert list(val.iter_errors(x));bad.append(1)
 failure(lambda x:x.update(display_only=False));failure(lambda x:x.update(output_keys=['F13']));failure(lambda x:x['annotations'][0].update(output='Q'))
 failure(lambda x:x['annotations'][0].update(source_refs=[]));failure(lambda x:x['annotations'][0].update(evidence='EFFECTIVE_CONFIG'))
 failure(lambda x:x['annotations'][0].update(execution_policy='SEND_INPUT'));failure(lambda x:x.update(base_mapping_fingerprint='unknown'))
 report=BeautifulSoup((P/'Azeron_R7_Research_HE.html').read_text(),'html.parser');assert len(report.find_all('h2'))>=10;assert len(report.find_all('table'))>=3
 assert '__DATA__' not in str(soup) and '__CONTENT__' not in str(report)
 result={'revision':'R7','status':'STATIC_AND_QUERY_CHECKS_NOT_BROWSER_OR_RUNTIME','source_records_in_atlas':179,'inherited_selected_rows_preserved':177,'additive_new_source_facts':2,'inherited_corpus_rows':2195,'per_game_records':94,'vocabulary_pairs_reconciled':4371,'semantic_anchor_roles':4,'demand_cases':22,'schema_negative_cases':len(bad),'inline_js_syntax_checks':len(scripts),'native_design_unchanged':True,'palette_contrast_full_opacity':{k:round(v,2) for k,v in ratios.items()},'full_accessibility_conformance_claim':False,'real_browser_tested':False,'keyboard_hook_or_input_injection':False,'native_import_performed':False,'hardware_tested':False,'gameplay_tested':False,'personal_usage_frequency_measured':False,'prior_denied_browser_route_retried':False,'ui_scope':'Manual local exploration only; actual peek/pin/native-layer integration is future.'}
 (P/'QA_DATA_R7.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,indent=2))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--design',type=Path,required=True);a=p.parse_args();check(a.corpus,a.design)
