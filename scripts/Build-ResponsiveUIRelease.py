"""Preserve the verified incumbent; replace only reviewed layout sources."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path
OWNED=['scripts/GameToolModernUI.py','scripts/GameToolAppearance.py','scripts/Game-Tool-Hub.py',
 'scripts/tests/Test-GameToolModernUI.py','scripts/Build-ResponsiveUIRelease.py','docs/RESPONSIVE-UI.md',
 'scripts/GameToolCompactHeader.py']
def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_responsive_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True).strip():raise ValueError('Commit the scoped layout source first')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.27-preview.1',modern_ui='0.1.3',appearance='0.5.4',compact_header='0.1.0')
    manifest['component_update']={'component':'responsive_ui','source_commit':commit,
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':n,'bytes':len(b),'sha256':api.digest(b)}for n,b in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as z:
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for n,b in sorted(payloads.items()):z.writestr(n,b)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),'incumbent_files_preserved':sum(payloads[n]==b for n,b in before['payloads'].items())}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
