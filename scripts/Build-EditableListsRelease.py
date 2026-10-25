"""Scoped UI update over the exact verified incumbent; preserve other owners."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path
OWNED=['scripts/GameToolEditableLists.py','scripts/GameToolCompactUI.py','scripts/Game-Tool-Hub.py',
 'scripts/GameToolGameProfiles.py','scripts/tests/Test-GameProfiles.py',
 'examples/game-input/AzeronOverlayStudio.integrated.ahk','examples/game-input/StudioOverlayGroups.ahk',
 'scripts/tests/Test-EditableLists.py','scripts/tests/Test-GameToolCompactUI.py',
 'scripts/Build-EditableListsRelease.py','docs/EDITABLE-CHOICE-LISTS.md']
def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_editable_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True).strip():
        raise ValueError('Commit the scoped source before packaging')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.25-preview.1',overlay_studio='2.2.0-unified.24',
      compact_ui='0.5.0',editable_lists='0.1.2',overlay_groups='0.1.13',game_profiles='0.2.1')
    manifest['component_update']={'component':'editable_lists','source_commit':commit,
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),
      'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':name,'bytes':len(raw),'sha256':api.digest(raw)}for name,raw in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as z:
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for name,raw in sorted(payloads.items()):z.writestr(name,raw)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),
      'incumbent_files_preserved':sum(payloads[n]==raw for n,raw in before['payloads'].items())}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
