"""Versioned, importable game support packs. A pack is data, never plugin code.

Registry sources: shipped pack JSON, explicit local imports, legacy recipes.
Mutable selection is one compare-before-write pointer; pack revisions are immutable.
"""
from __future__ import annotations
import copy
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl
from datetime import date
from .definitions import validate_definition, default_definition, validate_mode
from .safety import (ModError, require, no_links, contained, read_json, strict_json,
                     object_hash, json_new, write_new, regular, digest, local_lock, slug)
from .recipes import validate_recipe
from .managers import capabilities

PACK_FIELDS={'schema_version','kind','pack_version','definition','recipe','sources','notes'}
BUILTIN=Path(__file__).resolve().parents[2]/'examples/game-tool-hub/game-support'
MAX_PACKS=64
MAX_PACK_BYTES=512*1024
SHA=re.compile(r'[0-9a-f]{64}\Z')


def _data(value,depth=0):
    require(depth<=20,'SUPPORT_SCHEMA','Support data is nested too deeply.')
    if type(value) is dict:
        require(not {str(k).lower() for k in value}&{'command','shell','script','python','eval','password','apikey','api_key','token','cookie'},
                'EXECUTABLE_RECIPE','Executable code and credential fields cannot be part of game support data.')
        for v in value.values():_data(v,depth+1)
    elif type(value) is list:
        for v in value:_data(v,depth+1)
    elif type(value) is str:
        require(len(value)<=4000,'SUPPORT_SCHEMA','A support text field is too long.')
        if value.startswith(('https://','http://')):
            u=urlsplit(value)
            require(u.scheme=='https' and u.hostname and not u.username and not u.password,
                    'SUPPORT_SCHEMA','Support URLs must use credential-free HTTPS.')
            require(not {k.casefold() for k,_ in parse_qsl(u.query)} &
                    {'key','apikey','api_key','token','auth','authorization','access_token','sig','signature','expires'},
                    'SUPPORT_SCHEMA','Do not save authorization or signed download URLs in a support pack.')
    else:
        require(value is None or type(value) in (int,bool),'SUPPORT_SCHEMA','Only bounded JSON data is supported.')


def validate_pack(pack):
    require(type(pack) is dict and set(pack)==PACK_FIELDS,'SUPPORT_SCHEMA','Use the exact game-support schema fields.')
    require(type(pack['schema_version']) is int and pack['schema_version']==1 and pack['kind']=='game_support_pack',
            'SUPPORT_SCHEMA','Unsupported support pack schema.')
    require(type(pack['pack_version']) is str and bool(re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?',pack['pack_version'])),
            'SUPPORT_SCHEMA','Use a semantic pack version, such as 1.0.0.')
    _data(pack);d=validate_definition(pack['definition'])
    sources=pack['sources']
    require(type(sources) is list and 0<len(sources)<=16,'SUPPORT_SCHEMA','Keep 1–16 source references, including template provenance.')
    for source in sources:
        require(type(source) is dict and set(source)=={'url','checked_on','evidence'},'SUPPORT_SCHEMA','A source needs URL, checked_on and evidence.')
        require(type(source['url']) is str,'SUPPORT_SCHEMA','Source URL must be a string.')
        u=urlsplit(source['url'])
        require(u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and not u.query,
                'SUPPORT_SCHEMA','Use credential-free HTTPS source URLs without signed query parameters.')
        require(type(source['checked_on']) is str and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',source['checked_on'])),
                'SUPPORT_SCHEMA','Source review date must be YYYY-MM-DD.')
        try:date.fromisoformat(source['checked_on'])
        except ValueError:raise ModError('SUPPORT_SCHEMA','Source review date is not a calendar date.') from None
        require(source['evidence'] in {'upstream-documented','template-unverified','operator-reported'},
                'SUPPORT_SCHEMA','Unsupported evidence level.')
    require(type(pack['notes']) is list and len(pack['notes'])<=12 and all(type(n) is str and len(n)<=800 for n in pack['notes']),
            'SUPPORT_SCHEMA','Use at most 12 short notes.')
    if pack['recipe'] is not None:
        recipe=compose_recipe(pack,validate=False)
        validate_recipe(recipe)
        require(recipe['game_id']==d['game_id'] and recipe['manager_id']==d['manager_id'],
                'GAME_MISMATCH','The recipe and definition must identify the same game and manager.')
        require('game_definition' not in pack['recipe'],'SUPPORT_SCHEMA','Definition is owned by the pack, not repeated in its recipe.')
    require(len(json.dumps(pack,ensure_ascii=False).encode())<=MAX_PACK_BYTES,'SIZE_LIMIT','Support pack is too large.')
    return pack


def compose_recipe(pack,validate=True):
    if validate:validate_pack(pack)
    if pack['recipe'] is None:return None
    r=copy.deepcopy(pack['recipe']);r['game_definition']=copy.deepcopy(pack['definition'])
    r['support_revision']=object_hash(pack)
    return r


def read_pack(source):
    source=regular(Path(source),MAX_PACK_BYTES*2)
    if source.suffix.lower()=='.zip':
        try:
            with zipfile.ZipFile(source) as z:
                require(z.namelist()==['game-support.json'],'SUPPORT_SCHEMA','A support ZIP contains exactly game-support.json; executable payloads are not accepted.')
                entry=z.infolist()[0]
                require(entry.file_size<=MAX_PACK_BYTES and entry.compress_type in {0,8} and not entry.flag_bits&1,
                        'SIZE_LIMIT','Unsupported support ZIP.')
                raw=z.read(entry)
        except (zipfile.BadZipFile,RuntimeError,NotImplementedError,EOFError) as e:
            raise ModError('INVALID_SUPPORT_ZIP','The support ZIP is damaged or unsupported; nothing was registered.') from e
    else:raw=source.read_bytes()
    require(len(raw)<=MAX_PACK_BYTES,'SIZE_LIMIT','Support pack is too large.')
    return validate_pack(strict_json(raw)),raw


def describe(pack):
    validate_pack(pack);d=pack['definition'];r=pack['recipe']
    return {'game_id':d['game_id'],'name':d['name'],'pack_version':pack['pack_version'],
        'revision':object_hash(pack),'manager_id':d['manager_id'],'adapter':d['adapter'],
        'recipe_available':r is not None,'mod_items':len(r['items']) if r else 0,
        'preset_names':list(r.get('presets',{})) if r else [],'capabilities':capabilities(d),
        'evidence':'definition_validated_not_game_tested','changes_game_files':False}


def scaffold(game_id,name,adapter='directory',executable='Game.exe'):
    d=default_definition(game_id,name,adapter,executable)
    return validate_pack({'schema_version':1,'kind':'game_support_pack','pack_version':'0.1.0',
        'definition':d,'recipe':None,
        'sources':[{'url':'https://example.invalid/replace-with-author-source','checked_on':'2026-10-13','evidence':'template-unverified'}],
        'notes':['No mod list yet. Research author instructions, then add recipe items and presets. No game or mod is installed by this template.']})


def schema():
    """Small machine-readable contract. The runtime validator is authoritative."""
    return {'schema_version':1,'kind':'game_support_authoring_contract','pack_fields':sorted(PACK_FIELDS),
        'definition_example':default_definition('example-game','Example Game'),
        'adapter_ids':['umm','smapi','bepinex','directory','external'],
        'archive_layouts':['umm','smapi','generic'],
        'recipe_required_fields':['schema_version','kind','game_id','manager_id','items'],
        'item_example':{'id':'author-mod','name':'Author Mod','kind':'mod','display_version':'choose compatible version',
            'source':{'kind':'manual'},'download_page':'https://example.invalid/author-mod',
            'max_download_bytes':16777216,'sha256':None,'archive_layout':'generic',
            'required_files':[],'requires':[],'conflicts':[]},
        'recipe_presets_example':{'default':['author-mod']},
        'optional_item_fields':['mod_id','archive_root','required_files','expected_version'],
        'validation':'All unknown top-level pack/definition fields rejected; no commands or secrets; paths stay relative.',
        'installation_authority':False,'automatic_network':False,
        'next':'Validate the data, review the diff, then import with the exact reviewed digest. Adding an unknown adapter requires a separately tested code module.'}


class SupportRegistry:
    def __init__(self,data_dir,builtin=BUILTIN):
        self.root=no_links(Path(data_dir))/'mod-workflows'/'game-support'
        self.builtin=no_links(Path(builtin))

    def _shipped(self):
        rows={}
        if not self.builtin.exists():return rows
        paths=sorted(self.builtin.glob('*.json'))
        require(len(paths)<=MAX_PACKS,'RECORD_LIMIT','Too many shipped game support packs.')
        for p in paths:
            pack,_=read_pack(p);ident=pack['definition']['game_id']
            require(ident not in rows,'SUPPORT_CONFLICT','Duplicate shipped game support identity.')
            rows[ident]={'pack':pack,'revision':object_hash(pack),'source':'shipped','path':p}
        return rows

    def rows(self):
        rows=self._shipped()
        if not self.root.exists():return rows
        folders=sorted(self.root.iterdir())
        require(len(folders)<=MAX_PACKS+2,'RECORD_LIMIT','Too many local support records.')
        for folder in folders:
            no_links(folder)
            if not folder.is_dir():continue
            slug(folder.name);pointer=folder/'current.json'
            if not pointer.exists():continue # incomplete immutable revision, not activated
            state=read_json(pointer,2048)
            require(type(state) is dict and set(state)=={'schema_version','revision'} and state['schema_version']==1 and
                    type(state['revision']) is str and SHA.fullmatch(state['revision']),
                    'SUPPORT_CORRUPT','Support selection pointer is invalid.')
            path=folder/state['revision']/'game-support.json'
            pack,_=read_pack(path);revision=object_hash(pack)
            require(revision==state['revision'] and pack['definition']['game_id']==folder.name,
                    'SUPPORT_CORRUPT','Selected support data changed; do not use it.')
            rows[folder.name]={'pack':pack,'revision':revision,'source':'locally_reviewed','path':path}
        require(len(rows)<=MAX_PACKS,'RECORD_LIMIT','Too many active support packs.')
        return rows

    def get(self,game_id):
        row=self.rows().get(slug(game_id))
        require(row is not None,'SUPPORT_REQUIRED','No support definition exists for this game.')
        return row

    def review(self,pack):
        after=describe(pack);before=self.rows().get(after['game_id']);diff=[]
        if before:
            for field in sorted(PACK_FIELDS):
                if before['pack'][field]!=pack[field]:diff.append(field)
        return {'before_revision':before['revision'] if before else None,'after':after,
                'changed_sections':diff if before else sorted(PACK_FIELDS),
                'warning':'Registration changes future plans only; old plans and receipts remain immutable. Source references are evidence, not trust certification.'}

    def import_pack(self,source,*,reviewed_sha256,expected_revision=None,confirmed=False):
        require(confirmed,'REVIEW_REQUIRED','Review and confirm this data pack before selecting it.')
        pack,raw=read_pack(source);revision=object_hash(pack);ident=pack['definition']['game_id']
        require(revision==reviewed_sha256,'SOURCE_CHANGED','Support data changed after review.')
        with local_lock(self.root):
            folder=contained(self.root,ident);pointer=folder/'current.json'
            previous=regular(pointer,2048).read_bytes() if pointer.exists() else None
            rows=self.rows();before=rows.get(ident)
            require((regular(pointer,2048).read_bytes() if pointer.exists() else None)==previous,
                    'CONCURRENT_CHANGE','Support changed while reading its current selection.')
            if before and before['revision']==revision:return {'game_id':ident,'status':'ALREADY_REGISTERED','revision':revision}
            require((before['revision'] if before else None)==expected_revision,
                    'CONCURRENT_CHANGE','Game support changed or already exists. Review its current revision before replacement.')
            require(ident in rows or len(rows)<MAX_PACKS,'RECORD_LIMIT','Support pack limit reached.')
            folder=contained(self.root,ident);folder.mkdir(exist_ok=True)
            revisions=[p for p in folder.iterdir() if p.is_dir()]
            revdir=folder/revision
            require(revdir.exists() or len(revisions)<32,'RECORD_LIMIT','Too many revisions; preserve/review old records before continuing.')
            if revdir.exists():
                saved,_=read_pack(revdir/'game-support.json')
                require(saved==pack,'SUPPORT_CORRUPT','The saved revision is not intact.')
            else:
                revdir.mkdir();write_new(revdir/'game-support.json',raw)
            recipe=compose_recipe(pack)
            if recipe is not None:
                target=revdir/'recipe.json'
                if target.exists():require(read_json(target)==recipe,'SUPPORT_CORRUPT','Derived recipe changed.')
                else:json_new(target,recipe)
            data=(json.dumps({'schema_version':1,'revision':revision},indent=2)+'\n').encode()
            fd,tmp=tempfile.mkstemp(dir=folder,prefix='.selection-')
            try:
                with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
                require((regular(pointer,2048).read_bytes() if pointer.exists() else None)==previous,
                        'CONCURRENT_CHANGE','Support selection changed during registration.')
                os.replace(tmp,pointer)
            finally:
                if os.path.exists(tmp):os.unlink(tmp)
            require(self.get(ident)['revision']==revision,'SUPPORT_CORRUPT','Support readback failed.')
        return {'game_id':ident,'status':'REGISTERED_NOT_INSTALLED','revision':revision,
                'previous_revision':expected_revision}

    def recipe_path(self,game_id):
        row=self.get(game_id);recipe=compose_recipe(row['pack'])
        if recipe is None:return None
        if row['source']=='locally_reviewed':
            target=row['path'].parent/'recipe.json'
            require(read_json(target)==recipe,'SUPPORT_CORRUPT','Derived recipe is not the selected pack’s recipe.')
            return target
        # This derived recipe is generated during packaging, not on a read-only
        # AI request. It is verified against the canonical support pack every read.
        target=self.builtin.parent/'mod-recipes'/(game_id+'.json')
        require(read_json(target)==recipe,'SUPPORT_CORRUPT','Shipped derived recipe is missing or changed.')
        return target

    def export(self,game_id,destination):
        row=self.get(game_id);dest=no_links(Path(destination))
        raw=(json.dumps(row['pack'],indent=2,ensure_ascii=False)+'\n').encode()
        if dest.suffix.lower()=='.zip':
            import io
            b=io.BytesIO()
            with zipfile.ZipFile(b,'w',compression=zipfile.ZIP_DEFLATED) as z:z.writestr('game-support.json',raw)
            raw=b.getvalue()
        write_new(dest,raw)
        pack,_=read_pack(dest)
        require(object_hash(pack)==row['revision'],'SUPPORT_CORRUPT','Export readback failed.')
        return {'game_id':game_id,'revision':row['revision'],'bytes':len(raw),'status':'EXPORTED_DATA_ONLY'}
