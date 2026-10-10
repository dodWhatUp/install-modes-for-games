#!/usr/bin/env python3
"""Audit an unchanged candidate against the inherited R2 binding corpus.

Standard-library only. Reads the exact existing HTML derivative, never executes
its scripts, and never edits an Azeron profile. The parser expands explicitly
listed input variants, not an assumption that every slash means interchangeable
actions. Unknown syntax is retained. Route results are logical / model-only.
"""
from __future__ import annotations
import argparse, collections, hashlib, itertools, json, re
from pathlib import Path

ALIASES: dict[str, str] = {}
def add(key: str, *names: str) -> None:
    for name in (key, *names): ALIASES[name.lower()] = key
for key, names in {
 'Ctrl':['Control'], 'Shift':[], 'Alt':[],
 'Left Ctrl':['Left Control'], 'Right Ctrl':['Right Control'],
 'Left Shift':[], 'Right Shift':[], 'Left Alt':[], 'Right Alt':[],
 'Esc':['Escape'], 'Space':['Spacebar'], 'Enter':['Return'], 'Tab':[],
 'Backspace':[], 'Delete':['Del'], 'Insert':['Ins'], 'Home':[], 'End':[],
 'Page Up':['PageUp'], 'Page Down':['PageDown'], 'Caps Lock':['CapsLock'],
 'Num Lock':['NumLock'], 'Scroll Lock':['ScrollLock'], 'Pause':['Pause/Break'],
 'Up Arrow':['Up'], 'Down Arrow':['Down'], 'Left Arrow':['Left'], 'Right Arrow':['Right'],
 'Comma':[','], 'Period':['.'], 'Slash':['/'], 'Backslash':['\\'], 'Semicolon':[';'],
 'Apostrophe':["'"], 'Minus':['-'], 'Equals':['='], 'Backtick':['`','Grave'],
 'Left Bracket':['['], 'Right Bracket':[']'],
 # Symbols are NOT silently assigned a US-layout physical key or shifted chord.
 'Plus':['+'], 'Tilde':['~'], 'Underscore':['_'], 'Question Mark':['?'],
 'Hash':['#'], 'Less Than':['<'], 'Greater Than':['>'],
 'Mouse Left':['LMB','Mouse1','Left Mouse','Left Mouse Button'],
 'Mouse Right':['RMB','Mouse2','Right Mouse','Right Mouse Button'],
 'Mouse Middle':['MMB','MOUSE3','Middle Mouse','Middle Mouse Button','Mouse Wheel Button'],
 'Mouse Button 4':[], 'Mouse Button 5':[], 'Mouse Wheel':[],
 'Mouse Wheel Up':['WheelUp','Wheel Up'], 'Mouse Wheel Down':['WheelDown','Wheel Down'],
 'Mouse Movement':['MouseMove','Mouse move'],
}.items(): add(key,*names)

ARROWS = ['Up Arrow','Down Arrow','Left Arrow','Right Arrow']
SYMBOLS = {'Plus','Tilde','Underscore','Question Mark','Hash','Less Than','Greater Than'}
SIDE_RE = re.compile(r'^(Left|Right) (Ctrl|Shift|Alt)$')

def canonical(token: str) -> str | None:
    token = re.sub(r'\s+', ' ', token.strip())
    if token.lower() in ALIASES: return ALIASES[token.lower()]
    if re.fullmatch(r'[A-Za-z0-9]',token): return token.upper()
    if re.fullmatch(r'F(?:[1-9]|1[0-9]|2[0-4])',token,re.I): return token.upper()
    if re.fullmatch(r'Numpad (?:[0-9]|[+*/.\-]|Enter)',token,re.I):
        return 'Numpad '+token[7:].title()
    return None

def logical(key: str) -> str:
    return SIDE_RE.sub(lambda m:m[2],key)

def alternatives(raw: str, gesture: str='') -> dict:
    """Return explicit listed input variants; their gameplay relationship is unknown.
    Whole-row failure is conservative: it prevents partial success being used
    to claim coverage of an input expression containing an unknown component.
    """
    text=raw.strip(); notes=[]
    if re.search(r'\bthen\b',text,re.I):
        return dict(status='MANUAL_REVIEW',reason='SEQUENCE_NOT_SIMULTANEOUS',variants=[],notes=[])
    if re.search(r'\btwice\b',text,re.I):
        text=re.sub(r'\s+twice\b','',text,flags=re.I)
        notes.append('REPETITION_TIMING_NOT_EVALUATED')
    exact=canonical(text)
    if exact: return dict(status='PARSED',variants=[[exact]],notes=notes)
    if re.fullmatch(r'(?:[A-Z]\s+){1,}[A-Z]',text):
        return dict(status='PARSED',variants=[[t] for t in text.split()],notes=notes+['EXPLICIT_LETTER_LIST'])
    text=re.sub(r'Mouse\s+wheel\s+up\s*/\s*(?:Mouse\s+wheel\s+)?down',
                'Mouse Wheel Up | Mouse Wheel Down',text,flags=re.I)
    # Reattach an explicit preceding modifier to a collapsed mouse-wheel group.
    if '|' in text and '+' in text:
        left,right=text.split('|',1)
        prefix=left.rsplit('+',1)[0].strip()
        text=left+' / '+prefix+' + '+right.strip()
    else: text=text.replace('|','/')
    m=re.fullmatch(r'Numpad\s+([0-9](?:\s*/\s*[0-9])+)',text,re.I)
    if m:
        return dict(status='PARSED',variants=[['Numpad '+n] for n in re.findall(r'\d',m[1])],notes=notes+['EXPLICIT_NUMPAD_LIST'])
    # The inherited row itself explicitly says hold V/Shift plus direction.
    if text in ['V + W / A / S / D','Shift + W / A / S / D']:
        first=text.split(' + ')[0]
        if re.search(r'hold '+first,gesture,re.I):
            return dict(status='PARSED',variants=[[first,d] for d in 'WASD'],notes=notes+['MODIFIER_SCOPE_FROM_INHERITED_GESTURE'])
        return dict(status='MANUAL_REVIEW',reason='MODIFIER_SCOPE_AMBIGUOUS',variants=[],notes=notes)
    # Parent ranges have an explicit ascending end; 1-0 remains unresolved.
    if re.search(r'\b1[–—-]0\b',text):
        return dict(status='MANUAL_REVIEW',reason='CROSS_ROW_RANGE_1_TO_0',variants=[],notes=notes)
    parts=re.split(r'\s+or\s+|\s*/\s*|\s*;\s*',text,flags=re.I)
    # Commas separate ONLY the known digit-list spelling, not comma key chords.
    parts=[p2 for p in parts for p2 in (re.split(r',\s+',p) if re.match(r'^\d[–—-]\d,\s',p) else [p])]
    # Unprefixed tails of abbreviated chords need explicit source confirmation.
    if len(parts)>1 and '+' in parts[0] and canonical(parts[0]) is None and all('+' not in p for p in parts[1:]):
        return dict(status='MANUAL_REVIEW',reason='MODIFIER_SCOPE_AMBIGUOUS',variants=[],notes=notes)
    variants=[]
    for part in parts:
        part=part.strip()
        atoms=[part] if canonical(part) else re.split(r'\s*\+\s*',part)
        if not atoms or any(not a.strip() for a in atoms):
            return dict(status='MANUAL_REVIEW',reason='EMPTY_OR_AMBIGUOUS_TOKEN',variants=[],notes=notes)
        options=[]
        for atom in atoms:
            key=canonical(atom)
            if key: options.append([key]);continue
            if atom.lower() in ['arrows','arrow keys']:
                options.append(ARROWS);continue
            rg=re.fullmatch(r'(F?)(\d+)\s*[–—-]\s*(F?)(\d+)',atom,re.I)
            if rg:
                a,b=int(rg[2]),int(rg[4]); pre=rg[1].upper();pre2=rg[3].upper()
                if a<=b and ((pre==pre2=='' and b<=9) or (pre=='F' and pre2 in ('','F') and 1<=a<=b<=24)):
                    options.append([pre+str(i) for i in range(a,b+1)]);continue
            return dict(status='MANUAL_REVIEW',reason='UNRESOLVED_TOKEN: '+atom,variants=[],notes=notes)
        variants.extend([list(dict.fromkeys(x)) for x in itertools.product(*options)])
    unique=[]
    for v in variants:
        if v not in unique:unique.append(v)
    return dict(status='PARSED',variants=unique,notes=notes)

def finger(pos: str) -> str:
    m=re.fullmatch(r'R[1-5]C([1-4])',pos)
    if m:return ['little','ring','middle','index'][int(m[1])-1]
    if pos=='L3':return 'little'
    if pos=='R3':return 'index'
    if pos.startswith(('TH_','ST_')) or pos=='STICK':return 'thumb'
    raise ValueError(pos)

def route(variant: list[str], maps: dict, extra_movement=False) -> dict:
    keys=[logical(k) for k in variant if not k.startswith('Mouse ')]
    side=[k for k in variant if SIDE_RE.fullmatch(k)]
    mouse=[k for k in variant if k.startswith('Mouse ')]
    if not keys:return dict(status='MOUSE_ONLY',banks=[],side_unverified=side,mouse=mouse)
    unknown=[k for k in keys if not any(k in b.values() for b in maps.values()) and k not in ['W','A','S','D']]
    if unknown:
        status='SYMBOL_LAYOUT_REVIEW' if all(k in SYMBOLS for k in unknown) else 'UNMAPPED_OUTPUT'
        return dict(status=status,missing=unknown,banks=[],side_unverified=side,mouse=mouse)
    banks=[]; independent=[]
    for name,bank in maps.items():
        opts=[[p for p,v in bank.items() if v==k]+(['STICK'] if k in ['W','A','S','D'] else []) for k in keys]
        if not all(opts):continue
        banks.append(name)
        for combo in itertools.product(*opts):
            pairs=[(k,p) for k,p in zip(keys,combo)]
            # Explicit multiple movement directions can share the one thumb:
            # diagonals combine W/A, etc.; opposite directions cannot.
            dirs=[k for k,p in pairs if p=='STICK']
            if set(dirs)&{'W','S'}=={'W','S'} or set(dirs)&{'A','D'}=={'A','D'}:continue
            groups=[finger(p) for k,p in pairs if p!='STICK']
            if dirs or extra_movement:groups.append('thumb')
            if name!='BASIC':groups.append('little') # held selector hypothesis
            if len(set(groups))==len(groups):
                independent.append(dict(bank=name,positions=dict(pairs),stick_outputs=dirs))
                break
    if not banks:return dict(status='NO_SINGLE_BANK',banks=[],side_unverified=side,mouse=mouse)
    if not independent:return dict(status='FINGER_MODEL_CONFLICT',banks=banks,side_unverified=side,mouse=mouse)
    best=independent[0]
    status=('STICK_COMMAND_ROUTE' if best['stick_outputs'] else
            'DIRECT_BUTTON_ROUTE' if best['bank']=='BASIC' else 'LAYERED_BUTTON_ROUTE')
    return dict(status=status,banks=banks,route=best,other_routes=independent[1:],side_unverified=side,mouse=mouse)

def movement_action(row: dict) -> bool:
    # Explicit, conservative role heuristic; never a telemetry claim.
    return bool(re.search(
        r'^(Move(?:\s|$)|Movement$|Forward/back|Camera (?:pan|movement|tilt)|Pan camera|Map pan|Camera$|'
        r'Steer|Accelerate|Throttle$|Brake/reverse$|Thrust / brake$|Roll$|Boat brake/reverse$|'
        r'Sprint$|Dodge$|Jump forward$|Jump attack$|Slow lean right/left$|Blindfire up/right$|Peek$)',
        row['action'], re.I))

def run(html_path: Path, layout_path: Path, output: Path) -> dict:
    html=html_path.read_text(encoding='utf-8')
    marker='const data=';start=html.index(marker)+len(marker)
    rows,_=json.JSONDecoder().raw_decode(html[start:])
    layout=json.loads(layout_path.read_text(encoding='utf-8')); maps=layout['maps']
    if len(rows)!=2195 or len({r['game'] for r in rows})!=94:raise ValueError('Unexpected corpus revision')
    if len({r['id'] for r in rows})!=len(rows):raise ValueError('Duplicate row IDs')
    results=[]; per_game=collections.defaultdict(list)
    for raw in rows:
        p=alternatives(raw['key'],raw['gesture']); vs=[]
        if p['status']=='PARSED':
            for keys in p['variants']:
                base=route(keys,maps);stress=route(keys,maps,True)
                if base['status']=='STICK_COMMAND_ROUTE':
                    if movement_action(raw):
                        base['status']='STICK_DIRECTIONAL_ROUTE'
                    else:
                        stress['status']='STICK_ROLE_CONFLICT'
                        stress['reason']='A command consumes stick output; arbitrary independent movement cannot be assumed.'
                vs.append(dict(keys=keys,isolated=base,movement_stress=stress))
        record=dict(row=raw,syntax=p,variants=vs,role_basis='ANALYST_ACTION_LABEL_HEURISTIC',
                    player_frequency=None,runtime_verified=False)
        results.append(record);per_game[raw['game']].append(record)
    counts=collections.Counter(r['syntax']['status'] for r in results)
    route_counts=collections.Counter(v['isolated']['status'] for r in results for v in r['variants'])
    games=[]
    for game,recs in per_game.items():
        flat=[v for r in recs for v in r['variants']]
        count=collections.Counter(v['isolated']['status'] for v in flat)
        flags={
          'single_bank_gaps':[r['row']['id'] for r in recs if any(v['isolated']['status']=='NO_SINGLE_BANK' for v in r['variants'])],
          'finger_conflicts':[r['row']['id'] for r in recs if any(v['isolated']['status']=='FINGER_MODEL_CONFLICT' for v in r['variants'])],
          'unmapped_outputs':[r['row']['id'] for r in recs if any(v['isolated']['status']=='UNMAPPED_OUTPUT' for v in r['variants'])],
          'stick_for_nonmovement':[r['row']['id'] for r in recs if any(v['isolated']['status']=='STICK_COMMAND_ROUTE' for v in r['variants'])],
          'symbols_need_layout_review':[r['row']['id'] for r in recs if any(v['isolated']['status']=='SYMBOL_LAYOUT_REVIEW' for v in r['variants'])],
          'needs_syntax_review':[r['row']['id'] for r in recs if r['syntax']['status']!='PARSED'],
          'side_specific_input':[r['row']['id'] for r in recs if any(v['isolated']['side_unverified'] for v in r['variants'])],
        }
        games.append(dict(game=game,family=recs[0]['row']['family'],rows=len(recs),listed_variants=len(flat),
                          isolated_counts=dict(count),flags=flags))
    return dict(schema_version='azeron-corpus-access-audit/1',revision='R4',date='2026-10-10',
      status='DERIVED_CORPUS_AUDIT_NOT_NATIVE_PROFILE',layout_revision=layout['revision'],
      input_fingerprints={str(p.name):dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in [html_path,layout_path]},
      assumptions=[
       'Input is an existing full R2 HTML delivery derivative, not reconstructed original master bytes.',
       'The R3 layout is unchanged; the audit does not install or accept it.',
       'Slash/list variants are tested separately. They may be separate commands or alternative bindings; no action-coverage ratio follows.',
       'One modeled output per finger; little finger is reserved for a held secondary-layer selector after recognition.',
       'Mouse inputs are delegated to the other hand and not physically tested.',
       'Explicit WASD directions share the movement thumb. A WASD nonmovement command is flagged separately.',
       'Left/right modifier requirements retain their exact labels but routing uses logical modifier names pending native-output verification.',
       'Additional movement is an analyst stress test, not a claim that every command requires continuous movement.',
       'Raw urgency/gesture/source metadata is inherited, not new telemetry or a complete source recheck.',
       'No carry-over of a held output across layers is assumed; transition behavior is unknown.',
       'Presence of a listed variant is not sufficient to conclude that a game is playable or comfortable.'
      ],summary=dict(games=len(games),rows=len(rows),syntax_status=dict(counts),listed_variants=sum(route_counts.values()),
                     variant_routes=dict(route_counts)),games=sorted(games,key=lambda r:r['game'].casefold()),records=results)

def self_test() -> int:
    cases=[('Ctrl+1',[['Ctrl','1']]),('Ctrl+F1–F3',[['Ctrl','F1'],['Ctrl','F2'],['Ctrl','F3']]),
      ('C/V/Shift+C',[['C'],['V'],['Shift','C']]),('Numpad +',[['Numpad +']]),
      ('Numpad + / Numpad -',[['Numpad +'],['Numpad -']]),
      ('Numpad 8/2/4/6',[['Numpad 8'],['Numpad 2'],['Numpad 4'],['Numpad 6']]),
      ('C + Mouse Wheel Up/Down',[['C','Mouse Wheel Up'],['C','Mouse Wheel Down']]),
      ('E + arrow keys',[['E',k] for k in ARROWS]),('/',[['Slash']]),
      ('1–9, 0, -, =',[[str(i)] for i in range(1,10)]+[['0'],['Minus'],['Equals']]),
      ('Shift+A',[['Shift','A']]),('A',[['A']]),('Pause/Break',[['Pause']])]
    for raw,expected in cases:
        got=alternatives(raw)
        assert got['status']=='PARSED' and got['variants']==expected,(raw,got,expected)
    for raw in ['Shift + command','Ctrl+number','Right Ctrl + [ / ]','Ctrl + 1–0','Alt + G then LMB']:
        assert alternatives(raw)['status']=='MANUAL_REVIEW',raw
    return len(cases)+5

def main() -> None:
    ap=argparse.ArgumentParser();ap.add_argument('--corpus-html',type=Path,required=True)
    ap.add_argument('--layout',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    checks=self_test();report=run(args.corpus_html,args.layout,args.out)
    report['parser_unit_cases']=checks
    (args.out/'CORPUS_AUDIT_R4.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    compact={k:v for k,v in report.items() if k!='records'}
    (args.out/'SUMMARY_R4.json').write_text(json.dumps(compact,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['summary'],indent=2));print('Parser unit cases:',checks)
if __name__=='__main__':main()
