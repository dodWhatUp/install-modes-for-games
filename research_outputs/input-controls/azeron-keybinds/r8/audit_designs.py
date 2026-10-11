#!/usr/bin/env python3
"""Compare four candidates using the inherited model, scoped demands, regressions.
No quality percentage, telemetry, real hand test or effective-game claim.
"""
import argparse,collections,importlib.util,json
from pathlib import Path
P=Path(__file__).parent

def analyse(old,new,corpus,scenarios,model_path):
 d6=json.loads(old.read_text());d8=json.loads(new.read_text());raw=json.loads(corpus.read_text())['records'];prior=json.loads(scenarios.read_text())['demand_cases']
 spec=importlib.util.spec_from_file_location('access',model_path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 variants={'R6_COMPACT':d6['variants']['COMPACT'],'R6_SPARSE':d6['variants']['SPARSE'],**d8['variants']}
 stats={n:{m:collections.Counter() for m in ['isolated','movement_stress']} for n in variants};changed=[];count=0
 for r in raw:
  for i,v in enumerate(r['variants']):
   count+=1;res={}
   for n,map in variants.items():
    res[n]={}
    for mode,moving in [('isolated',False),('movement_stress',True)]:
     rt=mod.routes(v['keys'],map['maps'],map['selectors'],d8['position_map'],moving)
     if moving and rt['status'] in ['DIRECT_MODEL_ROUTE','LAYER_MODEL_ROUTE'] and v['isolated']['status']=='STICK_COMMAND_ROUTE':rt['status']='STICK_COMMAND_ROLE_REVIEW'
     res[n][mode]=rt['status'];stats[n][mode][rt['status']]+=1
   for a,b in [('R6_COMPACT','CORE5'),('R6_SPARSE','SPARSE6')]:
    for mode in ['isolated','movement_stress']:
     if res[a][mode]!=res[b][mode]:changed.append({'game':r['row']['game'],'row_id':r['row']['id'],'action':r['row']['action'],'keys':v['keys'],'mode':mode,'before_family':a,'after_family':b,'before':res[a][mode],'after':res[b][mode],'source_status':'INHERITED_SCOPE_NOT_REVERIFIED'})
 tests=[]
 demands=[{'id':x['id'],'keys':x['keys'],'movement':x['extra_movement_stress'],'direct':x['direct_basic_required_by_design'],'basis':x['requirement_origin'],'game_id':x['game_id'],'reason':x['reason']} for x in prior]
 additions=[
  ('bayo-lock-move',['Alt','W'],False,True,'bayonetta-pc','Published held lock plus movement; independent-finger feasibility is an analyst model.'),
  ('bayo-lock-jump',['Alt','Space','W'],False,True,'bayonetta-pc','Compound held lock/move/jump stress, not an explicit source chord.'),
  ('bayo-evade',['Shift','A'],False,True,'bayonetta-pc','Publisher explicitly describes directional evade.'),
  ('bayo-walk',['Ctrl','W'],False,True,'bayonetta-pc','Publisher explicitly describes held Ctrl walk.'),
  ('T-during-movement',['T'],True,True,None,'Regression guard: a game may need T while moving. No generic frequency assumed.'),
  ('zero-during-movement',['0'],True,False,None,'Regression guard: output capacity is not concurrent access.'),
  ('E-plus-arrow',['E','Up Arrow'],False,False,None,'Known cross-bank pattern; inherited Elden Ring scope remains unverified.'),
  ('C-plus-2',['C','2'],False,True,None,'Ordinary-letter modifier known from prior source audit; not repaired just by extra layers.'),
  ('Ctrl-Shift-8',['Ctrl','Shift','8'],True,False,None,'Deliberately demanding modifier stress, not a usage sample.'),
  ('F1-direct',['F1'],True,True,'shadowtr','Urgent healing scenario remains layered.'),
 ]
 demands += [dict(id=i,keys=k,movement=m,direct=dr,game_id=g,basis='TARGETED_REGRESSION_OR_SOURCE_DEMAND',reason=r) for i,k,m,dr,g,r in additions]
 for x in demands:
  row={**x,'results':{}}
  for n,map in variants.items():
   result=mod.routes(x['keys'],map['maps'],map['selectors'],d8['position_map'],x['movement']);result['meets_direct_requirement']=not x['direct'] or result['status']=='DIRECT_MODEL_ROUTE';row['results'][n]=result
  tests.append(row)
 counts={n:{k:dict(c) for k,c in st.items()} for n,st in stats.items()}
 assert count==3106
 for st in stats.values():
  for ct in st.values():assert sum(ct.values())==count
 # Logical anchors, not proof of continuous key ownership across layer transitions.
 anchors={n:{key:all(bank[pos]==key for bank in v['maps'].values()) for key,pos in [('Ctrl','R4C2'),('Shift','R4C3'),('Space','R4C4')]} for n,v in variants.items()}
 result={'revision':'R8','inherited_rows':len(raw),'inherited_game_records':len({x['row']['game'] for x in raw}),'listed_variants':count,'unparsed_rows_excluded':sum(x['syntax']['status']!='PARSED' for x in raw),'counts':counts,'anchors':anchors,'selected_demands':tests,'demand_count':len(tests),'changed_variant_count':len(changed),'limitations':['One concurrent resource per assumed finger. Same-finger failure is a screening flag, not proof of physical impossibility.','Targeted cases intentionally probe changed mappings; they are not a representative usage or latency distribution.','No numeric choice weights or population preference inferred.','Same-layer output availability is separate from held-key continuity and game recognition.','Source facts and unchanged R4 qualifiers retained.']}
 (P/'AUDIT_R8.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');(P/'REGRESSIONS_AND_GAINS_R8.json').write_text(json.dumps({'not_a_performance_score':True,'cases':changed},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'counts':counts,'anchors':anchors,'demands':len(tests)},indent=2));return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--r6',type=Path,required=True);a.add_argument('--r8',type=Path,required=True);a.add_argument('--corpus',type=Path,required=True);a.add_argument('--scenarios',type=Path,required=True);a.add_argument('--model',type=Path,required=True);x=a.parse_args();analyse(x.r6,x.r8,x.corpus,x.scenarios,x.model)
