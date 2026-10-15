#!/usr/bin/env python3
"""Run merged keybind source/headless suites; no installed game files."""
from pathlib import Path
import argparse,datetime,json,os,platform,re,shutil,subprocess,sys

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
 root=Path(__file__).resolve().parents[2];tests=root/'scripts/tests/keybinds';a.output.mkdir(parents=True,exist_ok=False)
 env=dict(os.environ);env['GAME_TOOLS_HOST_SOURCE']=str(root);env['PYTHONDONTWRITEBYTECODE']='1'
 commands=[('core',[sys.executable,str(tests/'test_keybinds.py')],root),('extended',[sys.executable,str(tests/'test_extended.py')],root),
 ('extensibility',[sys.executable,str(tests/'test_extensibility.py')],root),('effective',[sys.executable,str(tests/'test_effective.py')],root),
 ('host-integration',[sys.executable,str(tests/'test_host_integration.py')],root),('pack-integration',[sys.executable,str(tests/'test_pack_integration.py')],root),
 ('schema-contract',[sys.executable,str(tests/'test_schema_contract.py')],root)]
 xvfb=shutil.which('xvfb-run')
 for n in ('panel','pack-panel'):
  script=tests/('test_'+n.replace('-','_')+'.py');commands.append((n,[xvfb,'-a',sys.executable,str(script)] if xvfb else [sys.executable,str(script)],root))
 results=[]
 for name,argv,cwd in commands:
  try:
   r=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=80);raw=r.stdout+r.stderr;status='EXECUTED';rc=r.returncode
  except subprocess.TimeoutExpired as e:
   raw=(e.stdout or b'')+(e.stderr or b'');status='TIMEOUT_NO_RETRY';rc=None
  (a.output/(name+'.log')).write_bytes(raw);m=re.search(rb'Ran (\d+) tests?',raw)
  results.append({'suite':name,'status':status,'returncode':rc,'tests':int(m.group(1)) if m else None,'passed':status=='EXECUTED' and rc==0,'log':name+'.log'})
 report={'schema_version':1,'source_version':'0.27.0-preview.1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'runtime':{'system':platform.system(),'python':platform.python_version()},'suites':results,
  'total_test_methods':sum(r['tests'] or 0 for r in results),'all_passed':all(r['passed'] for r in results),
  'scope':'merged source/headless keybind, host integration, pack integration and widgets',
  'excluded':['native Windows API/ACL/launcher acceptance','installed Hub acceptance','real game files/gameplay','physical Azeron','recording/benchmarks']}
 (a.output/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return 0 if report['all_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
