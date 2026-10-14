#!/usr/bin/env python3
"""Read-only exact dependency check. This does not install, repin or adopt a host."""
import argparse,hashlib,json
from pathlib import Path
PINS={'scripts/GameToolAutomation.py': '34bffd633608713905f87f3ecdac50653169fbb815415e6a737a6766bad3fccf', 'scripts/GameToolAI.py': 'db1abcee0a77d6328bdc3171d65a97ee9f4c5de45ba8865d366283013a1aadae', 'scripts/GameToolAIContracts.py': 'e50876ac607cb49cf99b8faa3395767830d0ecf26bdb8a811051435557f75eed', 'scripts/GameToolAIFoundation.py': '0c745bd338a821b2e4dc2e1233cd60d2af175af6921258f59596981cb095b919', 'scripts/GameToolAITools.py': 'e4914d2c3ddf14b7941f564c6c6ce1340ef22f1ffca3aaf04f2791f0bb4c0a01', 'scripts/GameToolAIModern.py': '5a1046f3d950cac248d9deeca6db1d94e65fc8145e10f6a5dbe83730978ba5d9', 'scripts/GameToolJournal.py': '01e76b93c69adefa742dfcb139756903c2259812c437ec72c508739b2a81657a', 'scripts/GameToolGameWorkspaces.py': '73278d36bd9ee87a60f8cc694c5dda65a30a53537830e234f617b3b3b2ca619a', 'scripts/GameToolInstances.py': '9f5351132da8dd4269df1b49f570c7b6086877289f2e24836b251c6d349395de', 'scripts/GameToolPlanning.py': '1e1e11b0b565691c1d7b786c9c76f02a5e191464d62533bd7e32c6e61b753d2e', 'scripts/game_mod_ops/managers.py': '8f0f3c41861211ac2fd7665028b123ae532e0fd427826f5017c064656acd53a7', 'scripts/game_mod_ops/safety.py': 'a40f7a172716a02d19c4aef688ee67d45b4e86dcede00702eed766528175598b'}
def check(root):
    rows=[]
    for relative,expected in PINS.items():
        p=root/relative
        actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        rows.append({'path':relative,'expected_sha256':expected,'actual_sha256':actual,'matches':actual==expected})
    return {'status':'EXACT_DEPENDENCIES_MATCH' if all(r['matches'] for r in rows) else 'REVIEW_HOST_DIFFERENCES',
            'host_reference_version':'0.27.0-preview.1','files':rows,'installed':False,'repinned':False}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--host',type=Path,required=True);a=p.parse_args()
    r=check(a.host);print(json.dumps(r,indent=2));raise SystemExit(r['status']!='EXACT_DEPENDENCIES_MATCH')
