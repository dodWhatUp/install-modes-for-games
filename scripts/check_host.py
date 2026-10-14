#!/usr/bin/env python3
"""Read-only exact dependency check. This does not install, repin or adopt a host."""
import argparse,hashlib,json
from pathlib import Path
PINS={'scripts/GameToolAutomation.py': '7c8a3e00761d42721a95b88aedc0eae6f7f3025417e7b448aeafe177d5c4601e', 'scripts/GameToolAI.py': '4e47d377b6168a4d06c2a421d092ca3e93d5e83259409cda93bb9289b16cd07a', 'scripts/GameToolJournal.py': '01e76b93c69adefa742dfcb139756903c2259812c437ec72c508739b2a81657a', 'scripts/game_mod_ops/safety.py': 'a40f7a172716a02d19c4aef688ee67d45b4e86dcede00702eed766528175598b', 'scripts/GameToolGameWorkspaces.py': 'b2ac5a668ad371df9ea442f47b16a55417e8777fa43f9bab837c2e672cb2ad60'}
def check(root):
    rows=[]
    for relative,expected in PINS.items():
        p=root/relative
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        rows.append({'path':relative,'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected})
    return {'status':'EXACT_DEPENDENCIES_MATCH' if all(r['matches'] for r in rows) else 'REVIEW_HOST_DIFFERENCES',
            'host_reference_version':'0.26.0-preview.1','files':rows,'installed':False,'repinned':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',type=Path,required=True);a=p.parse_args()
    r=check(a.host);print(json.dumps(r,indent=2));raise SystemExit(r['status']!='EXACT_DEPENDENCIES_MATCH')
