#!/usr/bin/env python3
"""Build the research master, portable catalogue view, and readable report.

AI_MASTER.json is the editable research source after initial collection.
The report and catalogue view are generated derivatives.
"""
import argparse
import collections
import datetime
import html
import json
from pathlib import Path


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def make_master(d):
    games = {g['game_id']: g for g in d['games']}
    source_games = collections.defaultdict(list)
    for g in d['games']:
        for sid in g['source_ids']:
            source_games[sid].append(g)
    used_sources = {b['source_id'] for b in d['bindings']}
    sources = []
    for s in d['sources']:
        linked = source_games[s['source_id']]
        families = sorted({g['evidence_family'] for g in linked})
        family = families[0] if families else 'Unknown'
        typ = ('PRIMARY' if any(x in family for x in ['Publisher', 'Project'])
               else 'COMMUNITY' if 'Community' in family else 'PROFESSIONAL')
        sources.append({
            **s, 'locator': 'Keyboard / controls section; see associated game scope notes',
            'source_type': typ, 'accessed_at': '2026-10-09', 'published_at': None,
            'lineage_id': s['source_id'], 'sponsorship': 'UNKNOWN',
            'access_status': 'UNAVAILABLE' if s['url'].endswith('/performance/hotkeys-keybindings-faq') else 'EXCERPT',
            'extensions': {'evidence_families': families,
                           'supports_included_binding': s['source_id'] in used_sources,
                           'game_ids': [g['game_id'] for g in linked],
                           'note': 'Published dates and exact platform/version limitations are retained in the associated game metadata. Access describes the extracted evidence, not current installation verification.'}
        })
    candidates = []
    for g in d['games']:
        meta = g['raw_metadata']
        candidates.append({
            'candidate_id': g['game_id'], 'name': g['title'], 'category': g['genre_family'],
            'variant': meta.get('platform_scope', meta.get('subgenre', 'See evidence note')),
            'eligibility': 'ELIGIBLE', 'analysis_depth': 'LIGHT',
            'reason': 'Included as a source-documented control sample; completeness and current installed defaults are not established.',
            'extensions': {k: v for k, v in g.items() if k not in ['game_id', 'title', 'genre_family']}
        })
    observations = []
    for b in d['bindings']:
        observations.append({
            'observation_id': b['binding_id'], 'candidate_id': b['game_id'],
            'attribute': 'documented_control_binding', 'raw_value': b['raw_binding'],
            'raw_unit': None, 'value': b['parsed_key_presence'], 'unit': 'keyboard/mouse constituents',
            'value_state': 'KNOWN', 'source_id': b['source_id'],
            'locator': b['observed']['action'], 'kind': 'FACT_REPORTED',
            'extensions': {'analyst_classification': b['analyst_classification']}
        })
    support = {k: v for k, v in d.items() if k not in ['games', 'bindings', 'sources', 'schema_version']}
    return {
        'meta': {'schema_version': '1.0.0', 'research_id': 'azeron-cyborg-ii-keybinds-step1-2026-10',
                 'version': '1.0', 'stage': 'PREPRO_FACTS', 'status': 'READY_FOR_JUDGMENT',
                 'scope': 'Representative cross-genre keyboard-control catalogue and requirements for a small shared layer family. This is not an exhaustive catalogue, a current-installation audit, or an importable device configuration.',
                 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'supersedes': None},
        'context': [{'device_family': 'Azeron Cyborg II', 'software_family': 'Azeron Software v2',
                     'design_priorities': ['Few shared maps', 'Mnemonic keyboard-key families', 'Slow layers mainly for deliberate inputs', 'Immediate access for urgent or continuously held actions', 'Game-specific variants only when the access requirements justify them'],
                     'evidence_boundary': 'Urgency and repetition classifications are analyst interpretations. No measured keypress frequencies or physical comfort tests are available.'}],
        'candidates': candidates, 'sources': sources, 'observations': observations,
        'coverage': {'found_ids': list(games),
                     'missing_areas': ['Full current control tables for every sampled title', 'Exact selected in-game presets', 'Physical button reach and simultaneous access', 'Software v2 timing and held-input transition behavior', 'Complete specialist flight/simulation command coverage'],
                     'reconsideration_ids': [],
                     'scope_note': '74 game/edition/layout records. Historical manuals, port documentation, and partial observed guides retain their qualifiers. Candidate-attempt records can overlap; they must not be counted as additional verified games.'},
        'dependencies': {'method_schema': 'research-decision-ai-os/schemas/master.schema.json',
                         'method_snapshot': '57b12ccf2ac0aac21d40490c734164c22f39249f'},
        'extensions': {'catalogue_support': support,
                       'recommended_start': {'logical_map_families': 1, 'conceptual_layers': 4,
                                             'status': 'Provisional architecture; not a proven minimum or a native configuration',
                                             'layers': ['Base / immediate inputs', 'Numbers / indexed inputs', 'Letters / deliberate panels', 'Function keys / navigation / tools'],
                                             'conditional_base_variants': ['Hotbar', 'RTS command grid', 'Specialist simulation only if necessary']}}
    }


def catalogue_from_master(m):
    games = []
    for c in m['candidates']:
        games.append({'game_id': c['candidate_id'], 'title': c['name'], 'genre_family': c['category'], **c['extensions']})
    bindings = []
    for o in m['observations']:
        rb = o['raw_value']
        bindings.append({'binding_id': o['observation_id'], 'game_id': o['candidate_id'], 'source_id': o['source_id'],
                         'observed': {'action': rb.get('action'), 'key_expression': rb.get('key'), 'context': rb.get('context'), 'source_url': rb.get('source_url')},
                         'analyst_classification': o['extensions']['analyst_classification'],
                         'parsed_key_presence': o['value'], 'raw_binding': rb})
    return {'schema_version': '1.0', **m['extensions']['catalogue_support'], 'games': games, 'bindings': bindings,
            'sources': [{'source_id': s['source_id'], 'url': s['url']} for s in m['sources']]}


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th>' + h + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + str(c) + '</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def write_report(d, path, profile=None):
    esc = html.escape
    summary = d['summary']
    games = sorted(d['games'], key=lambda g: (g['genre_family'], g['title'].casefold()))
    by_id = {g['game_id']: g for g in games}
    group_rows = [[esc(k), n, summary['binding_rows_by_genre_family'][k], esc('; '.join(g['title'] for g in games if g['genre_family'] == k))] for k, n in summary['game_counts_by_genre_family'].items()]
    presence_rows = [[esc(r['key']), r['game_count']] for r in summary['top_documented_keyboard_presence'][:30]]
    game_cards = []
    for g in games:
        meta = g['raw_metadata']
        links = ' · '.join('<a href="' + esc(u, quote=True) + '">Source ' + str(i + 1) + '</a>' for i, u in enumerate(meta.get('source_urls', [])))
        note = meta.get('evidence_note', '')
        if not isinstance(note, str): note = json.dumps(note, ensure_ascii=False)
        game_cards.append('<details class="game"><summary>' + esc(g['title']) + '<span>' + str(len(g['binding_ids'])) + ' entries · ' + esc(g['evidence_family']) + '</span></summary><p><b>' + esc(g['genre_family']) + '</b> · ' + esc(meta.get('subgenre', '')) + '</p><p>' + esc(meta.get('platform_scope', meta.get('coverage', 'See scope note below'))) + '</p><p>' + esc(note) + '</p><p>' + links + '</p></details>')
    bindings = []
    for b in d['bindings']:
        g = by_id[b['game_id']]
        rb = b['raw_binding']
        bindings.append({'game': g['title'], 'genre': g['genre_family'], 'action': rb.get('action', ''),
                         'key': rb.get('key', ''), 'context': rb.get('context', ''), 'urgency': rb.get('urgency', ''),
                         'hold': rb.get('held_or_repeat', ''), 'note': rb.get('notes', ''), 'source': rb.get('source_url', ''),
                         'evidence': g['evidence_family'], 'keys': b['parsed_key_presence']['keyboard_keys_exact']})
    layer_rows = [
        ['Base', 'Movement, raw modifiers, immediate action keys, urgent number-key duplicates', 'Use the easiest positions for short-deadline actions and keys held with movement or aim.'],
        ['Numbers', '1–9, 0, minus, equals; indexed selection', 'A coherent full numeric bank. Duplicate the most urgent numbers on Base; never assume numbers are slow.'],
        ['Letters / panels', 'Remaining letters and deliberate menu commands; Enter and Backspace', 'Keep related letter groups stable. A letter can still be combat-critical in a particular game.'],
        ['Functions / navigation', 'F1–F12; Home, End, Insert, Delete, Page Up/Down; arrows and needed punctuation', 'Organize predictable families. Move urgent F-key or arrow actions to an immediate route when needed.']
    ]
    evidence_rows = [
        ['Warframe', 'E melee; X interaction; F weapon switching; 1–4 abilities', 'Key categories are reusable; the same printed key does not promise the same action in every game.', 'https://www.warframe.com/en/game/quickstart'],
        ['Guild Wars 2', '6 healing; 1–5 weapon skills; F1–F4 illustrated profession actions', 'Some numbers and function keys deserve immediate access.', 'https://www.guildwars2.com/en/new-player-guide/'],
        ['Final Fantasy XIV', 'F2–F8 party targets; F10 focus; F11 nearest enemy', 'Function keys are not inherently administrative. Target selection can be urgent.', 'https://na.finalfantasyxiv.com/game_manual/operation/'],
        ['Shadow of the Tomb Raider', 'F1–F4 held for plant consumables, including healing', 'A function-key layer needs exceptions for combat and sustained presses. Source is the Feral Linux manual.', 'https://www.feralinteractive.com/en/manuals/shadowofthetombraider/latest/linux/'],
        ['Alien: Isolation', 'V held with WASD for peeking; Space held for tracker', 'Plan simultaneous access. Space is not universally jump. Source is the Feral Mac manual.', 'https://www.feralinteractive.com/en/manuals/alienisolation/latest/steam/'],
        ['Age of Empires II: DE', 'Grid command keys; Ctrl plus a number assigns a group', 'RTS command grids and control groups require a different base-access pattern.', 'https://www.ageofempires.com/learn-to-play/match-goals-aoe2/'],
        ['League of Legends', 'Optional WASD scheme: Shift ability 2; E ability 3; R ultimate', 'Selected input scheme changes the required keys; Point & Click remains the default in the May 2026 official FAQ.', 'https://support.riotgames.com/en-us/league-of-legends/gameplay/league-of-legends-keyboard-wasd-input-faq'],
        ['Elden Ring', 'E plus mouse / arrow chords; arrow selectors', 'An input family that looks like navigation can be part of combat. Exact timing is not established by this observed guide.', 'https://www.shacknews.com/article/128968/elden-ring-controls-and-pc-keybindings']
    ]
    evidence_table = table(['Game / documented example', 'Keys', 'Layer implication'], [[ '<a href="'+esc(u,quote=True)+'">'+esc(g)+'</a>',esc(k),esc(i)] for g,k,i,u in evidence_rows])
    profile_html = ''
    if profile:
        profile_html = '<section id="current"><h2>Reading your current four layers</h2>' + ''.join('<p>'+esc(p)+'</p>' for p in profile['paragraphs']) + '</section>'
    payload = json.dumps(bindings, ensure_ascii=False).replace('<', '\\u003c')
    report = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Azeron Cyborg II — Step 1 research</title><style>
    :root{--ink:#172331;--muted:#526477;--line:#d8e0e8;--accent:#2d5187;--paper:#fff;--wash:#f2f5f9;--amber:#fff4d8}*{box-sizing:border-box}body{margin:0;background:var(--wash);font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:var(--ink);line-height:1.6}header{background:#162b46;color:#fff;padding:48px max(24px,calc((100vw - 1240px)/2)) 36px}header p{max-width:880px;color:#d5e2ef}h1{font-size:clamp(30px,4vw,46px);line-height:1.15;margin:10px 0 18px}h2{font-size:26px;margin:0 0 20px;line-height:1.25}h3{font-size:19px;margin:28px 0 10px}.eyebrow{font-size:12px;letter-spacing:.12em;font-weight:700;text-transform:uppercase}.tag{display:inline-block;border:1px solid #6f89a7;padding:3px 10px;border-radius:16px;font-size:12px;margin:2px 8px 0 0}nav{position:sticky;top:0;background:#fff;border-bottom:1px solid var(--line);padding:12px 24px;display:flex;gap:20px;flex-wrap:wrap;z-index:5;font-size:14px}nav a{text-decoration:none;color:var(--accent);font-weight:650}main{max-width:1288px;margin:auto;padding:30px 24px 60px}section{background:var(--paper);border:1px solid var(--line);border-radius:12px;margin:0 0 24px;padding:30px;scroll-margin-top:100px}p{margin:0 0 16px}a{color:#254f89}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:0 0 28px}.stat{border-left:3px solid var(--accent);padding:5px 16px}.stat b{font-size:30px;display:block;line-height:1.3}.stat span{font-size:13px;color:var(--muted)}.callout{background:#edf3fc;border-left:4px solid #3d659c;padding:18px 20px;margin:20px 0}.caution{background:var(--amber);border-color:#b08932}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:7px;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:14px}th{text-align:left;background:#e9eff6;color:#263f60;font-weight:650}td,th{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:top}tr:last-child td{border-bottom:0}tbody tr:nth-child(even){background:#f8fafc}td:first-child{font-weight:600}code{font-family:ui-monospace,Consolas,monospace;background:#eaf0f6;padding:2px 5px;border-radius:3px}li{margin:7px 0}.two{display:grid;grid-template-columns:1fr 1fr;gap:30px}.game{border-top:1px solid var(--line);padding:12px 0}.game summary{font-weight:650;cursor:pointer}.game summary span{display:block;margin-left:18px;font-size:12px;color:var(--muted);font-weight:400}.game p{font-size:14px;margin:12px 18px}.filters{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin:16px 0}input,select,button{font:inherit;font-size:14px;border:1px solid #aebdce;border-radius:5px;padding:10px 12px;background:white;color:var(--ink)}input{min-width:230px;flex:1}button{cursor:pointer;background:#e9eff8}#binding-table{min-width:1100px}#binding-table td:nth-child(3){font-family:ui-monospace,Consolas,monospace;font-weight:650}small,.muted{color:var(--muted)}footer{padding:0 12px;color:var(--muted);font-size:13px} @media(max-width:700px){.two{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}section{padding:20px}nav{gap:14px}main{padding:20px 12px}}@media print{nav,.filters,button{display:none}header{background:#fff;color:#172331;padding:12px}header p{color:#526477}section{break-inside:avoid;border:0;padding:12px;margin:0}body{background:white}main{padding:0}.game{break-inside:avoid}.table-wrap{overflow:visible}a{color:inherit}#catalogue{break-before:page}}
    </style></head><body><header><div class="eyebrow">Research snapshot · October 2026</div><h1>Azeron Cyborg II<br>Shared layers, grounded in game controls</h1><p>Step 1: a broad control catalogue and a practical architecture for fewer maps. Keyboard families keep the layout memorable; urgency, sustained inputs and simultaneous access decide which keys must stay immediate.</p><span class="tag">Software v2 target</span><span class="tag">Source-documented samples</span><span class="tag">Provisional layer concept</span></header>
    <nav><a href="#findings">Findings</a><a href="#coverage">Coverage</a><a href="#layers">Layers</a><a href="#exceptions">Exceptions</a><a href="#catalogue">Search bindings</a><a href="#games">Game sources</a></nav><main>
    <section id="findings"><div class="stats"><div class="stat"><b>74</b><span>Game / edition / layout records</span></div><div class="stat"><b>1,747</b><span>Binding entries</span></div><div class="stat"><b>78</b><span>Cited source URLs</span></div><div class="stat"><b>8</b><span>Broad genre families</span></div></div><h2>Recommended starting point: one shared family, four layers</h2><p>Keep a direct Base and three coherent banks: Numbers, Letters / Panels, and Functions / Navigation. Use these layers to add reach without multiplying game profiles. Duplicate urgent indexed inputs on Base even when their full family is also available on another layer.</p><div class="callout"><b>The important exception is urgency.</b> An infrequent heal, interrupt, dodge or target change can require faster access than a frequently opened inventory. A held input also needs a comfortable chord with movement, aim and any layer selector.</div><p>Four is a practical starting architecture, not a mathematical minimum. Three may hold enough raw key outputs, but its larger mixed groups may be harder to remember or chord. More layers create capacity without necessarily improving access. The final physical layout depends on which buttons you can press comfortably together.</p></section>
    <section id="coverage"><h2>What the research covers</h2><p>The collection contains representative documented controls, including keyboard and mouse rows where they explain combinations. A row can describe several keys or one context-specific action. It does not equal one unique key. No sampled game was tested in a current local installation.</p>''' + table(['Genre family','Game records','Binding entries','Games / scoped layouts'],group_rows) + '''<div class="two"><div><h3>Evidence quality</h3>''' + table(['Source family','Game records'],[[esc(k),v] for k,v in summary['game_counts_by_evidence_family'].items()]) + '''</div><div><h3>Important limits</h3><p>Publisher documentation is preferred, but old manuals remain old manuals. Feral port manuals establish the documented Mac/Linux mappings, not an independently verified current Windows preset. Independent guides and community tables retain their lower-assurance labels.</p><p>Cyberpunk 2077 uses a legacy 2021 control guide; Diablo IV is a prelaunch sample; World of Warcraft and ESO use historical manuals/guides. Escape from Tarkov has version ambiguity. DCS and X-Plane are small specialist subsets.</p><p>PoE2's older table contains unresolved key/preset/context collisions. Conflicting rows were omitted; the newer UI source does not resolve the complete current combat preset. Rejected Hades and Dota 2 tables do not contribute to the totals.</p></div></div><h3>Documented key presence</h3><p>These counts are the number of sampled game records in which a key appears. They include keys inside chords and sequences. Left/right modifiers are grouped only in this aggregate; exact variants and numpad keys remain separate in the catalogue. Partial source coverage makes these lower-bound counts within this sample. They are <b>not keypress frequency, urgency, popularity, or a representative market survey</b>.</p>''' + table(['Key / aggregate modifier alias','Sampled game records'],presence_rows) + '''<p>For example, Esc is omitted from many short introductory tables. Its lower count does not make it less useful than another key. The catalogue also includes mouse inputs, stored separately from keyboard presence.</p></section>
    <section id="layers"><h2>Layer architecture</h2>''' + table(['Conceptual layer','Key family','Access rule'],layer_rows) + '''<h3>A compact direct-key starting set</h3><p>Use the thumbstick for <code>W A S D</code> where that is the intended movement scheme. Keep <code>Shift Ctrl Alt Space Esc Tab</code> accessible. Give common action letters such as <code>Q E R F C X Z V G T</code> direct candidates, alongside <code>1 2 3 4</code>. This is a candidate key set, not a universal action assignment or a final button map. Additional direct keys follow personal frequency and urgency.</p><h3>How to choose the easiest positions</h3><ol><li><b>Identify a reaction deadline or dangerous failure first.</b> A rare emergency action can outrank a frequent panel.</li><li><b>Check simultaneous and sustained access.</b> Test the complete combination: layer selector, key, movement, raw modifier and mouse aim.</li><li><b>Use actual personal repetition next.</b> The present research does not contain telemetry. Source-table counts cannot substitute for it.</li><li><b>Use cross-game key presence and mnemonic families to break ties.</b> Put deliberate keys into recognizable groups.</li><li><b>Use action labels as annotations.</b> A printed key keeps its stable place; its action may vary by game unless the game itself is rebound.</li></ol><h3>Rules across every shared layer</h3><ul><li>Keep the same selector positions and a predictable return path.</li><li>Keep movement output consistent unless a different scheme is deliberate.</li><li>Retain a usable Esc / cancel route and the raw modifiers needed by chords.</li><li>Use a layer selector as a device control; emitting game Shift or Ctrl as part of it must be intentional.</li><li>Do not treat a visually blank mapping as transparent until the exported configuration or runtime confirms it.</li><li>Preserve top-row digits separately from numpad digits, and left/right modifiers where the game distinguishes them.</li></ul></section>
    <section id="exceptions"><h2>What forces an exception</h2>''' + evidence_table + '''<h3>Optional base variants</h3>''' + table(['Variant','When it is justified','What stays shared'],[
        ['Hotbar','Repeated use of most number-row slots, modifier banks, or urgent F-key target/ability commands.','The same Numbers, Letters and Functions / Navigation organization.'],
        ['RTS grid','Direct QWER / ASDF / ZXCV commands, unit groups and camera controls need comfortable independent access.','The same slow utility banks; verify how thumbstick WASD interacts with the selected command grid.'],
        ['Specialist simulation','Aircraft or vehicle controls exceed comfortable access even after coherent layering.','Reuse the common utility banks wherever practical; add only the specialist commands that are actually required.']]) + '''<p>Start without these alternates. Add Hotbar or Grid when the selected games demonstrate a concrete access problem. If both workflows matter, two distinct alternate bases can be reasonable. A strict two-map ceiling would be arbitrary. Genre is an organizational aid; the selected input preset and actual held combinations are the deciding evidence.</p><h3>Use game context to reduce manual switching</h3><p>A game often reuses the same key across walking, vehicles, menus, building and combat. Let that native context do useful work. Do not create a separate Azeron layer for every in-game state unless access or clarity requires it.</p></section>
    ''' + profile_html + '''
    <section id="implementation"><h2>What remains for a concrete Software v2 layout</h2><p>Azeron's current software page describes six onboard profiles and game-dependent Xbox 360 analog support. Its linked older Cyborg II manual documents layer switching, momentary return and an option that changes held outputs when a layer changes. Those older instructions do not establish the exact behavior of the installed v2 build.</p><p><a href="https://azeron.com/pages/software">Azeron Software information</a> · <a href="https://cdn.shopify.com/s/files/1/0930/2386/3123/files/Azeron_Cyborg_II_Manual_V1_5_4-3_1642644f-e002-4121-8560-6cde7ed84c65.pdf?v=1744695206">Linked v1.5.4 manual</a></p><p>The implementation stage should identify the physical button IDs and comfortable combinations; inspect the current export; confirm hold thresholds, tap delivery and held-input transitions; check the selected in-game presets; and then generate separate keys, actions and combined diagrams. A 150 ms exclusive tap/hold selector would make its layer unavailable until the threshold is met; this is a design consequence of that proposed threshold, not a measured v2 latency.</p><p>Raw function keys can also be consumed by graphics or overlay tools. Moving F10 to a layer still emits F10; it does not isolate listeners. Resolve a real collision by changing an emitted binding or the receiving shortcut where supported.</p><div class="callout caution"><b>Step 1 boundary:</b> this research defines the requirements and starting architecture. It does not assign physical button IDs, create an importable Azeron profile, change any device setting, or establish gameplay timing.</div></section>
    <section id="catalogue"><h2>Search the complete binding catalogue</h2><p>Filter by game or genre, then search an action, raw key expression or context. Every result links to its control source. Urgency is analyst interpretation; hold/repeat is only a documented fact when its source note explicitly says so.</p><div class="filters"><label for="search">Search</label><input id="search" placeholder="e.g. reload, F1, inventory, Ctrl"><select id="genre" aria-label="Genre"><option value="">All genres</option></select><select id="game" aria-label="Game"><option value="">All games</option></select><button id="clear">Clear</button></div><p id="result-count" class="muted" aria-live="polite"></p><div class="table-wrap"><table id="binding-table"><thead><tr><th>Game</th><th>Action</th><th>Raw key expression</th><th>Context</th><th>Urgency estimate</th><th>Hold / repeat classification</th><th>Source / notes</th></tr></thead><tbody id="rows"></tbody></table></div><button id="more">Show 100 more</button><noscript><p>JavaScript is needed for the searchable table. All records are also available in the accompanying workbook and research JSON.</p></noscript></section>
    <section id="games"><h2>Game scope and source notes</h2><p>Open a game to see its exact source qualification. A full table is not claimed where the source only supplies an introductory subset.</p>''' + ''.join(game_cards) + '''</section><footer>Research stage: ready for layout judgment within the stated scope. Keyboard presence is a derived count, not measured use. Report and workbook are generated views of the research master.</footer></main><script>
    const data=__DATA__;
    const search=document.getElementById('search'),genre=document.getElementById('genre'),game=document.getElementById('game'),rows=document.getElementById('rows'),more=document.getElementById('more');
    let limit=100;
    function option(el,v){const o=document.createElement('option');o.value=v;o.textContent=v;el.append(o)}
    [...new Set(data.map(r=>r.genre))].sort().forEach(v=>option(genre,v));
    [...new Set(data.map(r=>r.game))].sort().forEach(v=>option(game,v));
    const safe=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
    function render(){const q=search.value.toLowerCase().trim();const found=data.filter(r=>(!genre.value||r.genre===genre.value)&&(!game.value||r.game===game.value)&&(!q||[r.game,r.action,r.key,r.context,...r.keys].join(' ').toLowerCase().includes(q)));rows.innerHTML=found.slice(0,limit).map(r=>'<tr><td>'+safe(r.game)+'</td><td>'+safe(r.action)+'</td><td>'+safe(r.key)+'</td><td>'+safe(r.context)+'</td><td>'+safe(r.urgency)+'</td><td>'+safe(r.hold)+'</td><td><a href="'+safe(r.source)+'">Control source</a><br><small>'+safe(r.evidence)+(r.note?'<br>'+safe(r.note):'')+'</small></td></tr>').join('');document.getElementById('result-count').textContent=found.length+' matching entries · '+Math.min(limit,found.length)+' displayed';more.hidden=found.length<=limit;}
    [search,genre,game].forEach(el=>el.addEventListener('input',()=>{limit=100;render()}));more.addEventListener('click',()=>{limit+=100;render()});document.getElementById('clear').addEventListener('click',()=>{search.value='';genre.value='';game.value='';limit=100;render()});render();
    </script></body></html>'''
    report = report.replace('Cited source URLs', 'Registered URLs · 76 bind sources')
    path.write_text(report.replace('__DATA__', payload), encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalogue', type=Path)
    ap.add_argument('--master', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--profile', type=Path)
    ap.add_argument('--export-inputs', action='store_true', help='Regenerate collection inputs for the normalizer from the canonical master')
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    if args.master:
        master = json.loads(args.master.read_text())
        catalogue = catalogue_from_master(master)
    else:
        catalogue = json.loads(args.catalogue.read_text())
        master = make_master(catalogue)
    (args.output / 'AI_MASTER.json').write_text(json.dumps(master, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    dump(args.output / 'catalogue_view.json', catalogue)
    if args.export_inputs:
        game_map = {g['game_id']: g for g in catalogue['games']}
        binding_map = {b['binding_id']: b for b in catalogue['bindings']}
        for doc in catalogue['input_documents']:
            original = dict(doc['raw_document_metadata'])
            original['games'] = []
            for gid in doc['main_game_ids']:
                g = game_map[gid]
                original['games'].append({**g['raw_metadata'], 'bindings': [binding_map[bid]['raw_binding'] for bid in g['binding_ids']]})
            dump(args.output / doc['filename'], original)
    profile = json.loads(args.profile.read_text()) if args.profile else None
    write_report(catalogue, args.output / 'Azeron_Step1_Research_Report.html', profile)
    print(json.dumps({'games': len(catalogue['games']), 'binding_rows': len(catalogue['bindings']), 'sources': len(catalogue['sources']), 'master_bytes': (args.output / 'AI_MASTER.json').stat().st_size, 'report_bytes': (args.output / 'Azeron_Step1_Research_Report.html').stat().st_size}))


if __name__ == '__main__':
    main()
