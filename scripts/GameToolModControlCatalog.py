"""Public module presentation and shared, advisory resource/dependency context."""
from copy import deepcopy
from pathlib import PurePosixPath
from urllib.parse import urlsplit
from game_mod_ops.safety import require,slug

LAYERS={'game-mods','graphics-tools'}
MECHANISMS={'content','configuration','engine-plugin','loader','graphics-injector','external-manager'}

def public_url(value):
    if type(value) is not str:return False
    try:p=urlsplit(value)
    except ValueError:return False
    return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password and len(value)<=1000

def validate_catalog(modules,fields):
    require(type(modules) is list and len(modules)<=32,'CONTROL_CATALOG','At most 32 module rows are supported.')
    ids=set();known={f['id']:f for f in fields}
    for m in modules:
        require(type(m) is dict and {'id','name','layer','mechanism','settings'}<=set(m),'CONTROL_CATALOG','A module needs identity, layer, mechanism and settings.')
        slug(m['id']);require(m['id'] not in ids,'CONTROL_CATALOG','Duplicate module ID.');ids.add(m['id'])
        require(m['layer'] in LAYERS and m['mechanism'] in MECHANISMS,'CONTROL_CATALOG','Choose a supported module layer and mechanism.')
        require(type(m['name']) is str and 0<len(m['name'])<=100,'CONTROL_CATALOG','Use a short module name.')
        require(type(m['settings']) is list and len(m['settings'])<=32 and all(type(k) is str for k in m['settings']) and set(m['settings'])<=known.keys(),'CONTROL_CATALOG','Module settings must reference existing typed fields.')
        enabled=m.get('enabled_field')
        require(enabled is None or type(enabled) is str and enabled in known and known[enabled]['type']=='bool','CONTROL_CATALOG','The row switch must reference a boolean field.')
        key=m.get('hotkey_field')
        require(key is None or type(key) is str and key in known and known[key]['type']=='enum','CONTROL_CATALOG','A configured hotkey must reference a typed enum field.')
        for key in ('github','nexus'):
            require(m.get(key) is None or type(m[key]) is str and public_url(m[key]),'CONTROL_CATALOG','Use public HTTPS source pages.')
            if m.get(key):
                hosts={'github.com','www.github.com'} if key=='github' else {'nexusmods.com','www.nexusmods.com','next.nexusmods.com'}
                require(urlsplit(m[key]).hostname in hosts,'CONTROL_CATALOG','A labeled source button must match its GitHub or Nexus service.')
        require(type(m.get('description','')) is str and len(m.get('description',''))<=2000,'CONTROL_CATALOG','Description is too long.')
        require(type(m.get('requires',[])) is list and len(m.get('requires',[]))<=16 and all(type(k) is str for k in m.get('requires',[])),'CONTROL_CATALOG','Use bounded module dependency IDs.')
        require(type(m.get('claims',[])) is list and len(m.get('claims',[]))<=32,'CONTROL_CATALOG','Too many resource claims.')
        for claim in m.get('claims',[]):
            require(type(claim) is str and len(claim)<=240 and ':' in claim and '\\' not in claim,'CONTROL_CATALOG','Use short relative resource IDs.')
            kind,target=claim.split(':',1)
            require(kind in {'file','proxy','setting','feature','hotkey'} and target and ':' not in target and not target.startswith('/') and '..' not in PurePosixPath(target.split('#')[0]).parts,'CONTROL_CATALOG','A resource claim cannot contain an absolute or escaping path.')
        images=m.get('images',[])
        require(type(images) is list and len(images)<=12,'CONTROL_CATALOG','At most 12 verified image references per module.')
        for image in images:
            require(type(image) is dict and {'file','url','caption','credit'}<=set(image),'CONTROL_CATALOG','An image needs file, URL, caption and credit.')
            require(type(image['file']) is str,'CONTROL_CATALOG','Image cache paths must be relative text.')
            path=PurePosixPath(image['file'])
            require(not path.is_absolute() and '..' not in path.parts and '\\' not in image['file'] and ':' not in image['file'],'CONTROL_CATALOG','Image cache paths must be relative.')
            require(public_url(image['url']) and all(type(image[k]) is str and len(image[k])<=500 for k in ('caption','credit')),'CONTROL_CATALOG','Use a bounded caption and public image source.')
    for m in modules:require(set(m.get('requires',[]))<=ids,'CONTROL_CATALOG','A dependency must reference a module in this catalog.')
    return deepcopy(modules)

def coordinate(modules,values,*,draft=False):
    active={m['id'] for m in modules if m.get('enabled_field') and values.get(m['enabled_field']) is True}
    owners={};issues=[]
    for m in modules:
        if m['id'] not in active:continue
        for dependency in m.get('requires',[]):
            if dependency not in active:issues.append({'code':'DEPENDENCY_OFF','module':m['id'],'requires':dependency})
        claims=list(m.get('claims',[]));hotkey=values.get(m.get('hotkey_field'))
        if hotkey and str(hotkey).casefold()!='none':claims.append('hotkey:'+str(hotkey))
        for claim in claims:owners.setdefault(claim.casefold(),[]).append(m['id'])
    for resource,claimants in owners.items():
        if len(set(claimants))>1:issues.append({'code':'RESOURCE_COLLISION','resource':resource,'owners':sorted(set(claimants))})
    return {'scope':'draft' if draft else 'applied-files','modules':len(modules),'active_modules':sorted(active),
        'layers':{layer:[m['id'] for m in modules if m['layer']==layer] for layer in sorted(LAYERS)},
        'resource_owners':owners,'issues':issues,'blocked':bool(issues),
        'compatibility':'CONFLICT' if issues else 'DECLARED_RESOURCES_CLEAR_RUNTIME_UNVERIFIED',
        'communication':'Shared installation, revisions, typed drafts, resource ownership and dependency checks. No automatic cross-owner apply.',
        'runtime_verified':False}
