#!/usr/bin/env python3
"""Generate documented and stress-test cases. No runtime input capture."""
from pathlib import Path
import json, sys
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
r3maps=json.loads((out/"layout_candidate.json").read_text(encoding="utf-8"))["maps"]
def write_json(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
cases=[]
def case(cid,bank,keys,move,origin,source=None,notes="",kind="chord"):
    cases.append(dict(id=cid,bank=bank,keys=keys,movement_required=move,
                      requirement_origin=origin,source_id=source,notes=notes,kind=kind))
for digit in list("1234567890"):
    case('num-'+digit,'NUMBERS',[digit],True,'ANALYST_ACCESS_STRESS',notes='Deliberate full number bank; test does not assert this digit is combat-critical.',kind='single')
    case('ctrl-num-'+digit,'NUMBERS',['Ctrl',digit],True,'ANALYST_ACCESS_STRESS')
    case('shift-num-'+digit,'NUMBERS',['Shift',digit],True,'ANALYST_ACCESS_STRESS')
    case('ctrl-shift-num-'+digit,'NUMBERS',['Ctrl','Shift',digit],True,'ANALYST_ACCESS_STRESS')
    case('alt-num-'+digit,'NUMBERS',['Alt',digit],True,'ANALYST_ACCESS_STRESS')
for i in range(1,13):
    case('f-'+str(i),'TOOLS',[f'F{i}'],True,'ANALYST_ACCESS_STRESS',kind='single')
    case('shift-f-'+str(i),'TOOLS',['Shift',f'F{i}'],True,'ANALYST_ACCESS_STRESS')
for k in ['1','2','3','4','C','V']:
    case('wolong-shift-'+k,'BASIC',['Shift',k],True,'SOURCE_SHORTCUT_PLUS_MOVEMENT_STRESS','wolong',
         'The shortcut is documented; adding continuous stick movement is a conservative stress condition, not a source-measured requirement.')
for k in ['2','3','4']:
    case('fairytail-tab-'+k,'BASIC',['Tab',k],False,'DERIVED_FROM_SOURCE_DEFINITIONS','fairytail2')
for k in ['1','2']:
    case('fairytail-space-'+k,'BASIC',['Space',k],False,'SOURCE_EXPLICIT_CHORD','fairytail2')
case('taiko-red-large','BASIC',['X','C'],False,'SOURCE_EXPLICIT_PAIR','taiko')
case('taiko-blue-large','BASIC',['Z','V'],False,'SOURCE_EXPLICIT_PAIR','taiko')
for k in ['1','3']:
    case('base-ctrl-'+k,'BASIC',['Ctrl',k],True,'ANALYST_ACCESS_STRESS')
for bank in r3maps:
    for key in ['Space','Enter','Esc']:
        case(f'common-{bank}-{key}',bank,[key],False,'DESIGN_INVARIANT',kind='single')
for k in ['Up Arrow','Left Arrow','Right Arrow','Down Arrow']:
    case('arrows-moving-'+k,'LETTERS',[k],True,'ANALYST_ACCESS_STRESS',notes='The main thumb is already on movement; a thumb-only arrow should not receive an independent-access pass.')
case('gw2-heal6-direct','BASIC',['6'],True,'SOURCE_KEY_PLUS_URGENCY_REQUIREMENT','gw2',
     '6 is the documented healing key. Requiring it on Basic is a conservative reaction-design requirement, not measured frequency.',kind='single')
case('gw2-heal6-layered','NUMBERS',['6'],True,'SOURCE_KEY_PLUS_ACCESS_STRESS','gw2',
     'Reach can pass but this is still layered, not direct. It does not resolve the direct-heal requirement.',kind='single')
write_json(out/'cases.json',{"schema_version":"1.0","status":"STATIC_ACCESS_CASES_NOT_GAMEPLAY_TESTS","cases":cases})

print("Generated",len(cases),"static cases")
