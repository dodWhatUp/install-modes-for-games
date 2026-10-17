"""Data-only game identity and layout contracts; never execute a definition.

A new game using a known adapter needs only a support JSON file. New executable
adapter code is a separate reviewed development change, never imported from data.
"""
from __future__ import annotations
import copy
import re
from .safety import require, safe_relative, slug

ADAPTERS = {'umm', 'smapi', 'bepinex', 'directory', 'external'}
LAYOUTS = {'umm', 'smapi', 'generic'}
DEFINITION_FIELDS = {'game_id','name','manager_id','adapter','platform','executable_any',
                     'mods_relative','loader_markers','scan_depth','review_note'}


def text(value, maximum=240):
    require(type(value) is str and 0 < len(value) <= maximum and
            not any(ord(c)<32 for c in value), 'SUPPORT_SCHEMA', 'Expected short, nonempty printable text.')
    return value


def validate_definition(value):
    require(type(value) is dict and set(value)==DEFINITION_FIELDS,
            'SUPPORT_SCHEMA', 'Game definition fields do not match schema 1.')
    ident=slug(value['game_id'])
    require(ident==ident.lower(), 'INVALID_ID', 'Game IDs must be lowercase.')
    text(value['name'],160); slug(value['manager_id'])
    known={'unity-mod-manager':{'umm'},'smapi':{'smapi'},'bepinex':{'bepinex'},
           'mod-organizer-2':{'external'},'vortex':{'external'},'rhi':{'external'}}
    require(value['manager_id'] not in known or value['adapter'] in known[value['manager_id']],
            'SUPPORT_SCHEMA','The selected manager and file-format adapter disagree.')
    require(value['adapter'] in ADAPTERS, 'ADAPTER_UNAVAILABLE', 'This adapter is not implemented. Add reviewed code, not a command in JSON.')
    require(value['platform'] in {'windows','linux','macos'}, 'SUPPORT_SCHEMA', 'Define one target operating system per support pack.')
    require(type(value['scan_depth']) is int and 1 <= value['scan_depth'] <= 6,
            'SUPPORT_SCHEMA', 'Scan depth must be 1–6, bounded to the named mod directory.')
    for key in ('executable_any','loader_markers'):
        a=value[key]
        require(type(a) is list and (1 if key=='executable_any' else 0)<=len(a)<=8,
                'SUPPORT_SCHEMA', 'Expected bounded game/loader marker lists.')
        for path in a: safe_relative(path)
        require(len({p.casefold() for p in a})==len(a), 'SUPPORT_SCHEMA', 'Marker paths collide.')
    if value['adapter']=='external':
        require(value['mods_relative'] is None,'SUPPORT_SCHEMA','External managers keep ownership of their mod directories.')
    else:
        safe_relative(value['mods_relative'])
        require(value['mods_relative'].casefold() not in {'windows','system32','users'},
                'SUPPORT_SCHEMA','The mod directory must be game-local.')
    require(type(value['review_note']) is str and len(value['review_note'])<=800,
            'SUPPORT_SCHEMA','Review note is too long.')
    return value


def validate_mode(mode):
    # A preset is not necessarily a combat mode: default, quality-of-life, etc.
    require(type(mode) is str and bool(re.fullmatch(r'[a-z][a-z0-9-]{0,47}',mode)),
            'MODE','Use a short lowercase preset name.')
    return mode


def archive_contract(item, manager_id, definition=None):
    adapter=definition['adapter'] if definition else ('umm' if manager_id=='unity-mod-manager' else
                                                     'smapi' if manager_id=='smapi' else 'generic')
    default='generic' if item['kind']=='manager' and manager_id!='unity-mod-manager' else (
        adapter if adapter in {'umm','smapi'} else 'generic')
    layout=item.get('archive_layout',default)
    require(layout in LAYOUTS,'ARCHIVE_LAYOUT','Unsupported declared archive format.')
    root=item.get('archive_root')
    if root is not None:
        safe_relative(root)
        require(layout=='generic','ARCHIVE_LAYOUT','Manifest adapters find their own mod root.')
    expected=item.get('mod_id',item.get('umm_id'))
    if expected is not None: slug(expected)
    required=item.get('required_files',[])
    require(type(required) is list and len(required)<=32,'ARCHIVE_LAYOUT','Expected at most 32 required payload files.')
    for path in required: safe_relative(path)
    require(len({p.casefold() for p in required})==len(required),'ARCHIVE_LAYOUT','Required files collide.')
    return {'layout':layout,'root':root,'expected_id':expected,'required_files':required}


def default_definition(game_id, name, adapter='directory', executable='Game.exe'):
    require(adapter in ADAPTERS,'ADAPTER_UNAVAILABLE','Unknown adapter.')
    return validate_definition({'game_id':game_id,'name':name,
        'manager_id':{'umm':'unity-mod-manager','smapi':'smapi','bepinex':'bepinex',
                      'directory':'manual','external':'manual'}[adapter],
        'adapter':adapter,'platform':'windows','executable_any':[executable],
        'mods_relative':None if adapter=='external' else ('BepInEx/plugins' if adapter=='bepinex' else 'Mods'),
        'loader_markers':[],'scan_depth':3,
        'review_note':'Template only. Verify exact build, paths, loader and author instructions before using real mods.'})
