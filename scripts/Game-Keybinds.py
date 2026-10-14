#!/usr/bin/env python3
"""Local operator CLI for Game Tools Keybinds. No network or game launches.

Python 3.10+. Always use the SAME host data root. Mutation needs the exact staged
plan and a local interactive confirmation; the AI-facing adapter has no approve
or register tools. GUI and CLI share this service and its original-file ledger.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import sys
from game_keybind_ops.core import Service
from game_keybind_ops.deps import Error,read_json,require
from game_keybind_ops.discovery import catalog,discover_local,windows_roots
from game_keybind_ops.planner import cached_extract
from game_keybind_ops.documents import Document
from game_keybind_ops.core import snapshot


def default_data():
    return Path(os.environ.get('LOCALAPPDATA',str(Path.home()/'.local/share')))/'GameToolHub'

def confirm_local(plan):
    require(sys.stdin.isatty(),'INTERACTIVE_APPROVAL_REQUIRED','Local terminal/GUI approval is required; piped approval is not accepted.')
    print(json.dumps(plan,ensure_ascii=False,indent=2))
    print('Close the game and the launcher/cloud clients named by the reviewed recipe.')
    print('This changes only the listed config files. Original-byte backups are already staged.')
    typed=input('Type the FULL plan SHA-256 above to approve this exact operation: ').strip()
    return typed==plan['plan_sha256']

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-dir',type=Path,default=default_data())
    subs=p.add_subparsers(dest='command',required=True)
    lk=subs.add_parser('lock-inspect');lk.add_argument('--kind',choices=['operations','registration'],default='operations')
    lr=subs.add_parser('lock-retire');lr.add_argument('--inspection-sha',required=True);lr.add_argument('--kind',choices=['operations','registration'],default='operations')
    subs.add_parser('catalog');subs.add_parser('context');subs.add_parser('history');subs.add_parser('gui')
    d=subs.add_parser('discover');d.add_argument('--game',required=True);d.add_argument('--roots',type=Path)
    r=subs.add_parser('register');r.add_argument('--spec',type=Path,required=True)
    r=subs.add_parser('inspect');r.add_argument('--target',required=True)
    for name in ('preview','stage'):
        r=subs.add_parser(name);r.add_argument('--patch',type=Path,required=True)
        if name=='stage':r.add_argument('--preview-sha',required=True);r.add_argument('--plan-id')
    r=subs.add_parser('replacement-preview');r.add_argument('--target',required=True);r.add_argument('--file',type=Path,required=True)
    for name in ('status','reconcile','apply','undo-preview','stage-undo'):
        r=subs.add_parser(name);r.add_argument('--plan',required=True)
        if name=='apply':r.add_argument('--plan-sha',required=True)
        if name in ('undo-preview','stage-undo'):r.add_argument('--selective',action='store_true')
        if name=='stage-undo':r.add_argument('--preview-sha',required=True);r.add_argument('--plan-id')
    r=subs.add_parser('planner');r.add_argument('--source',type=Path,required=True);r.add_argument('--game');r.add_argument('--variant')
    r=subs.add_parser('inventory');r.add_argument('--file',type=Path,required=True);r.add_argument('--adapter',required=True)
    r.add_argument('--include-values',action='store_true');r.add_argument('--offset',type=int,default=0);r.add_argument('--limit',type=int,default=40)
    from game_keybind_ops.pack_cli import add_arguments,dispatch,COMMANDS
    add_arguments(subs)
    a=p.parse_args(argv)
    try:
        s=Service(a.data_dir);c=a.command
        if c in COMMANDS:result=dispatch(s,a)
        elif c=='lock-inspect':
            from game_keybind_ops.recovery import inspect_lock
            result=inspect_lock(s,lock_kind=a.kind)
        elif c=='lock-retire':
            from game_keybind_ops.recovery import retire_lock_local
            def approve(i):
                require(sys.stdin.isatty(),'INTERACTIVE_APPROVAL_REQUIRED','Local terminal approval required.')
                print(json.dumps(i,indent=2));return input('Archive this VERIFIED DEAD lock only? Type its full inspection SHA: ').strip()==i['inspection_sha256']
            result=retire_lock_local(s,a.inspection_sha,authorize=approve,lock_kind=a.kind)
        elif c=='catalog':result=catalog()
        elif c=='gui':
            from game_keybind_ops.panel import main as gui
            gui(a.data_dir);return 0
        elif c=='context':result=s.context()
        elif c=='history':result=s.history()
        elif c=='discover':
            roots={k:Path(v) for k,v in read_json(a.roots).items()} if a.roots else windows_roots()[0]
            result=discover_local(a.game,roots)
        elif c=='register':result=s.register_local(read_json(a.spec))
        elif c=='inspect':result=s.inspect_target(a.target)
        elif c=='preview':result=s.preview(read_json(a.patch)['items'])
        elif c=='stage':result=s.prepare(read_json(a.patch)['items'],a.preview_sha,plan_id=a.plan_id)
        elif c=='replacement-preview':result=s.replacement_preview_local(a.target,a.file)
        elif c=='status':result=s.status(a.plan)
        elif c=='reconcile':result=s.reconcile(a.plan)
        elif c=='apply':result=s.apply_local(a.plan,a.plan_sha,authorize=confirm_local)
        elif c=='undo-preview':result=s.rollback_preview(a.plan,selective=True) if a.selective else s.exact_rollback_preview(a.plan)
        elif c=='stage-undo':result=s.prepare_rollback(a.plan,a.preview_sha,selective=a.selective,plan_id=a.plan_id)
        elif c=='planner':
            result=cached_extract(a.source,a.data_dir)
            if a.game or a.variant:
                result={'source_sha256':result['source_sha256'],'cache_hit':result['cache_hit'],
                        'variants':[v for v in result['variants'] if (not a.game or v['game']==a.game) and (not a.variant or v['variant_id']==a.variant)]}
            else:
                result={k:v for k,v in result.items() if k not in {'variants','source_policy','pending_or_source_corrections'}}
        else:
            require(a.offset>=0 and 0<a.limit<=100,'INVALID_ARGUMENTS','Use a nonnegative offset and limit 1–100.')
            d=Document(snapshot(a.file),a.adapter)
            rows=[]
            for cell in d.cells[a.offset:a.offset+a.limit]:
                row={'selector':cell.selector,'value_type':type(cell.value).__name__}
                if a.include_values:row['native_value']=cell.value
                rows.append(row)
            result={'status':'LOCAL_INSPECTION_NOT_REVIEWED_RECIPE','total_scalars':len(d.cells),'offset':a.offset,
                    'next_offset':a.offset+len(rows) if a.offset+len(rows)<len(d.cells) else None,'rows':rows,
                    'notice':'Values and selectors can contain private settings; inspect locally before sharing. No action IDs were inferred.'}
        print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False));return 0
    except (Error,OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({'status':getattr(e,'code','LOCAL_OPERATION_REFUSED'),'message':str(e) if isinstance(e,Error) else 'Local read/write failed; inspect the same operation before retrying.'},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
