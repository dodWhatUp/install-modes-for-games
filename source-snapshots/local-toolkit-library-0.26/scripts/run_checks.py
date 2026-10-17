#!/usr/bin/env python3
"""Reproduce bounded synthetic tests; does not install or touch game configurations."""
from pathlib import Path
import argparse,datetime,json,os,platform,re,shutil,subprocess,sys

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--host',type=Path);ap.add_argument('--output',required=True,type=Path);a=ap.parse_args()
    root=Path(__file__).absolute().parents[1];a.output.mkdir(parents=True,exist_ok=False)
    commands=[('core',[sys.executable,'scripts/tests/test_keybinds.py'],root),
              ('extended',[sys.executable,'scripts/tests/test_extended.py'],root),
              ('extensibility',[sys.executable,'scripts/tests/test_extensibility.py'],root),
              ('effective',[sys.executable,'scripts/tests/test_effective.py'],root)]
    panel=[sys.executable,'scripts/tests/test_panel.py']
    if os.name!='nt':
        xvfb=shutil.which('xvfb-run');panel=[xvfb,'-a',*panel] if xvfb else None
    if panel:
        commands.append(('panel',panel,root))
        pack_panel=list(panel);pack_panel[-1]='scripts/tests/test_pack_panel.py';commands.append(('pack-panel',pack_panel,root))
    if a.host:
        commands += [('host-integration',[sys.executable,'scripts/tests/test_host_integration.py'],root),
                     ('pack-integration',[sys.executable,'scripts/tests/test_pack_integration.py'],root),
                     ('host-workspaces-regression',[sys.executable,'scripts/tests/Test-GameToolGameWorkspaces.py'],a.host),
                     ('host-automation-regression',[sys.executable,'scripts/tests/Test-GameToolAutomation.py'],a.host),
                     ('host-journal-regression',[sys.executable,'scripts/tests/Test-GameToolJournal.py'],a.host)]
    env=dict(os.environ)
    if a.host:env['GAME_TOOLS_HOST_SOURCE']=str(a.host.absolute())
    results=[]
    for name,argv,cwd in commands:
        # Native tests are fixture-only; no retry after a timeout or unknown effect.
        try:
            process=subprocess.run(argv,cwd=cwd,env=env,capture_output=True,timeout=40)
            raw=process.stdout+process.stderr;returncode=process.returncode
            text=raw.decode('utf-8','replace');found=re.search(r'Ran (\d+) tests?',text)
            result={'suite':name,'returncode':returncode,'tests':int(found.group(1)) if found else None,'passed':returncode==0,'log':name+'.log'}
        except subprocess.TimeoutExpired as e:
            raw=(e.stdout or b'')+(e.stderr or b'');result={'suite':name,'passed':False,'status':'TIMEOUT_NO_RETRY','tests':None,'log':name+'.log'}
        (a.output/(name+'.log')).write_bytes(raw);results.append(result)
    report={'schema_version':1,'module':'Game Tools Keybinds','version':'0.2.0-preview.1','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'runtime':{'system':platform.system(),'python':platform.python_version()},'suites':results,
            'total_test_methods':sum(r['tests'] or 0 for r in results),'all_executed_suites_passed':all(r['passed'] for r in results),
            'scope':'ten built-in synthetic formats, extensible packs/SDK, effective multi-file owners, sparse overrides, controls, JSON-RPC stdio, draft deltas, own child interruption, headless widgets and unchanged host regression services',
            'excluded':['native Windows API/ACL/launcher tests','real game configuration schemas','installed Hub integration','real MCP client or ChatGPT connection','in-game/physical Azeron acceptance','screenshots/video/recording/benchmarks'],
            'headless_panel_executed':panel is not None,'host_reference':'0.23.0-preview.1' if a.host else None,
            'native_game_files_changed':0,'profile_files_changed':0,'host_files_modified':False,'new_services_installed':False,'notes':['Nested subtest iterations are not counted as separate test methods.','Original host regression suites were run unmodified; this is not the entire application regression suite.']}
    (a.output/'VALIDATION.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));return 0 if report['all_executed_suites_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
