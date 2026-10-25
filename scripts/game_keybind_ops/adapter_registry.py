"""Explicit trusted-code extension seam. Data packs cannot import/execute code."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from .deps import require

@dataclass(frozen=True)
class Adapter:
    name: str
    version: int
    extensions: tuple[str, ...]
    parser: Callable | None = None
    renderer: Callable | None = None
    selector_help: str = ""

_ADAPTERS = {
    a.name: a for a in (
        Adapter('json',1,('.json',),selector_help='RFC6901 pointer or json_match identity'),
        Adapter('jsonc',1,('.json','.jsonc'),selector_help='JSON comments/trailing comma; original spans preserved'),
        Adapter('ini',1,('.ini','.cfg','.conf'),selector_help='section + key/command + occurrence'),
        Adapter('ini-sparse',1,('.ini','.cfg','.conf'),selector_help='optional single entry + reviewed fallback key'),
        Adapter('ue-ini',1,('.ini',),selector_help='existing ActionMappings/AxisMappings key only'),
        Adapter('ue-chord',1,('.ini',),selector_help='existing ActionMappings key and four explicit modifier flags'),
        Adapter('xml',1,('.xml',),selector_help='indexed element or xml_match identity + attribute'),
        Adapter('cfg-bind',1,('.cfg',),selector_help='quoted bind KEY COMMAND'),
        Adapter('idtech-bindset',1,('.cfg',),selector_help='configVersion 19; bindset + kind + command + occurrence'),
        Adapter('keyvalues',1,('.vdf','.acf','.txt','.cfg'),selector_help='quoted KeyValues1 path of name/occurrence pairs; no directives'),
        Adapter('colon-lines',1,('.txt','.properties','.conf'),selector_help='one key:value line, exact key and occurrence'),
    )
}

def adapter_info(name: str) -> Adapter:
    require(type(name) is str and name in _ADAPTERS,'ADAPTER_UNSUPPORTED','This format needs an explicitly reviewed host adapter.')
    return _ADAPTERS[name]

def capabilities() -> list[dict]:
    return [{'id':a.name,'contract_version':a.version,'extensions':list(a.extensions),'selector_help':a.selector_help,
             'loaded':True,'gameplay_verified':False} for a in _ADAPTERS.values()]

def register_adapter(adapter: Adapter) -> None:
    """Called only by reviewed HOST Python code. This is not a sandbox or AI tool.
    Parser receives Document and adds bounded Cells. Renderer returns replacement
    spans (start,end,text); Document enforces bounds/reparse. No auto-discovery.
    """
    require(isinstance(adapter,Adapter) and adapter.name.startswith('ext-') and len(adapter.name)<80,
            'ADAPTER_INVALID','Custom adapters use an ext- namespace.')
    require(adapter.name not in _ADAPTERS,'ADAPTER_CONFLICT','Never replace a loaded adapter silently.')
    require(adapter.version==1 and callable(adapter.parser) and callable(adapter.renderer),
            'ADAPTER_INVALID','Expected parser and renderer implementing adapter contract 1.')
    require(adapter.extensions and set(adapter.extensions)<={'.json','.ini','.cfg','.xml','.conf','.txt','.properties','.vdf'},
            'FILE_ROLE_UNSUPPORTED','This extension seam is for text config roles, not saves/binaries/scripts.')
    _ADAPTERS[adapter.name]=adapter
