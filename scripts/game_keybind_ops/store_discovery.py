"""Read explicitly selected Steam/Epic metadata. It never launches or searches the disk.
Metadata points to candidates; every root still passes path/link checks and native
instance selection. Store manifests are not proof of active keybinding ownership.
"""
from __future__ import annotations
import json,re
from pathlib import Path
from .core import snapshot,sha
from .deps import require,no_links,contained,strict_json
from .documents import Document


def steam_installations(steam_root:Path,app_id:str)->dict:
    require(type(app_id) is str and re.fullmatch(r'\d{1,12}',app_id),'GAME_ID_INVALID','Use one exact Steam AppID.')
    root=no_links(steam_root);libraries=[root];receipts=[];warnings=[]
    manifest=root/'steamapps/libraryfolders.vdf'
    if manifest.exists():
        raw=snapshot(manifest);d=Document(raw,'keyvalues');receipts.append({'file':'libraryfolders.vdf','sha256':sha(raw)})
        for c in d.cells:
            chain=c.selector['kv_path']
            # Exact metadata role only; not arbitrary strings containing paths.
            if len(chain)==3 and chain[0][0].casefold()=='libraryfolders' and str(chain[1][0]).isdigit() and chain[2][0]=='path':
                p=Path(c.value)
                require(p.is_absolute() and not str(p).startswith(('//','\\\\')),'UNSAFE_PATH','Store paths must be local absolute paths.')
                no_links(p)
                if p not in libraries:libraries.append(p)
    require(len(libraries)<=32,'DISCOVERY_LIMIT','Too many libraries; provide one selected library.')
    out=[]
    for lib in libraries:
        path=lib/'steamapps'/('appmanifest_'+app_id+'.acf')
        if not path.exists():continue
        raw=snapshot(path);d=Document(raw,'keyvalues');data={}
        for c in d.cells:
            chain=c.selector['kv_path']
            if len(chain)==2 and chain[0][0]=='AppState':
                require(chain[1][0] not in data,'STORE_AMBIGUOUS','Duplicate store metadata key.');data[chain[1][0]]=c.value
        require(data.get('appid')==app_id and 'installdir' in data,'STORE_MISMATCH','App manifest identity mismatch.')
        folder=contained(lib/'steamapps/common',data['installdir']);prefix=no_links(lib/'steamapps/compatdata'/app_id/'pfx')
        out.append({'store':'steam','app_id':app_id,'build_id':data.get('buildid'),'install_root':str(folder),
                    'exists':folder.is_dir(),'proton_prefix':str(prefix) if prefix.is_dir() else None,
                    'manifest_sha256':sha(raw),'active_config_verified':False})
    return {'candidates':out,'metadata_receipts':receipts,'warnings':warnings,'files_modified':False,'private_paths_included':True}


def epic_installations(manifest_root:Path,app_name:str)->dict:
    require(type(app_name) is str and 0<len(app_name)<=160,'GAME_ID_INVALID','Select an exact Epic AppName.')
    root=no_links(manifest_root);out=[];count=0
    for path in root.iterdir():
        count+=1;require(count<=4096,'DISCOVERY_LIMIT','Manifest directory inspection budget exceeded.')
        if path.suffix.lower()!='.item' or not path.is_file():continue
        data=strict_json(snapshot(no_links(path)));require(type(data) is dict,'STORE_MISMATCH','Expected one Epic manifest object.')
        if data.get('AppName')!=app_name:continue
        install=Path(data.get('InstallLocation',''))
        require(install.is_absolute() and not str(install).startswith(('//','\\\\')),'UNSAFE_PATH','Store root must be local and absolute.');no_links(install)
        out.append({'store':'epic','app_name':app_name,'install_root':str(install),'build_id':data.get('AppVersionString'),
                    'exists':install.is_dir(),'manifest_sha256':sha(snapshot(path)),'active_config_verified':False})
        require(len(out)<=32,'DISCOVERY_LIMIT','Ambiguous store metadata; choose an instance.')
    return {'candidates':out,'files_modified':False,'private_paths_included':True}
