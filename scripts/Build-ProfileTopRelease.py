"""Remove the duplicate Modern profile heading over a verified incumbent."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path

OWNED=['scripts/Game-Tool-Hub.py','scripts/GameToolModernUI.py','scripts/GameToolWorkspace.py',
       'scripts/tests/Test-GameToolModernUI.py','docs/PROFILE-PAGE-HEADER.md','scripts/Build-ProfileTopRelease.py']

def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_profile_top_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    if subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True).strip():raise ValueError('Commit the scoped presentation source first')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.34-preview.1',modern_ui='0.1.5',workspace='0.4.5')
    manifest['component_update']={'component':'profile_top','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':name,'bytes':len(raw),'sha256':api.digest(raw)}for name,raw in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as archive:
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for name,raw in sorted(payloads.items()):archive.writestr(name,raw)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),'incumbent_preserved':sum(payloads[n]==raw for n,raw in before['payloads'].items())}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',type=Path,required=True);parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(build(args.base,args.source,args.output),indent=2))
