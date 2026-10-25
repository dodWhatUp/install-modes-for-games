"""Build only reviewed Mod Controls 2.2 changes over the verified incumbent."""
import argparse,copy,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path

OWNED=[
 'scripts/GameToolModControls.py','scripts/GameToolModControlsPanel.py',
 'scripts/GameToolWickedControls.py','scripts/GameToolModControlCatalog.py',
 'scripts/GameToolFloatingWindows.py','scripts/GameToolModGallery.py',
 'scripts/GameToolModDiscovery.py','scripts/GameToolModDiscoveryUI.py',
 'scripts/Build-ModControlExtensions.py',
 'scripts/tests/Test-GameToolWickedControls.py','scripts/tests/Test-GameToolModModulesPanel.py',
 'scripts/tests/Test-GameToolModDiscovery.py','scripts/tests/Test-GameToolModDiscoveryUI.py',
 'examples/game-tool-hub/game-support/discovery/identities.json',
 'examples/game-tool-hub/game-support/no-rest-for-the-wicked.json',
 'examples/game-tool-hub/game-support/controls/no-rest-for-the-wicked.json',
 'docs/MULTI-GAME-MOD-CONTROLS.md','docs/MOD-CONTROL-CONTRACT.md',
 'templates/MOD-CONTROL-CATALOG.example.json',
]
def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_mod_control_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    if payloads.get('scripts/GameToolEditableLists.py')!=(source/'scripts/GameToolEditableLists.py').read_bytes():
        raise ValueError('Reconcile and test the incumbent shared editable-list owner before packaging.')
    paths=OWNED+[p.relative_to(source).as_posix() for p in (source/'examples/no-rest-for-the-wicked-controls').iterdir() if p.suffix in {'.py','.md','.json'}]
    for path in paths:payloads[api.member_name(path)]=(source/path).read_bytes()
    manifest=copy.deepcopy(before['manifest']);manifest['component_versions'].update(mod_controls='2.2.0',mod_control_catalog='1.0.0',mod_gallery='1.0.0',mod_discovery='1.0.0')
    manifest['component_update']={'component':'mod_controls','version':'2.2.0',
        'base_manifest_sha256':hashlib.sha256((base/'MANIFEST.json').read_bytes()).hexdigest(),
        'incumbent_sources_preserved_except':sorted(paths),'game_state_included':False}
    manifest['files']=[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2,ensure_ascii=True)+'\n')
        for path,raw in sorted(payloads.items()):archive.writestr(path,raw)
    sha=hashlib.sha256(output.read_bytes()).hexdigest();release=api.inspect_archive(output,sha)
    changed=[p for p,raw in before['payloads'].items() if payloads[p]!=raw]
    assert set(changed)<=set(paths)
    assert release['manifest']['component_versions']['tool_hub']==before['manifest']['component_versions']['tool_hub']
    return {'path':str(output),'sha256':sha,'base':str(base),'files':len(payloads),
        'unchanged_incumbent_files':sum(payloads[p]==raw for p,raw in before['payloads'].items()),
        'changed_incumbent_files':changed,'added_files':sorted(set(payloads)-set(before['payloads'])),
        'component_versions':release['manifest']['component_versions']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
