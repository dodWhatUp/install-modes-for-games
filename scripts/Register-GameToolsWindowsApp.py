"""Explicit reviewed Windows access registration; never launches or applies a game."""
import argparse,json,shutil
from pathlib import Path
from GameToolWindowsApp import APPS
from GameToolWindowsShortcut import read,write

def register(spec,recovery):
    key=spec['key'];identity,title,_=APPS[key]
    runtime=Path(spec['runtime']);entry=Path(spec['entry']);cwd=Path(spec['working_directory']);icon=Path(spec['icon'])
    if runtime.name.casefold()!='pythonw.exe' or not runtime.is_file() or entry.suffix not in ('.py','.pyw')or not entry.is_file():
        raise ValueError('Use the verified existing Python window runtime and authored entry')
    arguments=spec['arguments']
    if str(entry)not in arguments or '\n'in arguments or '\r'in arguments:raise ValueError('Expected the reviewed stable entry arguments')
    recovery=Path(recovery);recovery.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for index,location in enumerate(spec['shortcuts']):
        path=Path(location)
        if path.name!=title+' APP LAUNCHER.lnk':raise ValueError('Keep the exact named APP LAUNCHER convention')
        before=read(path)if path.exists()else None
        if before is not None:
            expected=spec['existing'].get(str(path))
            if before!=expected:raise ValueError('A newer shortcut requires reconciliation: '+str(path))
            shutil.copyfile(path,recovery/(str(index)+'.lnk'))
        value=write(path,target=str(runtime),arguments=arguments,working_directory=str(cwd),icon=str(icon),
                    app_id=identity,description='Open or restore '+title+'; game settings require separate reviewed actions.',expected=before)
        receipts.append({'path':str(path),'readback':value})
    (recovery/'SHORTCUTS.json').write_text(json.dumps(receipts,indent=2)+'\n',encoding='utf-8')
    return receipts

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--recovery',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(register(json.loads(args.spec.read_text(encoding='utf-8')),args.recovery),indent=2))
