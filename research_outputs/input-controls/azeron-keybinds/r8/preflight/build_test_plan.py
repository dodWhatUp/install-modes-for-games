#!/usr/bin/env python3
"""Build source-derived, NOT-RUN checklists. This never emits input."""
import argparse,json,hashlib
from pathlib import Path

def build(design,out):
 raw=design.read_bytes();d=json.loads(raw);plans={}
 for family,v in d['variants'].items():
  tests=[]
  for bank,button in v['selectors'].items():
   tests.append({'id':'selector-'+bank,'kind':'DEVICE_REQUIRED','buttons':[button],
    'instruction':f'With BASIC selected and games closed, hold native button {button}, observe {bank}, then release it.',
    'expected':'Correct bank remains active while held; release returns to BASIC with no second press or stuck output.',
    'known_limit':'The candidate has a reciprocal link; file presence is not an observed event.','status':'NOT_RUN'})
  for key,button in [('Ctrl',5),('Shift',9),('Space',14)]:
   tests.append({'id':'anchor-'+key,'kind':'DEVICE_REQUIRED','buttons':[button],
    'instruction':f'Using a supported native input inspector, check {key} on button {button} in each selected bank without running a game.',
    'expected':'The expected keyboard output is generated and fully released.','status':'NOT_RUN'})
  tests += [
   {'id':'held-output-transition','kind':'DEVICE_REQUIRED','buttons':[5,9,14],
    'instruction':'Test one anchor at a time: anchor down, layer selector down/up, then anchor up. Inspect every release; do not test all anchors together.',
    'expected':'No stuck or phantom key. Stop and record the exact order on failure.','status':'NOT_RUN'},
   {'id':'alt-and-movement','kind':'USER_HAND_REQUIRED','buttons':[3,24],
    'instruction':'Check the BASIC Alt output on button 3 while moving the stick, then release both.',
    'expected':'Reach and release are comfortable and deliberate. File/model availability is not sufficient.','status':'NOT_RUN'},
   {'id':'t-and-movement','kind':'USER_HAND_REQUIRED','buttons':[31,24],
    'instruction':'Check whether the BASIC T placement on thumb31 meets the actual game task; do not assume independent stick use.',
    'expected':'Record the tradeoff explicitly; a discomfort or concurrent-use failure is useful evidence, not a reason to force the position.','status':'NOT_RUN'},
   {'id':'zero-access','kind':'USER_HAND_REQUIRED','buttons':[13 if family=='CORE5' else 28],
    'instruction':'Check 0 in NUMBERS with the selector held; record whether movement must be released.',
    'expected':'The bank returns to BASIC cleanly and the access requirement fits the intended game.','status':'NOT_RUN'},
   {'id':'ctrl-number-route','kind':'USER_HAND_REQUIRED','buttons':[2,5,18] if family=='CORE5' else [2,5,23],
    'instruction':'Check a required Ctrl+number route using one Ctrl copy at a time. Release the number and Ctrl before the selector until transition behavior is verified.',
    'expected':'No duplicate modifier or missing key-up. Do not count merely separate button reach as a successful chord.','status':'NOT_RUN'},
   {'id':'reserved-button','kind':'FILE_AND_DEVICE_REQUIRED','buttons':[19],
    'instruction':'Confirm button19 remains reserved and that no unsupported external trigger has been introduced.',
    'expected':'No game or keyboard shortcut assigned by this package. External Overlay integration is still separate.','status':'NOT_RUN'}]
  plans[family]={'native_profile_count':len(v['maps']),'selector_buttons':v['selectors'],'tests':tests}
 data={'schema':'azeron-manual-test-plan/v1','design_sha256':hashlib.sha256(raw).hexdigest(),'baseline':'R8_UNCHANGED',
  'scope':'After an explicitly chosen family and authorized additive native import. Nothing in this plan runs automatically.',
  'safety':'Games closed and a supported native inspector first. Stop on unexpected/stuck input, discomfort or unknown effects; never force a repeated key test.',
  'families':plans,'all_physical_results':'NOT_RUN'}
 out.mkdir(parents=True,exist_ok=True);(out/'PHYSICAL_TEST_PLAN.json').write_text(json.dumps(data,indent=2)+'\n')
 template={'schema':'azeron-execution-receipt/v1','consumer_context':None,'source_commit_read':None,'family_chosen':None,
  'candidate_zip_sha256':None,'before_export_sha256':None,'after_export_sha256':None,'read_only_game_evidence':[],
  'native_review_before':None,'native_review_after':None,'stages':{
   'source_consumed':'NOT_RUN','family_selected':'NOT_RUN','native_backup_created':'NOT_RUN','native_import':'NOT_RUN',
   'layer_entry_and_return':'NOT_RUN','ordinary_outputs':'NOT_RUN','held_transition_and_keyup':'NOT_RUN',
   'physical_comfort':'NOT_RUN','effective_game_mapping':'NOT_RUN','gameplay':'NOT_RUN','live_overlay_integration':'NOT_RUN'},
  'observations':[],'unrelated_work_preserved':None,'stopped_reason':None,'next_action':None,
  'rule':'Pass only the observed scope, with an evidence reference. File generation/model tests do not prove native/device/game execution.'}
 (out/'EXECUTION_RECEIPT.template.json').write_text(json.dumps(template,indent=2)+'\n');return data
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--design',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=build(a.design,a.out);print({f:len(v['tests']) for f,v in r['families'].items()})
