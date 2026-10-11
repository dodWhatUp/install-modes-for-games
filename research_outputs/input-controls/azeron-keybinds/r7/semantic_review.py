#!/usr/bin/env python3
"""Traceable small semantic comparison + qualitative demands, not telemetry."""
import argparse,collections,importlib.util,itertools,json
from pathlib import Path
ROOT=Path(__file__).parent

def run(design_path,audit_script):
 data=json.loads((ROOT/'REVIEWED_ACTIONS_R7.json').read_text());d=json.loads(design_path.read_text())
 entries=data['entries'];anchors={
  'interaction':{'skyrim-original':'Activate','warframe':'Context action','tombraider2013':'Interact','shadowtr':'Interact','alienisolation':'Use','xcom2':'Interact','fairytail2':'Interact'},
  'sprint':{'skyrim-original':'Sprint','warframe':'Sprint','shadowtr':'Sprint','alienisolation':'Sprint','fairytail2':'Dash'},
  'jump':{'skyrim-original':'Jump','warframe':'Jump','tombraider2013':'Jump','shadowtr':'Jump/climb','fairytail2':'Jump'},
  'reload':{'tombraider2013':'Reload','shadowtr':'Reload','alienisolation':'Reload/activate','xcom2':'Reload'}
 }
 out=[]
 for role,gs in anchors.items():
  items=[]
  for game,action in gs.items():
   e=next(e for e in entries if e['game_id']==game and e['action']==action)
   # Compare main key, not required movement directions or optional mouse routes.
   keys=list(dict.fromkeys(v[0] for v in e['variants'] if not v[0].startswith('Mouse ')))
   items.append({'game_id':game,'role':role,'key_choices':keys,'entry_id':e['id'],'context':e['context'],'source_id':e['source_id']})
  pairs=list(itertools.combinations(items,2));same=sum(bool(set(a['key_choices'])&set(b['key_choices'])) for a,b in pairs)
  out.append({'role':role,'samples':items,'pairs':len(pairs),'pairs_sharing_a_key':same,'not_a_population_estimate':True})
 spec=importlib.util.spec_from_file_location('r6access',audit_script);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 cases=[]
 def demand(id,game,keys,reason,origin,src,direct=False,move=False,temporal='simultaneous'):
  result={f:mod.routes(keys,v['maps'],v['selectors'],d['position_map'],move) for f,v in d['variants'].items()}
  for f,r in result.items():
   r['direct_basic_requirement_satisfied']=not direct or r['status']=='DIRECT_MODEL_ROUTE'
  cases.append({'id':id,'game_id':game,'keys':keys,'direct_basic_required_by_design':direct,'extra_movement_stress':move,
    'relation':temporal,'requirement_origin':origin,'source_ids':src,'reason':reason,'results':result,'runtime_tested':False,'personal_frequency':None})
 demand('skyrim-sprint','skyrim-original',['Alt','W'],'Published Alt sprint needs directional movement; R6 puts BASIC Alt on thumb.','PUBLISHED_KEYS_PLUS_CONCURRENCY_INFERENCE',['S1'],True)
 demand('skyrim-jump','skyrim-original',['Space','W'],'Jump while moving is a design test, not a measured usage distribution.','PUBLISHED_KEYS_PLUS_CONCURRENCY_INFERENCE',['S1'],True)
 demand('warframe-sprint','warframe',['Shift','W'],'Source explicitly describes held Shift.','PUBLISHED_KEYS_PLUS_CONCURRENCY_INFERENCE',['S2'],True)
 demand('warframe-bullet-jump','warframe',['Ctrl','Space','W'],'Guide describes sprint/slide/jump relations; simultaneous set is a conservative access test, not a universal exact timing requirement.','DERIVED_COMPOUND_SEQUENCE_STRESS',['S2'],True,False,'sequence_with_possible_hold_overlap')
 demand('warframe-ability4','warframe',['4'],'Numbered ability requiring immediate access in chosen test.','PUBLISHED_KEY_PLUS_DESIGN_URGENCY',['S2'],True,True)
 demand('tomb-evade','tombraider2013',['Shift','W'],'Same Shift output means evade rather than sprint in this manual.','PUBLISHED_KEYS_PLUS_CONCURRENCY_INFERENCE',['S3'],True)
 demand('tomb-walk','tombraider2013',['Ctrl','W'],'Held walk direction.','PUBLISHED_KEYS_PLUS_CONCURRENCY_INFERENCE',['S3'],False)
 demand('shadow-heal','shadowtr',['F1'],'Held healing plant is an explicit F-key exception to the slow Tools bank.','PUBLISHED_KEY_PLUS_DESIGN_URGENCY',['S4'],True,True)
 demand('shadow-sprint','shadowtr',['Shift','W'],'Source explicitly lists hold Shift plus movement.','SOURCE_EXPLICIT_CHORD',['S4'],True)
 demand('alien-peek','alienisolation',['V','A'],'Source explicitly specifies hold V plus direction.','SOURCE_EXPLICIT_CHORD',['S5'],True)
 demand('alien-tracker','alienisolation',['Space'],'Source explicitly specifies hold Space for tracker.','PUBLISHED_KEY_PLUS_MOVEMENT_STRESS',['S5'],False,True)
 demand('alien-tracker-focus','alienisolation',['Ctrl','Space'],'Combines tracker and focus definitions; direct compound is a derived requirement.','DERIVED_CROSS_ROW_DEPENDENCY',['S5'],False,True)
 for digit in ['2','3','4']:
  demand('fairytail-bank-'+digit,'fairytail2',['Tab',digit],'Hold Tab changes the skill sheet; skill keys are 2/3/4.','DERIVED_CROSS_ROW_DEPENDENCY',['S7'],True)
 for digit in ['1','2']:
  demand('fairytail-space-'+digit,'fairytail2',['Space',digit],'Explicit item/flee chord.','SOURCE_EXPLICIT_CHORD',['S7'],True)
 demand('xcom-ability10','xcom2',['0'],'Tactical ability selection; camera need not move concurrently in this test.','PUBLISHED_KEY_DELIBERATE_TEST',['S6'])
 demand('xcom-waypoint','xcom2',['Ctrl','Mouse Right'],'Publisher-defined held waypoint selection.','SOURCE_EXPLICIT_CHORD',['S6'])
 demand('openttd-shift-f2','openttd',['Shift','F2'],'Road vehicle list; a deliberate menu operation, no movement requirement imposed.','SOURCE_EXPLICIT_CHORD',['S8'])
 demand('openttd-shift-f8','openttd',['Shift','F8'],'Road construction toolbar; same-column constraint remains a hypothesis.','SOURCE_EXPLICIT_CHORD',['S8'])
 demand('openttd-raise-and-pan','openttd',['W','Up Arrow'],'Optional stress: W is a command rather than a movement key; concurrent panning is not claimed required.','ANALYST_OPTIONAL_STRESS',['S8'])
 result={'revision':'R7','semantic_anchors':out,'demand_cases':cases,'limits':[
  'Convenience sample from scoped publisher/project manuals, not empirical population rates.',
  'Unrepresented games/actions are missing evidence, not proof of no binding.',
  'One modeled concurrent resource per finger; no latency, physical or ergonomic measurement.',
  'Direct-access and simultaneous sets are design requirements unless source says explicitly otherwise.',
  'Additional layers cannot resolve every physical, urgency or game-semantic mismatch.']}
 (ROOT/'SEMANTIC_AND_DEMAND_REVIEW_R7.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('Semantic anchors:',[(x['role'],x['pairs_sharing_a_key'],x['pairs']) for x in out]);print('Demand cases:',len(cases))
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--design',type=Path,required=True);p.add_argument('--access-script',type=Path,required=True);a=p.parse_args();run(a.design,a.access_script)
