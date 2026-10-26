"""Compose a UI-only release over an independently verified installed baseline."""
import argparse,copy,importlib.util,json,subprocess,sys,zipfile
from pathlib import Path

OWNED=['scripts/Game-Tool-Hub.py','scripts/GameToolAppMenus.py',
       'scripts/GameToolUIReview.py','scripts/GameToolUIReviewWidgets.py',
       'scripts/GameToolModControlsPanel.py','scripts/tests/Test-AppMenus.py',
       'scripts/tests/Test-GameToolUIReviewGUI.py','scripts/tests/Test-GameToolModControlsPanel.py',
       'scripts/Build-CompactAppsRelease.py','examples/shadow-of-war-controls/mod_panel.py',
       'examples/no-rest-for-the-wicked-controls/mod_panel.py','docs/COMPACT-APP-MENUS-2026-10-26.md',
       'docs/UI-AND-CONTENT-DESIGN.md','docs/design-history/UI-AND-CONTENT-DESIGN-2026-10-25.md',
       'preferences/GENERAL.md']

def build(base,source,output):
    spec=importlib.util.spec_from_file_location('_compact_apps_incumbent',base/'scripts/GameToolUnified.py')
    api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source,text=True).strip()
    if subprocess.check_output(['git','status','--porcelain','--',*OWNED],cwd=source,text=True).strip():
        raise ValueError('Commit the scoped UI source before building.')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    manifest=copy.deepcopy(before['manifest'])
    manifest['component_versions'].update(tool_hub='0.27.32-preview.1',app_menus='0.1.0')
    manifest['component_update']={'component':'compact_apps','source_commit':commit,
      'base_manifest_sha256':api.digest((base/'MANIFEST.json').read_bytes()),
      'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':name,'bytes':len(raw),'sha256':api.digest(raw)}for name,raw in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED)as archive:
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for name,raw in sorted(payloads.items()):archive.writestr(name,raw)
    digest=api.digest(output.read_bytes());api.inspect_archive(output,digest)
    return {'archive':str(output),'sha256':digest,'payloads':len(payloads),
      'incumbent_files_preserved':sum(payloads[name]==raw for name,raw in before['payloads'].items())}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',required=True,type=Path)
    parser.add_argument('--source',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();print(json.dumps(build(args.base,args.source,args.output),indent=2))
