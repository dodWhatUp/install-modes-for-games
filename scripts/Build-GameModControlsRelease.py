"""Build a reviewed component update from an exact verified incumbent source set."""
import argparse,copy,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path

OWNED=[
 'scripts/GameToolModControls.py','scripts/GameToolModControlsPanel.py','scripts/GameToolModControlAI.py',
 'scripts/GameToolModControlsLaunch.pyw','scripts/Build-GameModControlsRelease.py',
 'scripts/Create-ModControlsLauncher.py',
 'scripts/GameToolModIntegration.py','scripts/GameToolInstances.py','scripts/GameToolGameWorkspaces.py','scripts/GameToolAITools.py',
 'scripts/GameToolFocusUI.py','examples/game-tool-hub/game-support/middle-earth-shadow-of-war.json',
 'scripts/GameToolAIModern.py','scripts/tests/Test-GameToolAIModern.py',
 'scripts/GameToolAIKnowledge.py',
 'scripts/GameToolUnified.py',
 'scripts/tests/Test-GameToolModControls.py','scripts/tests/Test-GameToolModControlsPanel.py','scripts/tests/Test-GameToolGameWorkspaces.py',
 'examples/game-tool-hub/game-support/controls/middle-earth-shadow-of-war.json',
 'docs/MULTI-GAME-MOD-CONTROLS.md',
]
def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_incumbent_release_verifier',base/'scripts/GameToolUnified.py');verifier=importlib.util.module_from_spec(spec);sys.modules[spec.name]=verifier;spec.loader.exec_module(verifier)
    before=verifier.inspect_directory(base);payloads=dict(before['payloads']);paths=OWNED+[p.relative_to(source).as_posix() for p in (source/'examples/shadow-of-war-controls').iterdir() if p.suffix in {'.py','.md'}]
    for path in paths:payloads[verifier.member_name(path)]=(source/path).read_bytes()
    manifest=copy.deepcopy(before['manifest']);manifest['component_versions'].update(mod_controls='2.0.0',mod_integration='0.2.0',instances='0.2.0')
    manifest['component_update']={'component':'mod_controls','version':'2.0.0','base_manifest_sha256':hashlib.sha256((base/'MANIFEST.json').read_bytes()).hexdigest(),'incumbent_sources_preserved_except':sorted(paths),'game_state_included':False}
    manifest['files']=[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(payloads.items())]
    verifier.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2,ensure_ascii=True)+'\n')
        for path,raw in sorted(payloads.items()):archive.writestr(path,raw)
    sha=hashlib.sha256(output.read_bytes()).hexdigest();checked=verifier.inspect_archive(output,sha)
    return {'path':str(output),'sha256':sha,'files':len(payloads),'unchanged_incumbent_files':sum(payloads[p]==raw for p,raw in before['payloads'].items()),'component_versions':checked['manifest']['component_versions']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--base',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
