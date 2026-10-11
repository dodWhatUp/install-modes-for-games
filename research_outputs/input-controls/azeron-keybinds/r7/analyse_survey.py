#!/usr/bin/env python3
"""Reproducible descriptive audit; no input, runtime telemetry or native edits.
The sample is inherited and uneven. Jaccard measures observed output vocabulary,
NOT action identity, completeness, comfort, urgency or effective user settings.
"""
import argparse, collections, hashlib, itertools, json, re, statistics
from pathlib import Path

def logical(k):
    return re.sub(r'^(Left|Right) (Ctrl|Shift|Alt)$',r'\2',k)

def classify(row):
    # Discovery tags only. Never promoted to accepted overlay categories by this function.
    t=(row['action']+' '+row['context']).lower()
    if re.search(r'chat|push.to.talk|marker|ping|communication|emote',t):return 'communication'
    if re.search(r'camera|zoom|focus|scan|tracker|instinct|vision|flashlight|reconnaissance',t):return 'camera_information'
    if re.search(r'menu|inventory|journal|map|panel|quest|character screen|skill tree|ui\b',t):return 'menus_navigation'
    if re.search(r'weapon|reload|ammo|sheath|holster|revolver|shotgun|rifle|bow|melee swap',t):return 'weapons'
    if re.search(r'move|sprint|jump|crouch|walk|sneak|dodge|evade|swim|roll|steer|throttle|brake',t):return 'movement_defence'
    if re.search(r'interact|activate|use\b|item|flask|heal|craft|loot|context action',t):return 'interaction_items'
    if re.search(r'attack|skill|ability|spell|guard|parry|deflect|combat|power|rage',t):return 'combat_abilities'
    return 'review_other'

def analyse(inp,out):
    raw=inp.read_bytes();data=json.loads(raw);records=data['records']
    games=collections.defaultdict(list)
    for r in records:games[r['row']['game']].append(r)
    sets={}; family={}; rows=[]
    for g,rs in games.items():
        keys={logical(k) for r in rs for v in r['variants'] for k in v['keys'] if not k.startswith('Mouse ')}
        sets[g]=keys;family[g]=rs[0]['row']['family']
        rows.append({'game':g,'family':family[g],'row_count':len(rs),'keyboard_output_vocabulary':sorted(keys),
          'unparsed_rows':sum(r['syntax']['status']!='PARSED' for r in rs),
          'source_urls':sorted({r['row']['source_url'] for r in rs}),
          'discovery_category_counts':dict(collections.Counter(classify(r['row']) for r in rs))})
    pairs=[]
    for a,b in itertools.combinations(games,2):
        u=sets[a]|sets[b];inter=sets[a]&sets[b]
        pairs.append({'a':a,'b':b,'a_family':family[a],'b_family':family[b],'shared_keys':len(inter),'union_keys':len(u),
                      'jaccard':round(len(inter)/len(u),6) if u else None})
    byfamily=[]
    for f in sorted(set(family.values())):
        members=[g for g in games if family[g]==f];counter=collections.Counter(k for g in members for k in sets[g])
        byfamily.append({'family':f,'games':len(members),'rows':sum(len(games[g]) for g in members),
          'keys_by_game_presence':[{'key':k,'games_mentioning':n,'denominator':len(members)} for k,n in counter.most_common()],
          'median_rows_per_game':statistics.median(len(games[g]) for g in members)})
    overall=collections.Counter(k for s in sets.values() for k in s)
    selected_pairs=[]
    picks=[('Warframe','Tomb Raider (2013)'),('Tomb Raider (2013)','Shadow of the Tomb Raider: Definitive Edition'),
       ('Alien: Isolation','Tomb Raider (2013)'),('The Elder Scrolls V: Skyrim (original PC)','Cyberpunk 2077 (legacy controls)'),
       ('XCOM 2','OpenTTD'),('FAIRY TAIL 2','Warframe'),('Guild Wars 2','Warframe')]
    for a,b in picks:
        p=next(p for p in pairs if {p['a'],p['b']}=={a,b});selected_pairs.append(p)
    result={'revision':'R7','status':'DESCRIPTIVE_SAMPLE_AUDIT_NOT_OPTIMALITY_PROOF','input_sha256':hashlib.sha256(raw).hexdigest(),
       'game_records':len(games),'binding_rows':len(records),'genre_labels':len(byfamily),'pair_comparisons':len(pairs),
       'unparsed_rows':sum(r['syntax']['status']!='PARSED' for r in records),
       'median_rows_per_game':statistics.median(len(v) for v in games.values()),
       'families':byfamily,'overall_key_presence':[{'key':k,'games_mentioning':n,'denominator':len(games)} for k,n in overall.most_common()],
       'selected_pairs':selected_pairs,'games':rows,
       'limits':['Old/manual/port/preset qualifications remain. No complete-source recheck is implied.',
         'Each game counts once per key; a slash is not automatically one interchangeable action.',
         'No observed press-frequency or usage-time weighting exists.',
         'Logical modifiers merge left/right for vocabulary only, not native mapping.',
         'Sparse/incomplete source tables make absent keys UNKNOWN rather than unsupported.',
         'Discovery categories are keyword heuristics, not verified game-action icons.',
         'Similarity of key sets does not establish action-semantic or simultaneous-access similarity.']}
    out.mkdir(parents=True,exist_ok=True)
    (out/'SURVEY_R7.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (out/'KEY_VOCABULARY_PAIRS_R7.json').write_text(json.dumps({'limits':result['limits'],'pairs':pairs},ensure_ascii=False,indent=2)+'\n')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=analyse(a.input,a.output);print(json.dumps({k:r[k] for k in ['game_records','binding_rows','genre_labels','pair_comparisons','median_rows_per_game','selected_pairs']},ensure_ascii=False,indent=2))
