"""Local authoring commands added to the existing Keybinds CLI."""
from pathlib import Path
import json,sys
from .deps import read_json,require
from . import packs,effective,authoring,pack_transport,store_discovery

COMMANDS={'adapters','pack-check','pack-import','pack-list','pack-scaffold','pack-discover','pack-compare','pack-export','pack-unpack',
          'learn-diff','instance-bind','instances','instance-context','intent-preview','diagnose','store-discover','planner-bridge','preset-preview','registration-status','draft-context'}

def add_arguments(sub):
    sub.add_parser('adapters');sub.add_parser('pack-list')
    p=sub.add_parser('pack-scaffold');p.add_argument('--out',required=True,type=Path);p.add_argument('--game',required=True);p.add_argument('--title',required=True);p.add_argument('--adapter',default='json')
    for cmd in ('pack-check','pack-import','pack-discover','pack-export'):
        p=sub.add_parser(cmd);p.add_argument('--pack',required=True,type=Path)
        if cmd=='pack-import':p.add_argument('--pack-sha',required=True)
        if cmd=='pack-discover':p.add_argument('--roots',required=True,type=Path)
        if cmd=='pack-export':p.add_argument('--out',required=True,type=Path)
    p=sub.add_parser('pack-unpack');p.add_argument('--archive',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--pack-sha',required=True)
    p=sub.add_parser('pack-compare');p.add_argument('--before',required=True,type=Path);p.add_argument('--after',required=True,type=Path)
    p=sub.add_parser('learn-diff');p.add_argument('--before',required=True,type=Path);p.add_argument('--after',required=True,type=Path);p.add_argument('--adapter',required=True);p.add_argument('--include-values',action='store_true');p.add_argument('--encoding')
    p=sub.add_parser('instance-bind');p.add_argument('--request',required=True,type=Path)
    p=sub.add_parser('instances');p.add_argument('--game');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=50)
    p=sub.add_parser('instance-context');p.add_argument('--instance',required=True);p.add_argument('--known-revision');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=100)
    p=sub.add_parser('intent-preview');p.add_argument('--instance',required=True);p.add_argument('--revision',required=True);p.add_argument('--intent',required=True,type=Path);p.add_argument('--allow-partial',action='store_true')
    p=sub.add_parser('preset-preview');p.add_argument('--instance',required=True);p.add_argument('--preset',required=True);p.add_argument('--revision',required=True)
    p=sub.add_parser('registration-status');p.add_argument('--instance',required=True)
    p=sub.add_parser('draft-context');p.add_argument('--draft',required=True);p.add_argument('--section',default='overview');p.add_argument('--file-id');p.add_argument('--offset',type=int,default=0);p.add_argument('--limit',type=int,default=50)
    p=sub.add_parser('diagnose');p.add_argument('--code',required=True)
    p=sub.add_parser('store-discover');p.add_argument('--store',choices=['steam','epic'],required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--app',required=True)
    p=sub.add_parser('planner-bridge');p.add_argument('--variant',type=Path,required=True);p.add_argument('--crosswalk',type=Path,required=True)

def _approve(record):
    require(sys.stdin.isatty(),'INTERACTIVE_APPROVAL_REQUIRED','Use a local interactive terminal or the shared host approval UI.')
    digest=record.get('pack_sha256',record.get('revision'));print(json.dumps(record,indent=2))
    return input('Type the FULL displayed review digest to confirm this local registration: ').strip()==digest

def dispatch(service,a):
    c=a.command
    if c=='adapters':return {'adapters':packs.capabilities(),'loaded_adapters_are_not_game_certification':True}
    if c=='pack-scaffold':return authoring.scaffold(a.out,a.game,a.title,a.adapter)
    if c=='pack-check':return packs.inspect_pack(a.pack)
    if c=='pack-import':return packs.import_pack_local(service,a.pack,a.pack_sha,authorize=_approve)
    if c=='pack-list':return {'packs':packs.list_packs(service)}
    if c=='pack-discover':return packs.discover_pack(read_json(a.pack/'pack.json',4*1024*1024),{k:Path(v) for k,v in read_json(a.roots).items()})
    if c=='pack-compare':return packs.compare_packs(read_json(a.before/'pack.json',4*1024*1024),read_json(a.after/'pack.json',4*1024*1024))
    if c=='pack-export':return pack_transport.export_pack_local(a.pack,a.out)
    if c=='pack-unpack':return pack_transport.unpack_pack_local(a.archive,a.out,a.pack_sha)
    if c=='learn-diff':return authoring.learn_difference(a.before,a.after,a.adapter,encoding=a.encoding,include_values=a.include_values)
    if c=='instance-bind':
        r=read_json(a.request);require(set(r)=={'pin','instance_id','variant_id','bindings','expected_files','evidence'},'INSTANCE_FILES','Unexpected instance registration fields.')
        return packs.bind_instance_local(service,**r,authorize=_approve)
    if c=='instances':return effective.list_instances(service,a.offset,a.limit,a.game)
    if c=='instance-context':return effective.inspect_instance(service,a.instance,a.known_revision,a.offset,a.limit)
    if c=='intent-preview':return effective.intent_preview(service,a.instance,read_json(a.intent)['changes'],a.revision,allow_partial=a.allow_partial)
    if c=='preset-preview':return effective.preset_preview(service,a.instance,a.preset,a.revision)
    if c=='registration-status':return packs.registration_status(service,a.instance)
    if c=='draft-context':return authoring.draft_context(service,a.draft,a.section,a.file_id,a.offset,a.limit)
    if c=='diagnose':return authoring.troubleshoot(a.code)
    if c=='store-discover':return store_discovery.steam_installations(a.root,a.app) if a.store=='steam' else store_discovery.epic_installations(a.root,a.app)
    if c=='planner-bridge':return authoring.planner_bridge(read_json(a.variant),read_json(a.crosswalk)['rows'])
    raise ValueError('Unknown pack command')
