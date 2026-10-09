#!/usr/bin/env python3
"""Consolidate source-backed game controls; infer no usage telemetry.

Only top-level games are counted. Raw research schemas are preserved alongside
normalized records, except privacy metadata explicitly listed in the audit log.
Run: python research/normalize_bindings.py [--input-dir research]
"""
import argparse
import collections
import hashlib
import json
import re
import unicodedata
from pathlib import Path

INPUT_NAMES = ['action_games.json', 'rpg_survival_games.json',
               'strategy_sim_games.json', 'action_modern_additions.json']

def uid(prefix, value):
    return prefix + '_' + hashlib.sha256(value.encode('utf-8')).hexdigest()[:12]

def genre_family(game):
    title = game['game'].lower()
    genre = game.get('genre', '').lower()
    sub = game.get('subgenre', '').lower()
    if 'mmorpg' in genre + ' ' + sub:
        return 'MMORPG'
    if genre == 'shooter':
        return 'Shooter'
    if genre in ['survival', 'sandbox'] or title == 'minecraft education':
        return 'Survival & sandbox'
    if genre == 'strategy':
        return 'Strategy, tactics & MOBA'
    if genre == 'simulation':
        if any(x in sub for x in ['flight', 'driving', 'vehicle physics']):
            return 'Driving & flight simulation'
        return 'Building & management'
    if 'rpg' in genre:
        return 'RPG & action RPG'
    return 'Action & adventure'

def evidence_family(raw):
    tier = raw.get('evidence_tier', '').lower()
    if tier == 'primary' or tier.startswith('publisher/developer'):
        return 'Publisher/developer documentation'
    if 'project-maintained' in tier:
        return 'Project documentation'
    if 'third' in tier or 'independent reported' in tier:
        return 'Independent observed/reported controls'
    if 'community' in tier or 'official-hosted' in tier:
        return 'Community documentation'
    return 'Other explicitly qualified evidence'

ALIASES = {}
def aliases(canonical, *forms):
    for form in (canonical,) + forms:
        ALIASES[form.lower()] = canonical

for c, forms in {
    'Ctrl':['Control','CTRL'], 'Left Ctrl':['Left Control'],
    'Right Ctrl':['Right Control'], 'Shift':[], 'Left Shift':[],
    'Right Shift':[], 'Alt':[], 'Left Alt':[], 'Right Alt':[],
    'Esc':['Escape'], 'Space':['Spacebar'], 'Enter':['Return'],
    'Tab':[], 'Backspace':[], 'Delete':['Del'], 'Insert':['Ins'],
    'Home':[], 'End':[], 'Page Up':['PageUp','PgUp'],
    'Page Down':['PageDown','PgDown'], 'Caps Lock':['CapsLock'],
    'Num Lock':['NumLock'], 'Scroll Lock':['ScrollLock'],
    'Pause':['Pause/Break'], 'Up Arrow':['Up','Arrow Up'],
    'Down Arrow':['Down','Arrow Down'], 'Left Arrow':['Left','Arrow Left'],
    'Right Arrow':['Right','Arrow Right'], 'Comma':[','], 'Period':['.'],
    'Slash':['/'], 'Minus':['-'], 'Equals':['='], 'Plus':['+'],
    'Left Bracket':['['], 'Right Bracket':[']'],
    'Backtick':['`','Grave'], 'Tilde':['~'], 'Underscore':['_'],
    'Question Mark':['?'],
    'Mouse Left':['LMB','Mouse1','Left mouse','Left mouse button'],
    'Mouse Right':['RMB','Mouse2','Right mouse','Right mouse button'],
    'Mouse Middle':['MMB','MOUSE3','Middle mouse','Middle mouse button','Mouse wheel button'],
    'Mouse Button 4':[], 'Mouse Button 5':[], 'Mouse Wheel':[],
    'Mouse Wheel Up':['Wheel up'], 'Mouse Wheel Down':['Wheel down'],
    'Mouse Movement':['mouse move'],
}.items(): aliases(c, *forms)

def token_key(token):
    token = re.sub(r'\s+', ' ', token.strip())
    if token.lower() in ALIASES:
        return ALIASES[token.lower()]
    if re.fullmatch(r'[a-zA-Z0-9]', token):
        return token.upper()
    if re.fullmatch(r'F(?:[1-9]|1[0-9]|2[0-4])', token, re.I):
        return token.upper()
    if re.fullmatch(r'Numpad (?:[0-9]|[+*/.\-]|Enter)', token, re.I):
        return 'Numpad ' + token[7:].title()
    return None

def physical_alias(key):
    if re.fullmatch(r'(Left|Right) (Shift|Ctrl|Alt)', key):
        return key.split(' ', 1)[1]
    return key

def parse_expression(raw, action=''):
    """Extract documented constituent keys, not a reconstructed executable bind.

    Explicit ascending digit/F-key ranges expand. Contextual top-row 1–0 slot
    or control-group ranges expand; other 1–0 notation remains ambiguous. Unspecified
    number, unspecified click/command and unknown locale glyphs remain logged.
    Chord modifier inheritance is intentionally not reconstructed.
    """
    original = str(raw).strip()
    expr = original
    issues, transformations = [], []
    keys = set()
    # Protect standalone symbol keys and alias terms containing separators.
    if token_key(expr):
        keys.add(token_key(expr))
        return result(keys, issues, transformations, original)
    expr = re.sub(r'Pause/Break', 'Pause', expr, flags=re.I)
    expr = re.sub(r'Mouse Wheel Up\s*/\s*(?:Mouse Wheel )?Down',
                  'Mouse Wheel Up ; Mouse Wheel Down', expr, flags=re.I)
    # A single explicit Numpad prefix scopes a contiguous digit list.
    def numpad_list(match):
        digits = re.findall(r'\d', match.group(0))
        transformations.append('Expanded an explicit Numpad digit list; digits remain numpad keys.')
        return ' ; '.join('Numpad ' + x for x in digits)
    expr = re.sub(r'Numpad\s+[0-9](?:\s*/\s*[0-9])+(?![0-9])', numpad_list, expr, flags=re.I)
    # Remove repetition words while preserving the original expression.
    expr = re.sub(r'\s+twice\b', '', expr, flags=re.I)
    for term in re.split(r'\s+(?:then|or)\s+|\s*;\s*|\s*/\s*', expr, flags=re.I):
        # Comma serves as a separator only in digit range/list notation.
        terms = re.split(r',\s+', term) if re.search(r'\d,\s', term) else [term]
        for part in terms:
            # A literal + alone is a symbol, not an empty chord.
            atoms = [part] if part.strip() == '+' or part.strip().lower() == 'numpad +' else re.split(r'\s*\+\s*', part)
            for atom in atoms:
                atom = atom.strip()
                if not atom:
                    continue
                if atom.lower() in ['arrow keys','arrows']:
                    keys.update(['Up Arrow','Down Arrow','Left Arrow','Right Arrow'])
                    transformations.append('Expanded explicitly named arrow-key group.')
                    continue
                rg = re.fullmatch(r'(F?)(\d+)\s*[–—-]\s*(F?)(\d+)', atom, re.I)
                if rg:
                    a, b = int(rg[2]), int(rg[4])
                    fa, fb = rg[1].upper(), rg[3].upper()
                    explicit_slot_or_group = re.search(r'(?:ability|toolbar|hotbar|item|weapon|number)\s+slots|(?:assign|select|control)\s+group', action, re.I)
                    if a == 1 and b == 0 and not fa and not fb and explicit_slot_or_group:
                        keys.update(str(i) for i in range(10))
                        transformations.append('Expanded 1–0 as the ten top-row digits because the documented action explicitly identifies numbered slots or assign/select/control groups: ' + action)
                    elif a <= b and ((not fa and not fb and b <= 9) or (fa == 'F' and fb in ['', 'F'] and a >= 1 and b <= 24)):
                        keys.update(fa + str(i) for i in range(a, b+1))
                        transformations.append('Expanded explicit ascending range: ' + atom)
                    else:
                        issues.append({'expression_part':atom,'reason':'Descending/cross-row range or unclear range type; no keys inferred.'})
                    continue
                k = token_key(atom)
                if k:
                    keys.add(k)
                else:
                    issues.append({'expression_part':atom,'reason':'Unspecified input, layout-dependent unknown token, or unsupported syntax; no key inferred.'})
    return result(keys, issues, transformations, original)

def result(keys, issues, transformations, original):
    keyboard = sorted(k for k in keys if not k.startswith('Mouse '))
    mouse = sorted(k for k in keys if k.startswith('Mouse '))
    return {'status':'partial' if issues and keys else 'unparsed' if issues else 'fully_parsed',
            'keyboard_keys_exact':keyboard, 'keyboard_physical_aliases':sorted(set(map(physical_alias, keyboard))),
            'mouse_inputs':mouse, 'issues':issues, 'transformations':sorted(set(transformations)),
            'semantics':'Constituent-key presence only; original chord/sequence/range expression is preserved separately.'}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-dir', type=Path, default=Path(__file__).resolve().parent)
    args = ap.parse_args()
    source_map, sources, games, bindings, docs = {}, [], [], [], []
    privacy_redactions, parsing_issues = [], []
    def sanitize(x, path):
        if isinstance(x, dict):
            out = {}
            for k,v in x.items():
                if k.lower() in ['timezone','user_id','account_id','private_context','screenshot_content']:
                    privacy_redactions.append({'path':path+'/'+k,'reason':'Private/context metadata excluded from public consolidation.'})
                else:
                    out[k] = sanitize(v, path+'/'+k)
            return out
        if isinstance(x,list): return [sanitize(v,path+'/'+str(i)) for i,v in enumerate(x)]
        return x
    def source_id(url):
        url = str(url).strip()
        if not url: return None
        if url not in source_map:
            sid=uid('src',url)
            source_map[url]=sid
            sources.append({'source_id':sid,'url':url})
        return source_map[url]
    for name in INPUT_NAMES:
        data=sanitize(json.loads((args.input_dir/name).read_text(encoding='utf-8')),name)
        iid=uid('input',name)
        doc={'input_id':iid,'filename':name,'raw_document_metadata':{k:v for k,v in data.items() if k!='games'},'main_game_ids':[]}
        docs.append(doc)
        for raw in data['games']:
            title=raw['game']
            gid=uid('game',unicodedata.normalize('NFKC',title).casefold())
            if any(g['game_id']==gid for g in games): raise ValueError('Duplicate main game: '+title)
            doc['main_game_ids'].append(gid)
            g={'game_id':gid,'title':title,'genre_family':genre_family(raw),'evidence_family':evidence_family(raw),
               'input_id':iid,'source_ids':sorted(set(filter(None,(source_id(u) for u in raw.get('source_urls',[]))))),
               'raw_metadata':{k:v for k,v in raw.items() if k!='bindings'},'binding_ids':[]}
            games.append(g)
            occurrences=collections.Counter()
            for rb in raw['bindings']:
                signature=json.dumps({k:rb.get(k) for k in ['action','key','context','source_url']},sort_keys=True,ensure_ascii=False)
                occurrences[signature]+=1
                bid=uid('binding',gid+'|'+signature+'|'+str(occurrences[signature]))
                parsed=parse_expression(rb['key'],rb.get('action',''))
                sid=source_id(rb.get('source_url',''))
                b={'binding_id':bid,'game_id':gid,'source_id':sid,
                   'observed':{'action':rb.get('action'),'key_expression':rb.get('key'),'context':rb.get('context'),'source_url':rb.get('source_url')},
                   'analyst_classification':{'urgency_raw':rb.get('urgency'),'held_or_repeat_raw':rb.get('held_or_repeat'),
                       'note':'Urgency is analyst judgement, not measured usage. Held/repeat is interpreted unless explicitly documented in raw notes.'},
                   'parsed_key_presence':parsed,'raw_binding':rb}
                bindings.append(b);g['binding_ids'].append(bid)
                if parsed['issues']: parsing_issues.append({'binding_id':bid,'game_id':gid,'game':title,'raw_expression':rb['key'],'issues':parsed['issues']})
    # Count distinct game+key, regardless of how many actions mention it.
    exact=collections.defaultdict(set); mouse=collections.defaultdict(set)
    for b in bindings:
        for k in b['parsed_key_presence']['keyboard_keys_exact']: exact[(b['game_id'],k)].add(b['binding_id'])
        for k in b['parsed_key_presence']['mouse_inputs']: mouse[(b['game_id'],k)].add(b['binding_id'])
    presence=[{'game_id':g,'keyboard_key':k,'physical_alias':physical_alias(k),'binding_ids':sorted(ids)} for (g,k),ids in sorted(exact.items())]
    mouse_presence=[{'game_id':g,'mouse_input':k,'binding_ids':sorted(ids)} for (g,k),ids in sorted(mouse.items())]
    alias_games=collections.defaultdict(set)
    for row in presence: alias_games[row['physical_alias']].add(row['game_id'])
    exact_counts=collections.Counter(k for g,k in exact)
    summary={'main_game_or_scoped_edition_records':len(games),'main_binding_rows':len(bindings),'distinct_source_urls':len(sources),
      'excluded_candidate_records':sum(len(d['raw_document_metadata'].get('candidates_not_verified',[])) for d in docs),
      'game_counts_by_genre_family':dict(sorted(collections.Counter(g['genre_family'] for g in games).items())),
      'game_counts_by_evidence_family':dict(sorted(collections.Counter(g['evidence_family'] for g in games).items())),
      'binding_rows_by_genre_family':dict(sorted(collections.Counter(next(g['genre_family'] for g in games if g['game_id']==b['game_id']) for b in bindings).items())),
      'parser_status_counts':dict(collections.Counter(b['parsed_key_presence']['status'] for b in bindings)),
      'distinct_game_keyboard_key_pairs':len(presence),'distinct_game_mouse_input_pairs':len(mouse_presence),
      'keyboard_keys_exact_count':len(exact_counts),'keyboard_physical_alias_count':len(alias_games),
      'top_documented_keyboard_presence':[{'key':k,'game_count':len(gs)} for k,gs in sorted(alias_games.items(),key=lambda x:(-len(x[1]),x[0]))],
      'exact_keyboard_presence_counts':[{'key':k,'game_count':n} for k,n in sorted(exact_counts.items(),key=lambda x:(-x[1],x[0]))]}
    method={'count_unit':'Distinct named game/scoped edition record. Historical layouts and variants retain their explicit qualifiers; these are not 74 independently current installations.',
      'presence_not_frequency':'Presence is the number of sampled game records with a documented key, including modifiers within chords and keys within sequences. It is not press frequency, urgency, market prevalence, or player telemetry.',
      'parser':'Only explicit constituent keys are aggregated. Ascending numeric/function ranges and explicit arrow/numpad groups may expand. Top-row 1–0 notation expands to ten digits only when the action explicitly identifies numbered ability/toolbar/hotbar/item/weapon slots or assigned/selected/control groups. Other 1–0 notation, unspecified numbers, unknown tokens and incomplete expressions are logged without invented keys.',
      'physical_aliases':'Left/right Ctrl, Shift and Alt retain exact variants, with a common aggregate alias. Numpad keys remain distinct from top-row digits. Symbol keys are not mapped to assumed US-layout physical keys.',
      'raw_preservation':'Original document metadata, game metadata and binding rows are preserved. Private timezone/context fields are excluded and logged. Rejected original entries are retained only as excluded candidate audit trails.',
      'source_deduplication':'Exact URL strings after whitespace trimming; no speculative equivalence across mirrors, query strings or fragments.',
      'ids':'Stable hash-based game IDs from normalized title; source IDs from exact URL; binding IDs from game ID and observed action/key/context/source content with occurrence suffix for duplicates. Analyst urgency edits do not change binding IDs.',
      'privacy_scope':'Only the four named public research JSON documents are read. context.json, uploaded images, account data and personal context are not inputs.'}
    out={'schema_version':'1.0','methodology':method,'summary':summary,'input_documents':docs,'sources':sorted(sources,key=lambda x:x['source_id']),
         'games':games,'bindings':bindings,'keyboard_key_presence':presence,'mouse_input_presence':mouse_presence}
    notes={'schema_version':'1.0','summary':summary,'methodology':method,'privacy_redactions':privacy_redactions,
           'ambiguous_or_partial_expressions':parsing_issues,'genre_assignments':[{'game_id':g['game_id'],'title':g['title'],'genre_family':g['genre_family']} for g in games],
           'quality_gates':{'expected_game_records':74,'expected_binding_rows_at_request':1747,'actual_game_records':len(games),'actual_binding_rows':len(bindings),
                            'main_only':True,'rejected_original_entries_counted':False}}
    for filename,document in [('consolidated.json',out),('normalization_notes.json',notes)]:
        (args.input_dir/filename).write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
