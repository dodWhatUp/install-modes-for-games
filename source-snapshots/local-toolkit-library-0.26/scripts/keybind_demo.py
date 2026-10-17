#!/usr/bin/env python3
"""Synthetic-only demonstration. Creates one NEW directory; never scans real games."""
from pathlib import Path
import argparse,json
from game_keybind_ops.core import Service,sha

def run(root):
    root=Path(root).absolute();root.mkdir(parents=True,exist_ok=False)
    game=root/'SYNTHETIC-NOT-A-GAME';game.mkdir();path=game/'settings.json'
    original=b'{"bindings":{"use":"E","reload":"R","fire":"MouseLeft"},"graphics":{"quality":"ultra"}}\n'
    path.write_bytes(original)
    keys={x:x for x in ('E','F','R','MouseLeft')}
    spec={'schema_version':1,'target_id':'demo','game_id':'synthetic-not-a-game','root':str(game),
          'relative':'settings.json','adapter':'json','inventory_complete':True,
          'stopped_processes':['synthetic-not-a-game.exe'],
          'evidence':'SYNTHETIC example only; not a native game schema.',
          'fields':[{'id':n,'selector':{'pointer':'/bindings/'+n},'keys':keys,'collision_group':'gameplay'} for n in ('use','reload','fire')]}
    (root/'SYNTHETIC.recipe.json').write_text(json.dumps(spec,indent=2))
    service=Service(root/'demo-data');registered=service.register_local(spec)
    items=[{'target_id':'demo','target_revision':registered['target_revision'],'changes':{'use':'F'}}]
    (root/'SYNTHETIC.patch.json').write_text(json.dumps({'items':items},indent=2))
    preview=service.preview(items);plan=service.prepare(items,preview['preview_sha256'],plan_id='demo-apply')
    assert path.read_bytes()==original
    # Authorization is limited to this function-created synthetic target, not game files.
    result=service.apply_local(plan['plan_id'],plan['plan_sha256'],authorize=lambda _:True)
    assert result['status']=='APPLIED_FILES_RUNTIME_UNVERIFIED'
    path.write_bytes(path.read_bytes().replace(b'ultra',b'high'))
    undo=service.rollback_preview(plan['plan_id'],selective=True)
    inverse=service.prepare_rollback(plan['plan_id'],undo['preview_sha256'],selective=True,plan_id='demo-selective-undo')
    undone=service.apply_local(inverse['plan_id'],inverse['plan_sha256'],authorize=lambda _:True)
    assert path.read_bytes()==original.replace(b'ultra',b'high')
    report={'scope':'SYNTHETIC_FIXTURE_ONLY','preview_left_original_unchanged':True,'apply':result['status'],
            'selective_undo':undone['status'],'later_graphics_setting_preserved':True,
            'original_sha256':sha(original),'final_sha256':sha(path.read_bytes()),
            'history':service.history(),'real_games_touched':0,'gameplay_verified':False}
    (root/'DEMO_RESULT.json').write_text(json.dumps(report,indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();print(json.dumps(run(a.output),indent=2))
