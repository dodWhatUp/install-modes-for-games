#!/usr/bin/env python3
"""Build two universal-first alternatives from exact R6 design; no runtime edits."""
import argparse,copy,hashlib,json
from pathlib import Path

def build(src:Path,dst:Path):
 raw=src.read_bytes();old=json.loads(raw);d={k:copy.deepcopy(v) for k,v in old.items() if k not in ['variants','design_caveats']}
 d.update(revision='R8',status='NATIVE_CANDIDATES_NOT_IMPORTED',baseline_revision='R6',baseline_sha256=hashlib.sha256(raw).hexdigest())
 core=copy.deepcopy(old['variants']['COMPACT']);sparse=copy.deepcopy(old['variants']['SPARSE'])
 core.update(name='CORE5',profile_prefix='SHARED R8 CORE5');sparse.update(name='SPARSE6',profile_prefix='SHARED R8 SPARSE6')
 for v in [core,sparse]:
  v['maps']['BASIC']['R2C1']='Alt';v['maps']['BASIC']['TH_R']='T'
  for l in ['NUMBERS','MENUS','TOOLS']:v['maps'][l]['R4C4']='Space'
  v['maps']['MENUS']['R5C3']='Alt'
  v['maps']['TOOLS']['TH_R']='Alt'
 core['maps']['BASIC']['TH_U']='LAYER:NAV'
 core['selectors']['NAV']=28
 core['maps']['NUMBERS']['R5C3']='0'
 core['maps']['NUMBERS']['ST_D']='Alt' # Comma is still in NAV; keep the complete number grid.
 core['maps']['MENUS']['TH_U']='H'
 core['maps']['NAV']=copy.deepcopy(old['variants']['SPARSE']['maps']['NAV'])
 core['maps']['NAV']['R1C4']='E'
 core['maps']['NAV']['R4C1']='Semicolon' # Period remains in MENUS.
 sparse['maps']['NUMBERS']['TH_R']='Alt' # Equals preserved in new SYMBOLS.
 sparse['maps']['BASIC']['TH_D']='LAYER:SYMBOLS'
 sparse['selectors']['SYMBOLS']=30
 sparse['maps']['NAV']['R1C4']='E'
 sparse['maps']['NAV']['R4C1']='Alt' # Period preserved in SYMBOLS.
 sy={p:'UNASSIGNED' for p in old['position_map']}
 rows=[['Left Bracket','Right Bracket','Minus','Equals'],['Semicolon','Apostrophe','Backslash','Slash'],['Backtick','Comma','Period','Caps Lock'],['Tab','Ctrl','Shift','Space'],['Esc','UNASSIGNED','UNASSIGNED','Enter']]
 for r,row in enumerate(rows,1):
  for c,key in enumerate(row,1):sy[f'R{r}C{c}']=key
 sy.update(L3='Backspace',TH_D='LAYER:SYMBOLS',ST_RU='Enter',ST_RD='Esc')
 sparse['maps']['SYMBOLS']=sy
 d['variants']={'CORE5':core,'SPARSE6':sparse}
 for name,v in d['variants'].items():
  orig=old['variants']['COMPACT' if name=='CORE5' else 'SPARSE'];v['layer_count']=len(v['maps']);v.pop('changes_from_R5',None)
  v['changes_from_R6']=[dict(layer=l,position=p,button_id=old['position_map'][p],before=orig['maps'].get(l,{}).get(p,'NOT_PRESENT'),after=val) for l,bank in v['maps'].items() for p,val in bank.items() if orig['maps'].get(l,{}).get(p,'NOT_PRESENT')!=val]
  keys=set('WASD')|{k for bank in v['maps'].values() for k in bank.values() if k!='UNASSIGNED' and not k.startswith('LAYER:')}
  assert keys==set(d['target_outputs']),(name,keys^set(d['target_outputs']))
  assert all(bank['R3']=='UNASSIGNED' for bank in v['maps'].values())
  assert all(bank['R4C4']=='Space' and bank['R4C2']=='Ctrl' and bank['R4C3']=='Shift' for bank in v['maps'].values())
  if name=='SPARSE6':
   for bank,ids in d['source_sensitive_mask'].items():
    for n in ids:assert v['maps'][bank][next(p for p,i in d['position_map'].items() if i==n)]=='UNASSIGNED'
  v['unique_logical_outputs']=len(keys);v['status']='NATIVE_CANDIDATE_NOT_IMPORTED'
 d['r8_tradeoffs']=[
  'BASIC Alt is now little-finger button3; T moves to thumb31. Alt+movement gains a distinct modeled route; T+movement loses one. Direction/reach comfort remains unmeasured.',
  'Ctrl5, Shift9 and Space14 remain at the same locations across all banks. This preserves logical availability, not proof of held-output continuity across a layer transition.',
  'CORE5 adds deliberate thumb-held NAV28. H moves from BASIC28 to MENUS28. The NUMBERS zero remains at finger13; the full numeric grid is preserved.',
  'CORE5 NUMBERS keeps the 1–9 and zero grid plus alternate Ctrl18 and Shift38. Alt uses thumb23 instead of Comma, which remains in NAV; Alt with 5–0 while moving is not independently available there.',
  'SPARSE6 preserves all nine extra user-source finger blanks; adds SYMBOLS on thumb30 instead of BASIC Caps Lock. Caps Lock remains on SYMBOLS.',
  'NAV and SYMBOLS occupy the thumb while held. No independent thumbstick movement is claimed there.',
  'NAV E17 with arrows provides a same-bank pouch/confirm chord route; this is deliberate access, not proof of a current Elden Ring preset.',
  'TOOLS Alt on thumb31 trades simultaneous movement for retaining the F-key grid and Space14.',
  'Number presence is not urgent access. F1 healing, 5–0 hotbar actions and C+2/C+4 remain candidates for scoped game-side rebinding or later physical validation.',
  'No extra function bank or new default game remap is silently introduced. Existing R6 remains a rollback/comparison candidate, not a current live-state backup.'
 ]
 dst.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');return d
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--r6',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();d=build(a.r6,a.out);print({k:(v['layer_count'],len(v['changes_from_R6'])) for k,v in d['variants'].items()})
