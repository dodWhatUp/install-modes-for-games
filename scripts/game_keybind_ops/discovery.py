"""Bounded metadata discovery. A found file is a candidate, not proof of active ownership."""
from __future__ import annotations
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import re
from .deps import require, no_links, read_json, Error, object_hash
from .core import snapshot

CATALOG = Path(__file__).absolute().parents[2]/'examples/keybinds/game-locations.json'
MAX_ENTRIES=4096
MAX_CANDIDATES=64

def walk_pattern(root:Path,pattern:str) -> list[Path]:
    require(type(pattern) is str and 0<len(pattern)<=300 and not pattern.startswith('/')
            and '\\' not in pattern and '**' not in pattern,'UNSAFE_PATTERN','Only bounded relative component patterns are accepted.')
    parts=pattern.split('/')
    require(len(parts)<=12 and all(x not in {'','.','..'} and ':' not in x for x in parts),'UNSAFE_PATTERN','Unsafe pattern.')
    root=no_links(root);candidates=[root];visited=0
    for part in parts:
        result=[]
        for parent in candidates:
            if not parent.is_dir():continue
            for entry in parent.iterdir():
                visited+=1;require(visited<=MAX_ENTRIES,'DISCOVERY_LIMIT','Directory inspection budget reached; narrow the roots.')
                if not fnmatch.fnmatchcase(entry.name.casefold(),part.casefold()):continue
                no_links(entry);result.append(entry)
                require(len(result)<=MAX_CANDIDATES,'DISCOVERY_LIMIT','Too many candidates; select a narrower root.')
        candidates=result
    return sorted(candidates,key=lambda p:str(p).casefold())

def catalog() -> dict:
    return read_json(CATALOG,256*1024)

def discover_local(game_id:str,roots:dict[str,Path]) -> dict:
    require(type(roots) is dict and len(roots)<=12,'ROOTS_INVALID','Use at most 12 explicitly resolved root aliases.')
    games=catalog()['games'];matches=[g for g in games if g['id']==game_id]
    require(len(matches)==1,'GAME_UNKNOWN','Use a registered game ID; unknown games need a reviewed location record.')
    g=matches[0];rows=[];warnings=[];seen=set()
    for loc in g['locations']:
        alias=loc['root']
        if alias not in roots or roots[alias] is None:
            warnings.append({'root':alias,'status':'ROOT_UNRESOLVED'});continue
        root=no_links(roots[alias])
        try: paths=walk_pattern(root,loc['pattern'])
        except (Error,OSError) as e:
            warnings.append({'root':alias,'status':getattr(e,'code','READ_FAILED')});continue
        for p in paths:
            if not p.is_file():continue
            if str(p).casefold() in seen:continue
            seen.add(str(p).casefold());info=p.stat()
            rows.append({'candidate_id':object_hash({'game':game_id,'path':str(p)})[:24],
                         'root_alias':alias,'relative':p.relative_to(root).as_posix(),
                         'private_path':str(p),'bytes':info.st_size,'modified_ns':info.st_mtime_ns,
                         'schema_status':g['schema_status'],'write_ready':False})
            require(len(rows)<=MAX_CANDIDATES,'DISCOVERY_LIMIT','Too many candidates.')
    return {'game_id':game_id,'candidates':rows,'warnings':warnings,
            'selection':'operator_review_required' if rows else 'not_found_or_storage_unresolved',
            'active_file_verified':False,'gameplay_verified':False,'files_modified':False}

def windows_roots() -> tuple[dict[str,Path],list[dict]]:
    """Reuse known-folder/Steam metadata helpers from the prior copy-only collector."""
    require(os.name=='nt','WINDOWS_REQUIRED','Automatic Known Folder lookup requires Windows; explicit fixture/host roots remain supported.')
    from . import known_folders_reference as old
    roots={};warnings=[]
    for alias,guid in old.GUIDS.items():
        try:roots[alias]=old.known_folder(guid)
        except OSError:warnings.append({'root':alias,'status':'ROOT_UNRESOLVED'})
    steam=None
    try:steam=Path(old.read_reg_string(r'Software\Valve\Steam','SteamPath'))
    except OSError:pass
    try:
        account=int(old.read_reg_string(r'Software\Valve\Steam\ActiveProcess','ActiveUser'))
        if steam and account>0:roots['steam_user']=steam/'userdata'/str(account)
    except (OSError,ValueError):warnings.append({'root':'steam_user','status':'ACTIVE_ACCOUNT_UNRESOLVED'})
    # Reuse the exact collection route without invoking collection or registry export.
    class Notes:
        metadata={}
        def note(self,game,status,**details): warnings.append({'game_number':game,'status':status})
    if steam:
        found=old.game_roots(steam,Notes())
        if 6 in found:roots['cyberpunk']=found[6]
        if 7 in found:roots['dmc5']=found[7]
    return roots,warnings
