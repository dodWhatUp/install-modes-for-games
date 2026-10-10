#!/usr/bin/env python3
"""Compare output availability and conservative independent-finger routes.
Reads already-parsed R4 variants; no new claim about sources or gameplay.
NAV reserves the THUMB, unlike the other held layers; this is explicit.
"""
import argparse,collections,itertools,json,re
from pathlib import Path

def finger(p):
 if p.startswith('R') and 'C' in p:return ['little','ring','middle','index'][int(p.split('C')[1])-1]
 return {'L3':'little','R3':'index'}.get(p,'thumb')
def logical(k):return re.sub(r'^(Left|Right) (Ctrl|Shift|Alt)$',r'\2',k)
def routes(keys,maps,selectors,pos,move=False):
 keyboard=list(dict.fromkeys(logical(k) for k in keys if not k.startswith('Mouse ')))
 if not keyboard:return {'status':'OTHER_HAND_ONLY'}
 allkeys={k for b in maps.values() for k in b.values()}|set('WASD')
 missing=[k for k in keyboard if k not in allkeys]
 if missing:return {'status':'OUTPUT_REVIEW','missing':missing}
 same=[];found=[];ip={v:k for k,v in pos.items()}
 for l,b in maps.items():
  options=[[p for p,k in b.items() if k==key]+(['STICK'] if key in set('WASD') else []) for key in keyboard]
  if not all(options):continue
  same.append(l)
  busy=[] if l=='BASIC' else [finger(ip[selectors[l]])]
  for comb in itertools.product(*options):
   groups=[finger(p) for p in comb if p!='STICK']
   directions={k for k,p in zip(keyboard,comb) if p=='STICK'}
   if {'W','S'}<=directions or {'A','D'}<=directions:continue
   if move or directions:groups+=['thumb']
   g=busy+groups
   if len(g)==len(set(g)):
    found.append({'bank':l,'positions':dict(zip(keyboard,comb))});break
 if not same:return {'status':'CROSS_BANK_ONLY'}
 if not found:return {'status':'FINGER_MODEL_CONFLICT','banks':same}
 return {'status':'DIRECT_MODEL_ROUTE' if found[0]['bank']=='BASIC' else 'LAYER_MODEL_ROUTE','route':found[0],'alternatives':found[1:]}

def main(design,r5,r4,out):
 d=json.loads(design.read_text());old=json.loads(r5.read_text());records=json.loads(r4.read_text())['records']
 sets={'R5':{'maps':old,'selectors':{'NUMBERS':2,'LETTERS':1,'TOOLS':36}},**d['variants']}
 counts={n:{mode:collections.Counter() for mode in ['isolated','movement_stress']} for n in sets}
 results=[];bygame=collections.defaultdict(lambda:collections.Counter())
 for rec in records:
  row=rec['row']
  for i,var in enumerate(rec['variants']):
   result={'row_id':row['id'],'game':row['game'],'action':row['action'],'raw_expression':row['key'],'listed_variant':i,'keys':var['keys'],'source_url':row['source_url'],'source_status':'INHERITED_NOT_FRESHLY_VERIFIED','evaluations':{}}
   for n,v in sets.items():
    result['evaluations'][n]={}
    for mode,moving in [('isolated',False),('movement_stress',True)]:
     rt=routes(var['keys'],v['maps'],v['selectors'],d['position_map'],moving)
     if rt['status'] in ['DIRECT_MODEL_ROUTE','LAYER_MODEL_ROUTE'] and rec['variants'][i]['isolated']['status']=='STICK_COMMAND_ROUTE' and moving:
      rt['status']='STICK_COMMAND_ROLE_REVIEW'
     result['evaluations'][n][mode]=rt;counts[n][mode][rt['status']]+=1
   results.append(result)
 scenarios=[]
 # These are retained source-backed demand cases and analyst stress cases, not observed play.
 for keys,note in [(['Ctrl','1'],'Generic modifier access'),(['Shift','2'],'Generic modifier access'),(['Ctrl','Shift','8'],'Generic multi-modifier stress'),(['C','2'],'Atelier Yumia inherited publisher-defined command'),(['E','Up Arrow'],'Elden Ring inherited row; current preset not verified'),(['Shift','F2'],'OpenTTD documented command'),(['Alt','Q'],'Generic movement plus modifier stress'),(['Space'],'Any game using Space; urgency/context not presumed')]:
  for moving in [False,True]:
   scenarios.append({'keys':keys,'movement_stress':moving,'basis':note,'result':{n:routes(keys,v['maps'],v['selectors'],d['position_map'],moving) for n,v in sets.items()}})
 summary={'revision':'R6','rows_inherited':len(records),'game_records_inherited':len({r['row']['game'] for r in records}),'parsed_variants':len(results),'unparsed_rows_not_scored':sum(r['syntax']['status']!='PARSED' for r in records),
  'counts':{n:{m:dict(c) for m,c in modes.items()} for n,modes in counts.items()},'selected_scenarios':scenarios,
  'limits':['Counts are input variants, not independent actions, observed frequency, game compatibility or speed.','R4 parser and source limitations are inherited; no new worldwide key survey is claimed.','One concurrent resource per finger is a conservative hypothesis, not measured hand ability.','Thumb-held NAV prohibits independent thumbstick movement.','Side-specific modifiers and physical switch direction still need native/runtime review.','The sparse masks are user-source geometry preferences, not empirical population ergonomics.','Layer entry/exit, key-up handling and external overlay trigger remain untested.']}
 (out/'ACCESS_SUMMARY_R6.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 (out/'ACCESS_CASES_R6.json').write_text(json.dumps({'summary':{k:v for k,v in summary.items() if k!='selected_scenarios'},'variants':results},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k not in ['selected_scenarios','limits']},indent=2));return summary
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--design',type=Path,required=True);p.add_argument('--r5',type=Path,required=True);p.add_argument('--r4-audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();main(a.design,a.r5,a.r4_audit,a.out)
