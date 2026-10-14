"""Authoring/AI CLI for game support packs. Human actions are in the Workbench."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from game_mod_ops.support import SupportRegistry,read_pack,scaffold,describe,schema
from game_mod_ops.safety import ModError,json_new
from game_mod_ops.managers import inspect_game
from game_mod_ops.workflow import Job, default_data
from game_mod_ops.handoff import export_handoff

def main(argv=None):
 p=argparse.ArgumentParser(description='Game support data: no code loading or automatic installation.')
 p.add_argument('--data-dir',type=Path,default=default_data().parent)
 sub=p.add_subparsers(dest='action',required=True)
 sub.add_parser('schema');sub.add_parser('list')
 q=sub.add_parser('validate');q.add_argument('--pack',type=Path,required=True)
 q=sub.add_parser('scaffold');q.add_argument('--game-id',required=True);q.add_argument('--name',required=True)
 q.add_argument('--adapter',choices=['umm','smapi','bepinex','directory','external'],default='directory')
 q.add_argument('--executable',default='Game.exe');q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('import');q.add_argument('--pack',type=Path,required=True);q.add_argument('--reviewed-sha256',required=True)
 q.add_argument('--expected-revision');q.add_argument('--expected-recipe-revision');q.add_argument('--confirm',action='store_true')
 q=sub.add_parser('export');q.add_argument('--game-id',required=True);q.add_argument('--output',type=Path,required=True)
 q=sub.add_parser('inspect');q.add_argument('--game-id',required=True);q.add_argument('--game-dir',type=Path,required=True)
 q=sub.add_parser('handoff');q.add_argument('--job',type=Path,required=True);q.add_argument('--output',type=Path,required=True)
 q.add_argument('--reviewed-revision',required=True);q.add_argument('--confirm',action='store_true')
 a=p.parse_args(argv);r=SupportRegistry(a.data_dir)
 try:
  if a.action=='schema':result=schema()
  elif a.action=='list':result={'packs':[describe(row['pack']) for row in r.rows().values()]}
  elif a.action=='validate':result=r.review(read_pack(a.pack)[0])
  elif a.action=='scaffold':
   pack=scaffold(a.game_id,a.name,a.adapter,a.executable);json_new(a.output,pack);result=describe(pack)
  elif a.action=='import':
   from GameToolGameWorkspaces import RecipeCatalog
   result=RecipeCatalog(a.data_dir).import_support(a.pack,reviewed_sha256=a.reviewed_sha256,
       expected_revision=a.expected_revision,expected_recipe_revision=a.expected_recipe_revision,confirmed=a.confirm)
  elif a.action=='export':result=r.export(a.game_id,a.output)
  elif a.action=='inspect':result=inspect_game(a.game_dir,r.get(a.game_id)['pack']['definition'])
  elif a.action=='handoff':result=export_handoff(Job(a.job),a.output,reviewed_revision=a.reviewed_revision,confirmed=a.confirm)
  print(json.dumps(result,indent=2,ensure_ascii=False));return 0
 except ModError as e:print(json.dumps(e.record()));return 2
 except (ValueError,OSError,TypeError,KeyError):print(json.dumps({'status':'INVALID_OR_INCOMPLETE','message':'Inspect the selected source and existing output before retrying.'}));return 3
if __name__=='__main__':raise SystemExit(main())
