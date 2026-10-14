"""Reusable archive/installed-state adapters. Inspection is not runtime acceptance.

No DLL loading, process launch, security change, loader injection or manager DB
mutation. Managers with virtual filesystems retain ownership through handoff.
"""
from __future__ import annotations
import copy
import hashlib
import os
import zipfile
from pathlib import Path, PurePosixPath
from .archive import inspect_zip
from .definitions import validate_definition, archive_contract
from .safety import (ModError, require, regular, no_links, contained, digest,
                     read_json, strict_json, slug, safe_relative, object_hash)

ADAPTER_API_VERSION=1
MAX_ENTRIES=4000
MAX_METADATA_BYTES=256*1024


def capabilities(definition=None, manager_id='manual'):
    adapter=definition['adapter'] if definition else ('umm' if manager_id=='unity-mod-manager' else 'external')
    return {'adapter_api_version':ADAPTER_API_VERSION,'adapter':adapter,
        'plan':True,'download':True,'import_archive':True,'stage':True,
        'folder_identification':definition is not None,
        'mod_inventory':definition is not None and adapter!='external',
        'manifest_identity':adapter in {'umm','smapi'},
        'manager_handoff':True,'install_new':False,'upgrade':False,'enable_disable':False,
        'runtime_verification':False,'loads_third_party_code':False,
        'boundary':'Legacy Kingmaker install/rollback remains separate; no general manager writes.'}


def _version(value):
    require(type(value) is str and 0<len(value)<=80 and not any(ord(c)<32 for c in value),
            'INVALID_MOD_INFO','Manifest version is missing or invalid.')
    return value


def _manifest(info, adapter):
    require(type(info) is dict,'INVALID_MOD_INFO','Mod metadata must be an object.')
    key='Id' if adapter=='umm' else 'UniqueID'
    ident=slug(info.get(key,'')); version=_version(info.get('Version'))
    if adapter=='umm':
        assembly=info.get('AssemblyName',ident+'.dll');safe_relative(assembly)
        deps=info.get('Requirements') or []
        require(type(deps) is list and len(deps)<=100 and all(type(v) is str for v in deps),
                'DEPENDENCY_UNKNOWN','Unsupported UMM requirements.')
        required=list(deps)
    else:
        assembly=info.get('EntryDll');content=info.get('ContentPackFor')
        require(bool(assembly) != bool(content),'INVALID_MOD_INFO','SMAPI needs either EntryDll or ContentPackFor.')
        if assembly: safe_relative(assembly)
        if content:
            require(type(content) is dict,'INVALID_MOD_INFO','ContentPackFor must be an object.')
            slug(content.get('UniqueID',''))
        deps=info.get('Dependencies') or []
        require(type(deps) is list and len(deps)<=100,'DEPENDENCY_UNKNOWN','Unsupported SMAPI dependencies.')
        required=[]
        for d in deps:
            require(type(d) is dict,'DEPENDENCY_UNKNOWN','SMAPI dependency must be an object.')
            depid=slug(d.get('UniqueID',''))
            require(type(d.get('IsRequired',True)) is bool,'DEPENDENCY_UNKNOWN','Invalid dependency requirement.')
            if d.get('IsRequired',True):required.append(depid)
        if content:required.append(content['UniqueID'])
    return ident,version,assembly,required


def inspect_archive(path,item,operation_plan):
    d=operation_plan.get('game_definition')
    c=archive_contract(item,operation_plan['manager_id'],d)
    if c['layout']=='umm':
        result=inspect_zip(path,c['expected_id'],item['kind']=='manager','umm')
    else:
        result=inspect_zip(path,layout='generic')
        if c['layout']=='smapi' and item['kind']!='manager':
            paths=result['files']; matches=[p for p in paths if PurePosixPath(p).name.casefold()=='manifest.json']
            require(len(matches)==1,'ARCHIVE_LAYOUT','Expected one SMAPI manifest; split multi-mod bundles for explicit review.')
            marker=matches[0]
            require(paths[marker]['bytes']<=MAX_METADATA_BYTES,'ZIP_LIMIT','Manifest exceeds its limit.')
            with zipfile.ZipFile(path) as z: info=strict_json(z.read(marker))
            ident,version,assembly,deps=_manifest(info,'smapi')
            require(not c['expected_id'] or c['expected_id']==ident,'MOD_ID_MISMATCH','The SMAPI UniqueID differs from the recipe.')
            parent=str(PurePosixPath(marker).parent);prefix='' if parent=='.' else parent+'/'
            keep={p[len(prefix):]:v for p,v in paths.items() if p.startswith(prefix)}
            omitted=[p for p in paths if not p.startswith(prefix)]
            require(all(PurePosixPath(p).suffix.casefold() in {'.md','.txt','.png','.jpg'} or
                        PurePosixPath(p).name.upper() in {'LICENSE','COPYING'} for p in omitted),
                    'ARCHIVE_LAYOUT','Unexpected payload outside the SMAPI folder.')
            if assembly:require(assembly.casefold() in {p.casefold() for p in keep},'ASSEMBLY_MISSING','SMAPI EntryDll is missing.')
            result.update(kind='smapi_mod',mod_id=ident,version=version,prefix=prefix,files=keep,
                          omitted_documentation=omitted,requirements=deps,
                          info={k:info[k] for k in ('UniqueID','Version','EntryDll','ContentPackFor','Dependencies','MinimumApiVersion') if k in info})
        elif c['root']:
            prefix=c['root'].rstrip('/')+'/'
            kept={p[len(prefix):]:v for p,v in result['files'].items() if p.startswith(prefix)}
            require(bool(kept),'ARCHIVE_LAYOUT','The declared archive_root does not contain any files.')
            result.update(prefix=prefix,files=kept,
                          omitted_documentation=[],
                          excluded_by_explicit_root=[p for p in result['files'] if not p.startswith(prefix)],
                          root_selection='explicit_recipe_path_not_auto_detection')
    for rel in c['required_files']:
        require(rel.casefold() in {p.casefold() for p in result['files']},'REQUIRED_FILE_MISSING','A declared payload file is missing.')
    require(digest(path)==result['archive_sha256'],'SOURCE_CHANGED','Archive changed while inspecting metadata.')
    result['identity_evidence']='archive_manifest' if result['kind'] in {'umm_mod','smapi_mod'} else 'hash_and_paths_only'
    return result


def _walk(root,depth):
    """Count directories too. Never scan outside the selected mod subtree."""
    queue=[(root,0)]; count=0
    while queue:
        folder,level=queue.pop()
        with os.scandir(no_links(folder)) as entries:
            children=[]
            for entry in entries:
                require(len(children)+count<MAX_ENTRIES,'INVENTORY_LIMIT','Too many entries; narrow the support definition.')
                children.append(entry)
            children.sort(key=lambda e:e.name.casefold())
        for entry in children:
            count+=1;p=no_links(Path(entry.path));rel=p.relative_to(root).as_posix();safe_relative(rel)
            if p.is_dir():
                if level+1<depth:queue.append((p,level+1))
                else:yield p,rel,'depth_limit'
            elif p.is_file():yield p,rel,'file'
            else:raise ModError('SPECIAL_FILE','Special files are not inspected.')


def inspect_game(game_dir,definition):
    d=validate_definition(definition);root=no_links(Path(game_dir))
    require(root.is_dir(),'GAME_MISSING','Choose the exact game directory.')
    markers=[]
    for relative in d['executable_any']:
        p=contained(root,relative)
        if p.is_file():markers.append({'relative':relative,'bytes':p.stat().st_size})
    require(bool(markers),'GAME_MISMATCH','None of this support pack’s executable markers exists in the selected folder.')
    loaders=[{'relative':r,'present':contained(root,r).is_file()} for r in d['loader_markers']]
    result={'schema_version':1,'game_id':d['game_id'],'adapter':d['adapter'],
        'definition_sha256':object_hash(d),'evidence':'filesystem_metadata_not_runtime',
        'game_markers':markers,'loader_markers':loaders,'mods':[], 'warnings':[],
        'runtime':'NOT_VERIFIED','enabled_state':'UNKNOWN','complete':True}
    if d['adapter']=='external':
        result.update(complete=False,inventory_status='MANAGER_HANDOFF_REQUIRED')
        result['warnings'].append('Virtual deployment/load order belongs to the external manager. Game-folder files cannot prove its active profile.')
        return result
    mods=contained(root,d['mods_relative'])
    if not mods.exists():result['inventory_status']='MOD_DIRECTORY_ABSENT';return result
    require(mods.is_dir(),'GAME_MISMATCH','The declared mod directory is not a directory.')
    listing=list(_walk(mods,d['scan_depth']));seen={};metadata_count=0
    before=[(rel,kind,p.stat().st_size,p.stat().st_mtime_ns) for p,rel,kind in listing]
    for p,rel,kind in listing:
        if kind=='depth_limit':
            result['complete']=False;result['warnings'].append('Scan depth reached: '+rel);continue
        adapter=d['adapter'];base=p.name.casefold()
        metadata=(base=='info.json' if adapter=='umm' else base=='manifest.json' if adapter=='smapi' else False)
        if metadata:
            metadata_count+=1
            try:
                info=read_json(p,MAX_METADATA_BYTES);ident,version,assembly,deps=_manifest(info,adapter)
                folder=PurePosixPath(rel).parent.as_posix()
                ready=not assembly or contained(p.parent,assembly).is_file()
                row={'id':ident,'version':version,'folder':folder,'manifest_sha256':digest(p),
                     'payload_marker_present':ready,'identity_evidence':'manifest_declared',
                     'required_ids':deps,'enabled':'UNKNOWN',
                     'ignored_by_folder_convention':adapter=='smapi' and any(v.startswith('.') for v in PurePosixPath(rel).parts[:-1])}
                if ident.casefold() in seen:
                    result['complete']=False;result['warnings'].append('Duplicate manifest identity: '+ident)
                seen[ident.casefold()]=True
                result['mods'].append(row)
                if not ready:result['complete']=False;result['warnings'].append('Declared mod assembly missing: '+folder)
            except (ModError,OSError,ValueError) as e:
                result['complete']=False
                result['warnings'].append('Unreadable/unsupported manifest: '+rel)
        elif adapter in {'bepinex','directory'} and (p.suffix.casefold()=='.dll' or adapter=='directory'):
            result['mods'].append({'id':None,'version':None,'relative_file':rel,'bytes':p.stat().st_size,
                                  'identity_evidence':'file_name_only','enabled':'UNKNOWN'})
    if d['adapter'] in {'umm','smapi'}:
        # Unrecognized folders/files cannot prove that a dependency is absent.
        known=[str(PurePosixPath(r['folder'])) for r in result['mods']]
        unknown=[rel for _,rel,kind in listing if kind=='file' and
                 not any(folder=='.' or rel.startswith(folder+'/') for folder in known)]
        if unknown:
            result['complete']=False;result['warnings'].append('Unrecognized mod content; absence conclusions are inconclusive.')
        result['unrecognized_files']=unknown[:32]
        result['unrecognized_file_count']=len(unknown)
    result['inventory_status']='INVENTORY_OBSERVED' if result['complete'] else 'PARTIAL_INVENTORY'
    # A changing mod directory invalidates this read; do not present it as a snapshot.
    after=[(rel,kind,p.stat().st_size,p.stat().st_mtime_ns) for p,rel,kind in _walk(mods,d['scan_depth'])]
    require(after==before,'SOURCE_CHANGED','Mod content changed during inspection; no stable snapshot was returned.')
    # Store no absolute/private directory in public results.
    result['observed_file_set_sha256']=object_hash(after)
    return result


def compare_installed(operation_plan,observed):
    require(observed.get('game_id')==operation_plan['game_id'],'GAME_MISMATCH','Inventory belongs to another game.')
    complete=observed.get('complete') is True
    matches={}
    for r in observed.get('mods',[]):
        if r.get('id'):matches.setdefault(r['id'].casefold(),[]).append(r)
    rows=[]
    for item in operation_plan['items']:
        if item['kind']!='mod':continue
        ident=item.get('mod_id') or item.get('umm_id');found=matches.get(ident.casefold(),[]) if ident else []
        if not ident:state='IDENTITY_NOT_CONFIGURED'
        elif len(found)>1:state='AMBIGUOUS_DUPLICATE'
        elif not found:state='NOT_OBSERVED' if complete else 'INCONCLUSIVE'
        elif found[0].get('ignored_by_folder_convention'):state='IGNORED_FOLDER_PRESENT'
        elif found[0].get('payload_marker_present') is False:state='PAYLOAD_MARKER_MISSING'
        else:
            wanted=item.get('expected_version')
            state='VERSION_MATCH' if wanted and found[0]['version']==wanted else 'VERSION_DIFFERS' if wanted else 'IDENTITY_PRESENT'
        rows.append({'item_id':item['id'],'mod_id':ident,'state':state,
                     'observed_version':found[0]['version'] if len(found)==1 else None,
                     'runtime':'NOT_VERIFIED'})
    return {'game_id':operation_plan['game_id'],'items':rows,'compares':'plan_vs_observed_manifest_not_runtime',
            'complete_inventory':complete,'writes_game_files':False}
