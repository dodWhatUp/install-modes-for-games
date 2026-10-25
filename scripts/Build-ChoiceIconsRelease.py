"""Compose a scoped icon presentation update over the verified current owner."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path
OWNED=['scripts/GameToolChoiceIcons.py','scripts/GameToolEditableLists.py','scripts/Game-Tool-Hub.py',
       'scripts/tests/Test-ChoiceIcons.py','scripts/Build-ChoiceIconsRelease.py','docs/CHOICE-FIELD-ICONS.md']
def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_icons_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True).strip():raise ValueError('Commit the scoped icon source first.')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.28-preview.2',editable_lists='0.1.3',choice_icons='0.1.1')
    manifest['component_update']={'component':'choice_icons','source_commit':commit,
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),
      'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':n,'bytes':len(b),'sha256':api.digest(b)}for n,b in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as z:
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for n,b in sorted(payloads.items()):z.writestr(n,b)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),
      'incumbent_files_preserved':sum(payloads[n]==b for n,b in before['payloads'].items())}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
