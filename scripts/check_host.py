#!/usr/bin/env python3
"""Read-only exact dependency check. This does not install, repin or adopt a host."""
import argparse,hashlib,json
from pathlib import Path
PINS={'scripts/GameToolAutomation.py': '34bffd633608713905f87f3ecdac50653169fbb815415e6a737a6766bad3fccf', 'scripts/GameToolAI.py': '92b5189b8726882d194451233df9681409d6182c13199fdeb1004785860a2b69', 'scripts/GameToolAIContracts.py': '7e815a847fe59335aad3d29e63c8335df61546eef2940dad8f543f8e7940e39b', 'scripts/GameToolAIFoundation.py': '4c9a701d605fa6deced22168a276b4c7d5071ca4dd3617ce63ac8a211e7cddd5', 'scripts/GameToolAITools.py': 'e4914d2c3ddf14b7941f564c6c6ce1340ef22f1ffca3aaf04f2791f0bb4c0a01', 'scripts/GameToolAIModern.py': 'd0fd6e30b2995c765dc3d84c4e5e8ebda038142de87ff6d88a10b78124e0840b', 'scripts/GameToolJournal.py': '01e76b93c69adefa742dfcb139756903c2259812c437ec72c508739b2a81657a', 'scripts/GameToolGameWorkspaces.py': '73278d36bd9ee87a60f8cc694c5dda65a30a53537830e234f617b3b3b2ca619a', 'scripts/GameToolInstances.py': 'ff66f36243d2074525a2b610e805dc86cbccd108500c6858fea62eb2f4644143', 'scripts/GameToolPlanning.py': 'c65f8f8b38cae6a8a961d56e3816d5ea41de41f84b99bf4719bfbe32c18f873d', 'scripts/game_mod_ops/managers.py': '8f0f3c41861211ac2fd7665028b123ae532e0fd427826f5017c064656acd53a7', 'scripts/game_mod_ops/safety.py': 'a40f7a172716a02d19c4aef688ee67d45b4e86dcede00702eed766528175598b'}
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
