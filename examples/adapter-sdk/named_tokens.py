"""Fictional trusted-code SDK example: `map action KEY` records.
NOT part of a data pack, no real game support implied. The host explicitly imports
this module after normal source review; packs cannot request module loading.
"""
import re
from game_keybind_ops.adapter_registry import Adapter,register_adapter
from game_keybind_ops.documents import Cell
from game_keybind_ops.deps import require


def parse(document):
    offset=0;counts={}
    for line in document.text.splitlines(keepends=True):
        text=line.rstrip('\r\n')
        if text.strip() and not text.lstrip().startswith('#'):
            m=re.fullmatch(r'map ([a-z0-9_-]+) ([A-Za-z0-9_]+)',text)
            require(m is not None,'FORMAT_UNSUPPORTED','Expected reviewed map ACTION KEY records.')
            ident=m[1];occurrence=counts.get(ident,0);counts[ident]=occurrence+1
            document.add(Cell({'action':ident,'occurrence':occurrence},m[2],offset+m.start(2),offset+m.end(2),'extension'))
        offset+=len(line)


def render(document,cell,new_value):
    require(type(new_value) is str and re.fullmatch(r'[A-Za-z0-9_]+',new_value),'INVALID_VALUE','Expected one native key token.')
    return [(cell.start,cell.end,new_value)]


def register():
    register_adapter(Adapter('ext-named-tokens',1,('.conf',),parse,render,'Exact action and duplicate occurrence. Synthetic SDK example.'))
