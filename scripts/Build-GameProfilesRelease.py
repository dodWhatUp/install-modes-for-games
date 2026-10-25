"""Build a scoped game-profile update over the exact verified incumbent."""
import argparse,copy,hashlib,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path
OWNED=[
 'scripts/GameToolGameProfiles.py','scripts/GameToolGameProfilesUI.py','scripts/GameToolRewasd.py','scripts/Build-GameProfilesRelease.py',
 'scripts/Game-Tool-Hub.py','scripts/GameToolUnifiedPanel.py','scripts/GameToolWorkspace.py','scripts/GameToolModernUI.py',
 'examples/game-input/AzeronOverlayStudio.integrated.ahk','examples/game-input/StudioHubBridge.ahk',
 'scripts/tests/Test-GameProfiles.py','scripts/tests/Test-GameProfilesGUI.py','scripts/tests/Test-RewasdProfiles.py','scripts/tests/Test-GameToolWorkspace.py','scripts/tests/Test-GameToolModernUI.py',
 'docs/GAME-PROFILES.md']
def build(base,source,output):
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    dirty=subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True)
    if dirty:raise ValueError('Commit the scoped component sources before packaging; preserve other work')
    spec=importlib.util.spec_from_file_location('_profiles_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.24-preview.1',overlay_studio='2.2.0-unified.23',unified_panel='0.5.0',workspace='0.4.1',modern_ui='0.1.2',game_profiles='0.2.0',game_profiles_ui='0.2.0',rewasd='0.1.0')
    manifest['component_update']={'component':'game_profiles','base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),
      'source_commit':commit,'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':p,'bytes':len(v),'sha256':api.digest(v)}for p,v in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as z:
        z.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for name,raw in sorted(payloads.items()):z.writestr(name,raw)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),
      'unchanged_incumbent_payloads':sum(payloads[n]==raw for n,raw in before['payloads'].items()),'owned':OWNED}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',required=True,type=Path);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
