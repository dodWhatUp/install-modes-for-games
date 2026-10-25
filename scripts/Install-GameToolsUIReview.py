"""Create a new parallel preview from a verified incumbent; no source switch."""
import argparse,copy,hashlib,importlib.util,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path

OWNED=['scripts/GameToolUIReview.py','scripts/GameToolUIReviewModel.py','scripts/GameToolUIReviewWidgets.py',
       'scripts/GameToolUIReviewSearch.py','scripts/tests/Test-GameToolUIReviewSearch.py',
       'scripts/GameToolUIReviewBoot.pyw','scripts/Install-GameToolsUIReview.py',
       'scripts/tests/Test-GameToolUIReview.py','scripts/tests/Test-GameToolUIReviewGUI.py','docs/UI-WORKFLOW-PARALLEL-PREVIEW.md']
NAMES={'mods':'Mod Controls UI Preview APP LAUNCHER','files':'Game Tools UI Preview APP LAUNCHER'}
def install(current,source,destination,desktop=None,review_data=None):
    current=current.resolve();destination=destination.absolute()
    if destination.exists():raise ValueError('Use a new named preview folder; existing apps are never merged or replaced.')
    state_raw=(current/'install.json').read_bytes();state=json.loads(state_raw);base=(current/'versions'/state['current']).resolve()
    if base.parent!=(current/'versions').resolve():raise ValueError('Invalid incumbent version pointer.')
    spec=importlib.util.spec_from_file_location('_ui_review_base_verifier',base/'scripts/GameToolUnified.py');api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    existing=api.verify_current(current,state);payloads=dict(existing['payloads'])
    for relative in OWNED:payloads[api.member_name(relative)]=(source/relative).read_bytes()
    manifest=copy.deepcopy(existing['manifest']);manifest['component_versions']['ui_workflow_review']='0.2.0'
    manifest['parallel_review']={'version':'0.2.0','incumbent':state['current'],'production_source_switched':False,'native_profiles_migrated':False}
    manifest['files']=[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(payloads.items())];api.check_manifest(manifest,payloads)
    destination.mkdir(parents=True);package=destination/'source';package.mkdir()
    for relative,raw in payloads.items():
        target=package/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        if target.read_bytes()!=raw:raise ValueError('Preview source copy differs.')
    manifest_raw=(json.dumps(manifest,indent=2,ensure_ascii=True)+'\n').encode();(package/'MANIFEST.json').write_bytes(manifest_raw)
    review_data=Path(review_data).absolute() if review_data else destination/'review-data'
    from GameToolUIReviewModel import ReviewModel
    ReviewModel(state['data_dir'],review_data,current)  # Validate separation before writing configuration.
    config={'schema_version':1,'source_data':state['data_dir'],'review_data':str(review_data),'install_root':str(current),'base_installed_version':state['current'],'source_manifest_sha256':hashlib.sha256(manifest_raw).hexdigest(),'pythonw':state['pythonw']}
    (destination/'review-config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8');(destination/'GameToolsUIReview.pyw').write_bytes(payloads['scripts/GameToolUIReviewBoot.pyw'])
    entries=[]
    for page,name in NAMES.items():
        path=destination/(name+'.cmd');path.write_text('@echo off\nstart "" "'+state['pythonw']+'" "%~dp0GameToolsUIReview.pyw" --page '+page+'\n',encoding='utf-8');entries.append(str(path))
        if desktop:
            if os.name!='nt':raise ValueError('Desktop shortcuts need Windows.')
            link=desktop/(name+'.lnk')
            if link.exists():
                recovery=destination/'launcher-recovery';recovery.mkdir(exist_ok=True);shutil.copyfile(link,recovery/link.name)
            env=dict(os.environ,UIREVIEW_LINK=str(link),UIREVIEW_PYTHON=state['pythonw'],UIREVIEW_ENTRY=str(destination/'GameToolsUIReview.pyw'),UIREVIEW_ROOT=str(destination),UIREVIEW_PAGE=page)
            command='$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut($env:UIREVIEW_LINK);$s.TargetPath=$env:UIREVIEW_PYTHON;$s.Arguments=[char]34+$env:UIREVIEW_ENTRY+[char]34+" --page "+$env:UIREVIEW_PAGE;$s.WorkingDirectory=$env:UIREVIEW_ROOT;$s.Description="Open separate Game Tools UI preview";$s.Save();$v=$w.CreateShortcut($env:UIREVIEW_LINK);@{target=$v.TargetPath;arguments=$v.Arguments;working_directory=$v.WorkingDirectory}|ConvertTo-Json -Compress'
            result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],env=env,capture_output=True,text=True,check=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW);verified=json.loads(result.stdout)
            if Path(verified['target'])!=Path(state['pythonw']) or verified['arguments']!='"'+str(destination/'GameToolsUIReview.pyw')+'" --page '+page or Path(verified['working_directory'])!=destination:raise ValueError('Shortcut target readback differs.')
    archive=destination/'UI-Review-Authored-Source.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('MANIFEST.json',manifest_raw)
        for relative,raw in sorted(payloads.items()):z.writestr(relative,raw)
    checked=api.inspect_archive(archive,hashlib.sha256(archive.read_bytes()).hexdigest())
    if (current/'install.json').read_bytes()!=state_raw:raise ValueError('The incumbent pointer changed during preparation. Preserve the preview and reconcile its baseline.')
    receipt={'version':'0.2.0','destination':str(destination),'source_files':len(payloads),'source_package_sha256':checked['sha256'],'base_installed_version':state['current'],'incumbent_pointer_unchanged':True,'incumbent_payloads_preserved':sum(payloads[k]==v for k,v in existing['payloads'].items()),'launcher_entries':entries,'desktop':str(desktop) if desktop else None,'separate_review_data':config['review_data'],'adopted':False,'game_settings_applied':False}
    (destination/'DELIVERY-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--current-install',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);p.add_argument('--desktop',type=Path);p.add_argument('--review-data',type=Path,help='Reuse an existing separate preview data folder without copying or resetting drafts.');a=p.parse_args();print(json.dumps(install(a.current_install,a.source,a.destination,a.desktop,a.review_data),indent=2))
