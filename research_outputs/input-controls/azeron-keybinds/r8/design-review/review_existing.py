#!/usr/bin/env python3
"""Bounded descriptive review of existing R8 files. Never edits or imports them.
Evidence types stay separate: exact file comparison vs inherited model cases.
No new physical/game tests, profile compiler or global quality score.
"""
import argparse, collections, hashlib, json
from pathlib import Path

ROUTES = {'DIRECT_MODEL_ROUTE', 'LAYER_MODEL_ROUTE', 'OTHER_HAND_ONLY'}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def review(design_path, audit_path):
    d = json.loads(design_path.read_text(encoding='utf-8'))
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    assert d['revision'] == 'R8'
    assert set(d['variants']) == {'CORE5', 'SPARSE6'}
    pos = d['position_map']
    left, right = [d['variants'][f]['maps'] for f in ['CORE5', 'SPARSE6']]
    shared = sorted(set(left) & set(right))
    differences = []
    rows = []
    for fam, v in d['variants'].items():
        for bank, mapping in v['maps'].items():
            assert len(mapping) == 30 and mapping['R3'] == 'UNASSIGNED'
            keys = [x for x in mapping.values() if x != 'UNASSIGNED' and not x.startswith('LAYER:')]
            rows.append({'family':fam,'bank':bank,'keyboard_cells':len(keys),
                         'unique_keyboard_outputs':len(set(keys)),
                         'selector_cells':sum(x.startswith('LAYER:') for x in mapping.values()),
                         'unassigned_cells':sum(x == 'UNASSIGNED' for x in mapping.values())})
    for bank in shared:
        for p in left[bank]:
            if left[bank][p] != right[bank][p]:
                differences.append({'bank':bank, 'button_id':pos[p], 'position':p,
                                    'CORE5':left[bank][p], 'SPARSE6':right[bank][p]})
    base_diffs = [r for r in differences if r['bank']=='BASIC']
    assert len(base_diffs)==1 and base_diffs[0]['button_id']==30
    assert len(differences)==23
    assert len(shared)==5
    same_basic_keys = {k for p,k in left['BASIC'].items()
                       if k==right['BASIC'][p] and k!='UNASSIGNED' and not k.startswith('LAYER:')}
    assert len(same_basic_keys)==24
    cases = audit['selected_demands']
    signatures = collections.defaultdict(list)
    changed = []
    short_flag_traps = []
    counts = {f:collections.Counter() for f in ['CORE5','SPARSE6']}
    for case in cases:
        # Exact raw keys only; this dedup does not silently merge left/right modifiers.
        sig=(tuple(sorted(case['keys'])), case['movement'], case['direct'])
        signatures[sig].append(case['id'])
        for f in counts:
            r=case['results'][f]
            access = r['status'] in ROUTES
            immediate = not case['direct'] or r['status']=='DIRECT_MODEL_ROUTE'
            counts[f][('model_route_and_directness_fit' if access and immediate else 'unmet_or_unknown_in_model')]+=1
            if r.get('meets_direct_requirement') and not access:
                short_flag_traps.append({'id':case['id'],'family':f,'status':r['status'],
                                        'explanation':'Only the directness clause is true; this does not say access succeeded.'})
        a,b=[case['results'][f] for f in counts]
        if (a['status'],a['meets_direct_requirement']) != (b['status'],b['meets_direct_requirement']):
            changed.append({'id':case['id'],'keys':case['keys'],'movement_stress':case['movement'],
                            'direct_required':case['direct'],'CORE5':a['status'],'SPARSE6':b['status']})
    assert len(cases)==32 and len(signatures)==28 and len(changed)==3
    numeric_symmetry = {}
    for family,v in d['variants'].items():
        pairs=[]
        for n in range(1,10):
            np={p for p,k in v['maps']['NUMBERS'].items() if k==str(n)}
            fp={p for p,k in v['maps']['TOOLS'].items() if k=='F'+str(n)}
            pairs.append({'digit':n,'same_positions':np==fp,'number_positions':sorted(np),'function_positions':sorted(fp)})
        numeric_symmetry[family]=pairs
    assert sum(x['same_positions'] for x in numeric_symmetry['CORE5'])==9
    assert sum(x['same_positions'] for x in numeric_symmetry['SPARSE6'])==6
    return {
        'status':'BOUNDED_REVIEW_OF_UNCHANGED_R8_NOT_NEW_PROFILE_FAMILY',
        'input_sha256':{design_path.name:digest(design_path),audit_path.name:digest(audit_path)},
        'native_mutations':0,'physical_tests':0,'game_tests':0,
        'common_banks':shared,'keyboard_allocation_by_bank':rows,
        'shared_bank_cells_compared':150,'shared_bank_differences':differences,
        'basic_identical_native_cells':29,'basic_identical_visible_cells_excluding_19':28,
        'basic_identical_keyboard_outputs_at_same_positions':24,
        'basic_difference':base_diffs[0],
        'numbers_function_alignment':numeric_symmetry,
        'inherited_targeted_cases':32,'unique_exact_input_movement_directness_signatures':28,
        'duplicate_physical_signatures_different_contexts':[ids for ids in signatures.values() if len(ids)>1],
        'cases_distinguishing_families':changed,
        'directness_field_caveat':short_flag_traps,
        'selected_case_counts_for_diagnostics_only':{f:dict(c) for f,c in counts.items()},
        'limits':[
            '24 shared BASIC outputs and 23 cross-bank differences describe files, not hand comfort.',
            'The 32 old cases are targeted and not representative of usage; do not turn counts into a winner score.',
            'Deduplication preserves semantic source contexts; only mechanically identical signatures are grouped here.',
            'Inheritance of R8 model results is not a new experimental or effective-game verification.',
            'Same-finger conflicts remain hypotheses; different-finger routes are not proof of comfortable reach.',
            'Native identities, schemas, game source tables and all input files remain untouched.'
        ]
    }

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--design',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    before=[digest(a.design),digest(a.audit)]
    r=review(a.design,a.audit)
    if a.output.exists(): raise FileExistsError('Choose a new review output; do not overwrite evidence.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assert before==[digest(a.design),digest(a.audit)]
    print(json.dumps({'native_cells_unchanged':True,'shared_bank_differences':len(r['shared_bank_differences']),
        'old_cases':32,'discriminating_cases':len(r['cases_distinguishing_families']),
        'same_position_basic_keyboard_outputs':24},indent=2))
