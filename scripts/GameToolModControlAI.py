"""Typed additions to the existing local MCP/CLI interface; no model API client."""
from GameToolModControls import OPERATIONS,ini_template,validate_pack
from game_mod_ops.safety import object_hash,require

def tools(allow_requests=False):
    from GameToolAITools import tool_definition
    ident={'type':'string','minLength':1,'maxLength':100}
    revision={'type':'string','pattern':'^[a-f0-9]{64}$'}
    out=[
        tool_definition('mod_controls_games','List shared games, installations and available control-pack coverage.',{}),
        tool_definition('mod_controls_connections','Inspect known RHI/Vortex/MO2/Steam connection availability without paths or launching apps.',{}),
        tool_definition('mod_controls_inspect','Read typed applied settings, bounds, dependencies, file hashes, source provenance and capabilities for one registered installation. No private paths or raw files.',{'instance_id':ident},['instance_id']),
        tool_definition('mod_controls_preview','Preview setting changes using the same validation as the UI, without applying files.',{'instance_id':ident,'changes':{'type':'object'},'revision':revision},['instance_id','changes']),
        tool_definition('mod_controls_profile','Read one opaque saved profile with its game and schema checks.',{'instance_id':ident,'profile_id':ident},['instance_id','profile_id']),
        tool_definition('mod_controls_template','Create a data-only INI control-pack template. Import and connection remain local.',{'game_id':ident},['game_id']),
        tool_definition('mod_controls_validate_pack','Validate typed controls and relative configuration paths; never import code or write a game.',{'pack':{'type':'object'}},['pack']),
        tool_definition('mod_controls_request_status','Read a mod-control action proposal or verified result from the existing approval/journal owner.',{'instance_id':ident,'request_id':ident},['instance_id','request_id']),
    ]
    if allow_requests:
        out.append(tool_definition('mod_controls_propose','Submit a revision-bound mod-control action for local review. No model approval or automatic execution.',{'instance_id':ident,'operation':{'type':'string','enum':sorted(OPERATIONS)},'arguments':{'type':'object'},'request_id':ident},['instance_id','operation','arguments','request_id'],write=True))
    return out

def dispatch(service,name,args):
    require(hasattr(service,'controls'),'CAPABILITY_UNAVAILABLE','Use the shared game-workspace endpoint for mod controls.')
    controls=service.controls
    if name=='mod_controls_games':return controls.games()
    if name=='mod_controls_connections':return controls.tools_public()
    if name=='mod_controls_inspect':return controls.inspect(**args)
    if name=='mod_controls_preview':return controls.preview(**args)
    if name=='mod_controls_profile':return controls.profile(**args)
    if name=='mod_controls_template':return {'pack':ini_template(**args),'imported':False,'game_files_written':False}
    if name=='mod_controls_validate_pack':return {'valid':True,'pack_revision':object_hash(validate_pack(args['pack'])),'imported':False,'game_files_written':False}
    if name=='mod_controls_request_status':return controls.requests(args['instance_id']).request_status(args['request_id'])
    if name=='mod_controls_propose':return controls.requests(args['instance_id']).propose(args['operation'],args['arguments'],request_id=args['request_id'])
    raise ValueError('Unknown mod-control tool.')
