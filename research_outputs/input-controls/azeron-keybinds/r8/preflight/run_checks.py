#!/usr/bin/env python3
"""One-command offline rehearsal. No program installation, app launch or native import.
Requires the exact R8 recovery ZIP. Creates a NEW task directory only.
Python 3.9+; Node is optional but its missing tests remain NOT_RUN.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from safe_io import ReviewError, read_regular, new_output, write_report, timestamp
from native_review import bounded_zip
R8_SHA='467a57df9360c5eb6c90861cad5933004e8e2c67e2e0bd96d2072ea24b3479de'
ROOT=Path(__file__).parent


def rehearse(archive: Path, out: Path):
 raw,_=read_regular(archive,8_000_000)
 if hashlib.sha256(raw).hexdigest()!=R8_SHA:raise ReviewError('R8 recovery hash mismatch; stop and reconcile.')
 members=bounded_zip(raw);manifest=json.loads(members['MANIFEST.json'])
 for item in manifest['entries']:
  b=members[item['path']]
  if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:raise ReviewError('R8 inner manifest mismatch.')
 folder=new_output(out);r8=folder/'r8';r8.mkdir();reports=folder/'reports';reports.mkdir()
 for name,b in members.items():
  p=r8/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 steps=[];env=dict(os.environ,R8_ROOT=str(r8),QA_OUTPUT=str(reports/'QA_PREFLIGHT.json'))
 def command(name,args,cwd):
  result=subprocess.run(args,cwd=cwd,env=env,capture_output=True,text=True,timeout=90)
  steps.append({'step':name,'exit_code':result.returncode,'passed':result.returncode==0})
  (reports/(name+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
  if result.returncode:raise ReviewError('Test failed at '+name+'; results retained, no automatic retry.')
 try:
  command('preflight_tests',[sys.executable,str(ROOT/'test_preflight.py')],folder)
  command('prior_input_extract',[sys.executable,str(r8/'source/prepare_inputs.py'),'--r7-archive',str(r8/'prior/Azeron_R7_Complete_Recovery.zip'),'--out',str(folder/'inputs')],folder)
  inputs=folder/'inputs/r6'
  command('native_readback',[sys.executable,str(r8/'source/validate_profiles.py'),'--source',str(inputs/'inputs/r5/profiles/01_SHARED_R5_BASIC.json'),
   '--design',str(r8/'source/DESIGN_R8.json'),'--native',str(r8/'native'),'--prior',str(inputs/'inputs/r5/profiles'),'--prior',str(inputs/'native'),
   '--original',str(inputs/'inputs/r5/SOURCE_original_backup.zip'),'--output',str(reports/'QA_UNCHANGED_NATIVE_R8.json')],folder)
  checked=folder/'Azeron_R8_Action_Atlas_Checked_HE.html'
  command('atlas_build',[sys.executable,str(ROOT/'build_checked_atlas.py'),'--r8',str(r8),'--out',str(checked)],folder)
  node=shutil.which('node')
  if node:
   env['QA_OUTPUT']=str(reports/'QA_ATLAS_PREFLIGHT.json')
   command('atlas_additional_checks',[node,str(ROOT/'test_atlas_preflight.js'),str(checked)],folder)
   command('atlas_original_query_checks',[node,str(r8/'source/test_atlas.js'),str(checked)],folder)
   command('atlas_existing_event_checks',[node,str(r8/'source/test_ui_events.js'),str(checked)],folder)
   for name in ['QA_ATLAS_R8.json','QA_UI_EVENTS_R8.json']:
    p=r8/'source'/name
    if p.exists():shutil.copyfile(p,reports/name)
  else:steps.append({'step':'JavaScript_tests','passed':None,'status':'NOT_RUN_NODE_UNAVAILABLE'})
  status='OFFLINE_CHECKS_PASSED' if node else 'PARTIAL_NODE_UNAVAILABLE'
 except (ReviewError,subprocess.TimeoutExpired,OSError) as e:
  status='TEST_FAILURE_OR_UNKNOWN_EFFECT_NO_RETRY'
  write_report(folder,'RUN_RECEIPT.json',{'schema':'azeron-rehearsal/v1','status':status,'created_utc':timestamp(),'steps':steps,'native_imported':False,'game_launched':False,'live_state_verified':False})
  raise ReviewError('Offline rehearsal did not finish. Inspect its saved results before retrying.') from e
 result={'schema':'azeron-rehearsal/v1','status':status,'created_utc':timestamp(),'steps':steps,'native_family_revision':'R8_UNCHANGED',
  'native_imported':False,'new_native_identity_created_for_delivery':False,'game_launched':False,'live_state_verified':False,'real_browser_tested':False,
  'archive_sha256':R8_SHA,'source_preservation':hashlib.sha256(read_regular(archive,8_000_000)[0]).hexdigest()==R8_SHA}
 write_report(folder,'RUN_RECEIPT.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--r8',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 try:r=rehearse(a.r8,a.out)
 except (ReviewError,OSError) as e:raise SystemExit('STOP: '+str(e))
 print(json.dumps(r,indent=2))
