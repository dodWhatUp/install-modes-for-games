"""Explicit launcher delivery for an existing verified unified installation."""
import argparse,hashlib,importlib.util,json,os,shutil,subprocess,sys,uuid
from pathlib import Path

def deliver(install,desktop=None):
    if os.name!='nt':raise ValueError('Windows launcher delivery requires Windows.')
    install=install.resolve();state=json.loads((install/'install.json').read_text(encoding='utf-8'))
    versions=(install/'versions').resolve();current=(versions/state['current']).resolve()
    if current.parent!=versions:raise ValueError('Invalid version pointer.')
    manifest=json.loads((current/'MANIFEST.json').read_text(encoding='utf-8'));updater=current/'scripts/GameToolUnified.py'
    expected=next(r['sha256'] for r in manifest['files'] if r['path']=='scripts/GameToolUnified.py')
    if hashlib.sha256(updater.read_bytes()).hexdigest()!=expected:raise ValueError('Updater integrity differs.')
    spec=importlib.util.spec_from_file_location('_launcher_delivery_verifier',updater);api=importlib.util.module_from_spec(spec);sys.modules[spec.name]=api;spec.loader.exec_module(api)
    api.verify_current(install,state);lease=api.acquire_source_lease(state['studio_dir'],'mod-controls-launcher-delivery')
    recovery=install/'recovery'/('mod-controls-launchers-'+uuid.uuid4().hex)
    def put(path,raw):
        if path.exists():shutil.copyfile(path,recovery/path.name)
        api._replace_file(path,raw)
    try:
        recovery.mkdir(parents=True)
        put(install/'Game-Mod-Controls.pyw',(current/'scripts/GameToolModControlsLaunch.pyw').read_bytes())
        name='Game Mod Controls APP LAUNCHER'
        put(install/(name+'.cmd'),('@echo off\r\nstart "" "'+state['pythonw']+'" "%~dp0Game-Mod-Controls.pyw"\r\n').encode('utf-8'))
        result={'included_launcher':str(install/(name+'.cmd')),'entry':str(install/'Game-Mod-Controls.pyw'),'recovery':str(recovery),'opens_only':True}
        if desktop:
            shortcut=desktop/(name+'.lnk')
            if shortcut.exists():shutil.copyfile(shortcut,recovery/shortcut.name)
            env=dict(os.environ,MODCONTROL_LINK=str(shortcut),MODCONTROL_PYTHON=state['pythonw'],MODCONTROL_ENTRY=str(install/'Game-Mod-Controls.pyw'),MODCONTROL_ROOT=str(install))
            command='$w=New-Object -ComObject WScript.Shell; $s=$w.CreateShortcut($env:MODCONTROL_LINK); $s.TargetPath=$env:MODCONTROL_PYTHON; $s.Arguments=[char]34+$env:MODCONTROL_ENTRY+[char]34; $s.WorkingDirectory=$env:MODCONTROL_ROOT; $s.Description="Open shared Game Mod Controls"; $s.Save(); $v=$w.CreateShortcut($env:MODCONTROL_LINK); @{target=$v.TargetPath;arguments=$v.Arguments;working_directory=$v.WorkingDirectory}|ConvertTo-Json -Compress'
            r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],env=env,capture_output=True,text=True,check=True,timeout=15,creationflags=subprocess.CREATE_NO_WINDOW)
            checked=json.loads(r.stdout);assert Path(checked['target'])==Path(state['pythonw']) and checked['arguments']=='"'+str(install/'Game-Mod-Controls.pyw')+'"' and Path(checked['working_directory'])==install
            result.update(desktop_shortcut=str(shortcut),verified_target=checked)
        (recovery/'receipt.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');return result
    finally:api.release_source_lease(lease)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--install-root',type=Path,required=True);p.add_argument('--desktop',type=Path);a=p.parse_args();print(json.dumps(deliver(a.install_root,a.desktop),indent=2))
