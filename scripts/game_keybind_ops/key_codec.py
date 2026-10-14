"""No implicit conversion between display labels, virtual keys, scan codes or devices."""
from __future__ import annotations
from .deps import require
MODS=('LCtrl','RCtrl','Ctrl','LShift','RShift','Shift','LAlt','RAlt','Alt','Cmd')
PROTECTED={'MouseLeft','MouseRight','MouseMove','WheelUp','WheelDown','WheelLeft','WheelRight'}

def key_parts(key: str) -> set[str]:
    return set(key.split('+')) if type(key) is str else set()

def canonical_chord(key:str,modifiers:list[str]|None=None)->str:
    require(type(key) is str and key and '+' not in key,'KEY_INVALID','Use one canonical key plus explicit modifiers.')
    mods=modifiers or []
    require(type(mods) is list and len(mods)==len(set(mods)) and all(x in MODS for x in mods),'KEY_INVALID','Unknown or repeated modifier.')
    require(not ({'Ctrl','LCtrl'}<=set(mods) or {'Ctrl','RCtrl'}<=set(mods) or {'Shift','LShift'}<=set(mods) or {'Shift','RShift'}<=set(mods) or {'Alt','LAlt'}<=set(mods) or {'Alt','RAlt'}<=set(mods)),'KEY_AMBIGUOUS','Do not combine generic and sided forms of the same modifier.')
    return '+'.join(sorted(mods,key=MODS.index)+[key])

def encode(keymap:dict,key:str,modifiers:list[str]|None=None):
    canonical=canonical_chord(key,modifiers)
    require(canonical in keymap,'KEY_UNSUPPORTED','The pack has no reviewed encoding for this key/chord.')
    return keymap[canonical]

def unreal_chords(keys:dict[str,str],combinations:list[list[str]])->dict:
    """Authoring helper only: Unreal flag booleans cannot encode left/right variants."""
    output={}
    for mods in combinations:
        require(set(mods)<={'Ctrl','Shift','Alt','Cmd'},'KEY_UNSUPPORTED','Unreal boolean modifier flags do not prove left/right modifier support.')
        for key,native in keys.items():
            output[canonical_chord(key,mods)]={'key':native,'shift':'Shift' in mods,'ctrl':'Ctrl' in mods,'alt':'Alt' in mods,'cmd':'Cmd' in mods}
    return output
