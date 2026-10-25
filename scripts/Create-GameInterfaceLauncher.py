"""Include the named entry and Desktop shortcut; retain legacy launchers/settings."""
import argparse,datetime,json,os,shutil,subprocess,sys
from pathlib import Path
import GameToolUnified as api
NAME='Unified Game Tools APP LAUNCHER'
def prepare(root,desktop,recovery):
    root,desktop,recovery=map(api.local_path,(root,desktop,recovery))
    state=api.read_install(root);api.verify_current(root,state)
    runtime=Path(state['pythonw']);entry=root/'Start-UnifiedTools.pyw'
    if not runtime.is_file() or api.digest(entry.read_bytes())!=state['bootstrap_sha256']:raise ValueError('Existing launcher/runtime must verify first.')
    for path in (runtime,entry):
        if any(c in str(path) for c in '"%!\r\n'):raise ValueError('Launcher path requires supported quoting.')
    if not desktop.is_dir() or recovery.exists():raise ValueError('Use the existing Desktop and a new recovery folder.')
    command=root/(NAME+'.cmd');shortcut=desktop/(NAME+'.lnk');recovery.mkdir(parents=True)
    for index,path in enumerate((command,shortcut)):
        if path.exists():shutil.copy2(path,recovery/(str(index)+'-'+path.name))
    raw=('@echo off\r\nsetlocal DisableDelayedExpansion\r\nstart "" "'+str(runtime)+'" -B "'+str(entry)+'"\r\nexit /b 0\r\n').encode('utf-8')
    api._replace_file(command,raw)
    env=os.environ.copy();env.update(UGT_INTERFACE_LINK=str(shortcut),UGT_INTERFACE_RUNTIME=str(runtime),UGT_INTERFACE_ENTRY=str(entry),UGT_INTERFACE_ROOT=str(root))
    script='$w=New-Object -ComObject WScript.Shell;$s=$w.CreateShortcut($env:UGT_INTERFACE_LINK);$s.TargetPath=$env:UGT_INTERFACE_RUNTIME;$s.Arguments="-B "+[char]34+$env:UGT_INTERFACE_ENTRY+[char]34;$s.WorkingDirectory=$env:UGT_INTERFACE_ROOT;$s.Description="Open Unified Game Tools; choose Existing or New interface";$s.Save();$v=$w.CreateShortcut($env:UGT_INTERFACE_LINK);@{target=$v.TargetPath;arguments=$v.Arguments;working_directory=$v.WorkingDirectory}|ConvertTo-Json -Compress'
    result=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],env=env,capture_output=True,text=True,check=True)
    actual=json.loads(result.stdout)
    if Path(actual['target'])!=runtime or actual['arguments']!='-B "'+str(entry)+'"' or Path(actual['working_directory'])!=root:raise ValueError('Desktop shortcut readback differs.')
    assert command.read_bytes()==raw and shortcut.is_file()
    receipt={'included':str(command),'desktop':str(shortcut),'readback':actual,'legacy_preserved':True,'settings_changed':False,'app_launched':False}
    api.atomic_json(recovery/'RECEIPT.json',receipt);return receipt
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install-root',type=Path,required=True);p.add_argument('--desktop',type=Path,required=True);p.add_argument('--recovery',type=Path,required=True);a=p.parse_args();print(json.dumps(prepare(a.install_root,a.desktop,a.recovery),indent=2))
