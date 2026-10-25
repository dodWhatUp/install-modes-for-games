"""Add interface views to a verified incumbent; preserve every other source byte."""
import argparse,copy,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path
OWNED=['scripts/GameToolInterfaceViews.py','scripts/GameToolUIReview.py','scripts/GameToolUIReviewModel.py','scripts/GameToolUIReviewWidgets.py','scripts/GameToolUIReviewSearch.py','scripts/GameToolModIntegration.py','scripts/Game-Tool-Hub.py','scripts/Build-GameInterfaceRelease.py','scripts/Create-GameInterfaceLauncher.py','scripts/tests/Test-GameToolInterfaceViews.py','scripts/tests/Test-GameInterfacePackaging.py','scripts/tests/Test-GameToolUIReview.py','scripts/tests/Test-GameToolUIReviewGUI.py','scripts/tests/Test-GameToolUIReviewSearch.py','docs/UNIFIED-INTERFACE-VIEWS.md']
def enable_profiles_page(raw):
    text=raw.decode('utf-8');lines=text.splitlines(keepends=True)
    if "load_catalog_module('GameToolGameProfilesUI')" not in text:return raw
    matches=[i for i,line in enumerate(lines) if 'if name not in {' in line]
    if len(matches)!=1:raise ValueError('Review the changed Hub module allowlist before enabling its Profiles page.')
    i=matches[0]
    if '"GameToolGameProfilesUI"' in lines[i]:return raw
    lines[i]=lines[i].replace('if name not in {','if name not in {"GameToolGameProfilesUI", ',1)
    result=''.join(lines);compile(result,'Game-Tool-Hub.py','exec');return result.encode('utf-8')
def integrate_owner(raw):
    newline='\r\n' if b'\r\n' in raw else '\n';text=raw.decode('utf-8').replace('\r\n','\n')
    if 'self.interface_views=' in text:raise ValueError('Interface integration already exists; compare it before updating.')
    inserts=[("        self.routes['mod-controls']=self.mod_controls\n", "        self.interface_views=None\n        self._interface_attempts=0\n        def mount_interfaces():\n            self._interface_job=None\n            if getattr(notebook.winfo_toplevel(),'game_tools_notebook',None) is not notebook:\n                self._interface_attempts+=1\n                if self._interface_attempts<200:self._interface_job=notebook.after(50,mount_interfaces)\n                return\n            try:\n                from GameToolInterfaceViews import mount\n                self.interface_views=mount(notebook,self.mod_controls.controls,data_dir,status)\n            except (ImportError,OSError,ValueError,TclError) as error:\n                status.set('Existing interface retained: '+str(error))\n        self._interface_job=notebook.after(50,mount_interfaces)\n"),
             ('    def can_close(self):\n','        if self.interface_views is not None and not self.interface_views.can_close():return False\n'),
             ('    def close(self):\n','        if self._interface_job is not None:\n            self.mods.after_cancel(self._interface_job);self._interface_job=None\n        if self.interface_views is not None:self.interface_views.close()\n')]
    for anchor,addition in inserts:
        if text.count(anchor)!=1:raise ValueError('Integration owner changed; review the exact hook before packaging.')
        text=text.replace(anchor,anchor+addition)
    compile(text,'GameToolModIntegration.py','exec')
    return text.replace('\n',newline).encode('utf-8')
def build(base,source,output):
    base,source,output=Path(base).resolve(),Path(source).resolve(),Path(output).resolve()
    spec=importlib.util.spec_from_file_location('_interface_incumbent_verifier',base/'scripts/GameToolUnified.py');api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    before=api.inspect_directory(base);payloads=dict(before['payloads'])
    # Never replace newer runtime/Overlay/Studio/planner/updater sources with
    # an older branch. The one integration owner must match its reviewed base.
    original=before['payloads']['scripts/GameToolModIntegration.py'].decode('utf-8')
    if "self.routes['mod-controls']=self.mod_controls" not in original:raise ValueError('Base has no reviewed Mod Controls integration; reconcile it first.')
    if 'interface_views' in original:raise ValueError('An interface integration already exists; compare it instead of replacing it.')
    for name in OWNED:payloads[api.member_name(name)]=(source/name).read_bytes()
    payloads['scripts/GameToolModIntegration.py']=integrate_owner(before['payloads']['scripts/GameToolModIntegration.py'])
    payloads['scripts/Game-Tool-Hub.py']=enable_profiles_page(before['payloads']['scripts/Game-Tool-Hub.py'])
    manifest=copy.deepcopy(before['manifest']);manifest['component_versions']['interface_views']='1.0.1'
    manifest['component_update']={'component':'interface_views','version':'1.0.1','base_manifest_sha256':hashlib.sha256((base/'MANIFEST.json').read_bytes()).hexdigest(),'incumbent_sources_preserved_except':OWNED,'game_state_included':False}
    manifest['files']=[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(payloads.items())]
    api.check_manifest(manifest,payloads)
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr('MANIFEST.json',json.dumps(manifest,indent=2)+'\n')
        for path,raw in sorted(payloads.items()):archive.writestr(path,raw)
    sha=hashlib.sha256(output.read_bytes()).hexdigest();api.inspect_archive(output,sha)
    return {'path':str(output),'sha256':sha,'files':len(payloads),'unchanged_incumbent_files':sum(payloads[p]==raw for p,raw in before['payloads'].items()),'base_files':len(before['payloads']),'base_manifest_sha256':manifest['component_update']['base_manifest_sha256']}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.base,a.source,a.output),indent=2))
