#!/usr/bin/env python3
"""Read-only exact dependency check. This does not install, repin or adopt a host."""
import argparse,hashlib,json
from pathlib import Path
PINS={'scripts/GameToolAutomation.py': '34bffd633608713905f87f3ecdac50653169fbb815415e6a737a6766bad3fccf', 'scripts/GameToolAI.py': '2bb619d85ee3b90ef13168ad4b6ebde4a88e82c6353bdc4cdf0a09d82e75f0ff', 'scripts/GameToolJournal.py': '01e76b93c69adefa742dfcb139756903c2259812c437ec72c508739b2a81657a', 'scripts/game_mod_ops/safety.py': 'a40f7a172716a02d19c4aef688ee67d45b4e86dcede00702eed766528175598b', 'scripts/GameToolGameWorkspaces.py': '414bae3f71bc34f51b7043ac51cd49eb32b07213a2aeaf60403ae123aa5b442e'}
def check(root):
    rows=[]
    for relative,expected in PINS.items():
        p=root/relative
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        rows.append({'path':relative,'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected})
    return {'status':'EXACT_DEPENDENCIES_MATCH' if all(r['matches'] for r in rows) else 'REVIEW_HOST_DIFFERENCES',
            'host_reference_version':'0.25.0-preview.1','files':rows,'installed':False,'repinned':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',type=Path,required=True);a=p.parse_args()
    r=check(a.host);print(json.dumps(r,indent=2));raise SystemExit(r['status']!='EXACT_DEPENDENCIES_MATCH')
