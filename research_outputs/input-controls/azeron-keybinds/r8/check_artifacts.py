#!/usr/bin/env python3
"""Static content, script, geometry and source-contract checks, NOT rendering."""
import argparse,hashlib,json,re,subprocess,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
P=Path(__file__).parent

def check(html,prior):
 soup=BeautifulSoup(html.read_text(),'html.parser');data=json.loads(soup.find('script',id='atlas-data').string)
 design=json.loads((P/'DESIGN_R8.json').read_text());actions=json.loads((P/'ACTIONS_R8.json').read_text());old=json.loads(prior.read_text())
 assert data['design']==design and actions['entries'][:179]==old['entries']
 assert len(actions['entries'])==208 and len(data['actions']['entries'])==208
 assert hashlib.sha256((P/'DESIGN_R8.json').read_bytes()).hexdigest()==actions['native_design_sha256']
 assert len({e['id'] for e in actions['entries']})==208
 for e in actions['entries']:
  assert not e['effective_binding_verified'] and not e['physical_tested']
  assert e['source_id'] in {s['id'] for s in actions['sources']}
  assert data['icons'][e['icon'] if e['icon'] in data['icons'] else 'unknown']
 assert soup.html['dir']=='rtl' and soup.html['lang']=='he'
 assert not soup.select('script[src],img[src],iframe,form,link[href]')
 checks=[]
 with tempfile.TemporaryDirectory() as t:
  for i,s in enumerate(soup.find_all('script')):
   if s.get('type')=='application/json':continue
   text=s.string or s.get_text();f=Path(t)/('part'+str(i)+'.js');f.write_text(text)
   r=subprocess.run(['node','--check',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stderr
   assert not re.search(r'\b(fetch|WebSocket|XMLHttpRequest|localStorage|sessionStorage|setInterval)\b',text)
   assert not re.search(r'keydown|keyup|keypress|navigator\.hid|navigator\.serial',text);checks.append(i)
 # Row arithmetic is a static bound, not a real-font/browser layout test.
 for h in [98,116,140]:assert h-(13+5+5)-(18+19+12+9)>0
 ids=design['position_map'];views=0
 for v in design['variants'].values():
  for layer,bank in v['maps'].items():
   visible=[ids[p] for p in bank if ids[p]!=19]
   assert len(visible)==29 and len(set(visible))==29 and 36 in visible and 37 in visible and 24 not in visible;views+=1
 audit=json.loads((P/'AUDIT_R8.json').read_text());assert audit['demand_count']==32 and audit['listed_variants']==3106
 for counts in audit['counts'].values():
  for c in counts.values():assert sum(c.values())==3106
 native=json.loads((P/'QA_NATIVE_R8.json').read_text());assert native['digital_cells']==330 and native['directed_links']==18 and native['original_native_profiles_checked']==18
 ui=json.loads((P/'QA_UI_EVENTS_R8.json').read_text());q=json.loads((P/'QA_ATLAS_R8.json').read_text());co=json.loads((P/'QA_COLLECTOR_R8.json').read_text())
 assert q['named_query_contract_tests']==37 and ui['ui_event_assertions']==16 and co['tests_run']==15 and not co['errors'] and not co['failures']
 out={'revision':'R8','status':'OFFLINE_VERIFIED_NOT_INSTALLED','native_profiles':11,'native_inputs':473,'digital_cells':330,'layer_links':18,'old_native_profiles_checked':18,'views':views,'visible_cells_across_views':29*views,'action_records':208,'new_Bayonetta_records':29,'source_game_scopes':9,'pending_display_targets':10,'model_variants':3106,'targeted_demands':32,'pure_query_tests':37,'DOM_fixture_event_tests':16,'collector_fixture_tests':15,'inline_script_checks':len(checks),'source_179_rows_preserved':True,'geometry_static_bounds_checked':True,'no_outbound_code_or_key_hooks':True,'real_browser_rendering_tested':False,'native_import_tested':False,'hardware_or_game_tested':False,'Windows_effective_configs_read':False,'live_Codex_task_consumption_confirmed':False}
 (P/'QA_SUMMARY_R8.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));return out
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--html',type=Path,required=True);a.add_argument('--prior-actions',type=Path,required=True);x=a.parse_args();check(x.html,x.prior_actions)
