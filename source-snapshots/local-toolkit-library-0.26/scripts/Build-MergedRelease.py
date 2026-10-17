"""Build the reviewed local merger source inventory; no installation or publication."""
import argparse,datetime,hashlib,json,zipfile
from pathlib import Path

def build(root,output):
    if output.exists():raise ValueError('Use a new immutable archive destination.')
    manifest=json.loads((root/'MANIFEST.json').read_text(encoding='utf-8-sig'))
    files=sorted(p for p in root.rglob('*') if p.is_file() and p!=root/'MANIFEST.json'
                 and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.zip','.log','.exe','.dll'))
    rows=[dict(path=p.relative_to(root).as_posix(),bytes=p.stat().st_size,
               sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files]
    if len(rows)>512:raise ValueError('Merged inventory exceeds its fixed 512-file bound.')
    manifest['files']=rows
    manifest['component_versions'].update(tool_hub='0.25.0-preview.1',workbench='0.3.0',
        game_workspaces='0.3.0',ai_transport='0.3.0',ai='0.3.0',keybinds='0.2.0-preview.1',merger='0.1.0')
    manifest['archive_name']=output.name
    manifest['client_date']='2026-10-14'
    manifest['created_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest['source_basis']={'INPUT_A_0.24_sha256':'12f8198536dd9ae442cfa993c71d185e7e727fef813753951cd73aeee5d237a9',
        'INPUT_B_0.2_sha256':'439eae9bea536861da988de8aaa8eebf45f8418e1e3a4ee651dc498d747c870a',
        'owner':'dodWhatUp/install-modes-for-games','role':'locally_merged_source_no_git_publication'}
    manifest['runtime_status']={'installation':'separate_current_receipt_required',
        'live_ai_client':'not_tested','native_game_keybinds':'not_certified','gameplay':'not_tested'}
    (root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.write(root/'MANIFEST.json','MANIFEST.json')
        for row in rows:z.write(root/row['path'],row['path'])
    from GameToolUnified import inspect_archive
    sha=hashlib.sha256(output.read_bytes()).hexdigest()
    checked=inspect_archive(output,sha)
    return {'archive':str(output),'sha256':sha,'payloads':len(checked['payloads'])}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();print(json.dumps(build(Path(__file__).resolve().parents[1],args.output),indent=2))
