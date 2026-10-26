"""Compose Windows app-access sources over the exact verified incumbent."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path

OWNED=['scripts/Game-Tool-Hub.py','scripts/Start-UnifiedTools.pyw','scripts/GameToolWindowsApp.py',
       'scripts/GameToolWindowsShortcut.py','scripts/GameToolCompactHeader.py','scripts/GameToolWorkspace.py',
       'scripts/GameToolAppMenus.py','scripts/GameToolUIReview.py','scripts/GameToolModControlsPanel.py',
       'scripts/Register-GameToolsWindowsApp.py','scripts/Generate-AppIcons.py','scripts/Build-WindowsAppRelease.py',
       'scripts/tests/Test-WindowsApp.py','scripts/tests/Test-WindowsShortcut.py','scripts/tests/Test-GameToolModernUI.py',
       'examples/shadow-of-war-controls/mod_panel.py','examples/no-rest-for-the-wicked-controls/mod_panel.py',
       'docs/WINDOWS-APP-ACCESS.md']

def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_windows_access_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    names=OWNED+[str(path.relative_to(source)).replace('\\','/')for path in sorted((source/'scripts/app-icons').glob('*'))]
    if subprocess.check_output(['git','status','--porcelain','--',*names],cwd=source,text=True).strip():raise ValueError('Commit the scoped app-access source first')
    for name in names:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.33-preview.2',windows_app='0.1.0',compact_header='0.3.0',workspace='0.4.4',app_menus='0.2.0')
    manifest['component_update']={'component':'windows_app_access','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip(),
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),'incumbent_sources_preserved_except':names,'game_state_included':False}
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
