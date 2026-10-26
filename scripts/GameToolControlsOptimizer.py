"""Bounded, deterministic ordinal planning. Recommendations never apply input.

No comfort calibration or absolute global optimality claim. Unknown demand,
overlapping priority intervals, unreviewed requirements and immutable controls
remain visible instead of being silently assigned convenient numbers.
"""
from __future__ import annotations
import copy,time
import GameToolControlsPlanner as p
import GameToolControlsRules as rules
import GameToolOverlay as overlay

VERSION = "0.1.0"


def recommend(w, document, *, max_states=5000, seconds=1.0):
    overlay.require(type(max_states) is int and 1 <= max_states <= 20000 and type(seconds) in (int,float) and 0 < seconds <= 5,
                    "Use a bounded planning budget")
    initial = p.preview(w, document); records = {r["id"]: r for r in initial["rows"]}
    actions = {a["id"]: a for a in w["actions"]}; grouped = {}
    for a in w["actions"]: grouped.setdefault((a["context"], a["bundle_id"] or a["id"]), []).append(a)
    groups = []; withheld = []; active_rules = rules.active_rules(w)
    for identity, members in grouped.items():
        score = p.bundle_priority(members) if members[0]["bundle_id"] else p.priority(members[0]["urgency"], members[0]["frequency"])
        if any(a["overlay_context"] is None or a["needs_movement"] is None or not a["meaning"] or a["activation"] == "unknown" for a in members) or not score["candidates"]:
            withheld.append({"action_ids":[a["id"] for a in members],"reason":"Meaning, context, movement/activation or access need is unverified"});continue
        choices = {r["id"]: r for r in records[members[0]["id"]]["candidates"]}
        for a in members[1:]: choices = {key:r for key,r in choices.items() if key in {v["id"] for v in records[a["id"]]["candidates"]}}
        if not choices:
            withheld.append({"action_ids":[a["id"] for a in members],"reason":"No route satisfies the combined hard constraints"});continue
        groups.append({"id":identity,"members":members,"score":score,"choices":list(choices.values())})
    # Do not resolve an ambiguous demand order with a midpoint or genre guess.
    uncertain = set()
    exclusive={frozenset(x['contexts']) for x in w['exclusive_contexts']}
    for i,g in enumerate(groups):
        for h in groups[i+1:]:
            if frozenset((g['members'][0]['context'],h['members'][0]['context'])) in exclusive:continue
            ga,gb=g['score']['range'],h['score']['range']
            if ga!=gb and max(ga[0],gb[0])<=min(ga[1],gb[1]): uncertain.update((g['id'],h['id']))
    retained=[]
    for g in groups:
        if g['id'] in uncertain:withheld.append({'action_ids':[a['id'] for a in g['members']], 'reason':'Priority ranges overlap; research before relocating competing actions'})
        else:retained.append(g)
    groups=sorted(retained,key=lambda g:(-g['score']['range'][0],len(g['choices']),g['id']))
    overlay.require(len(groups)<=32,"Narrow optimization to at most 32 classified action groups")
    def quality(g,r):
        # Components are ordinal policy decisions, not measured ergonomic cost.
        row=p.route_access_rank(w,r)
        pref=sum(rules.preference(w,a,r,active_rules) for a in g['members'])
        moves=any(p.canonical_output(w,r['output'])!=p.canonical_output(w,a['output']) for a in g['members'])
        return (r['holder'] is not None,row,pref,moves,r['id'])
    for g in groups:g['choices'].sort(key=lambda r:quality(g,r))
    exclusive={frozenset(x['contexts']) for x in w['exclusive_contexts']}
    variable={a['id'] for g in groups for a in g['members']}
    fixed=[a for a in w['actions'] if a['id'] not in variable]
    canonical_cache={key:p.canonical_output(w,key) for key in {a['output'] for a in w['actions']} | {r['output'] for g in groups for r in g['choices']}}
    canonical=lambda value:canonical_cache.get(value,value)
    def collides(a,key,b,otherkey):
        if a['id']==b['id'] or a['bundle_id'] and (a['context'],a['bundle_id'])==(b['context'],b['bundle_id']):return False
        if canonical(key)!=canonical(otherkey) or frozenset((a['context'],b['context'])) in exclusive:return False
        # Retained pre-existing overlaps are evidence gaps, not new collisions.
        return canonical(key)!=canonical(a['output']) or canonical(otherkey)!=canonical(b['output'])
    states=0;deadline=time.monotonic()+seconds;limited=False;best=None;best_quality=None
    selected={}
    route_index={r['id']:r for r in p.routes(document)}
    def combination_penalty():
        primary={a['id']:selected[g['id']] for g in groups for a in g['members']}
        for a in fixed:
            current=records[a['id']]['current']
            if len(current)==1:primary[a['id']]=route_index[current[0]]
        pairs={tuple(sorted((a['id'],other))) for a in w['actions'] for other in a['simultaneous']}
        return sum(1 for a,b in pairs if a in primary and b in primary and
                   (primary[a]['finger']==primary[b]['finger'] or primary[a]['holder_finger']==primary[b]['finger'] or primary[b]['holder_finger']==primary[a]['finger']))
    def search(index):
        nonlocal states,limited,best,best_quality
        if states>=max_states or time.monotonic()>=deadline:limited=True;return
        states+=1
        if index==len(groups):
            qualities=[quality(g,selected[g['id']]) for g in groups]
            vector=(combination_penalty(),tuple(q[:3] for q in qualities),sum(bool(q[3]) for q in qualities),tuple(q[4] for q in qualities))
            if best_quality is None or vector<best_quality:best_quality=vector;best=dict(selected)
            return
        g=groups[index]
        for route in g['choices']:
            if any(collides(a,route['output'],b,b['output']) for a in g['members'] for b in fixed):continue
            if any(collides(a,route['output'],b,selected[h['id']]['output']) for a in g['members'] for h in groups[:index] for b in h['members']):continue
            selected[g['id']]=route;search(index+1);selected.pop(g['id'],None)
            if limited:return
    search(0)
    candidate=copy.deepcopy(w);proposals=[]
    if best is not None:
        by_id={a['id']:a for a in candidate['actions']}
        for g in groups:
            route=best[g['id']]
            for a in g['members']:
                if route['id'] not in records[a['id']]['current']:
                    by_id[a['id']]['proposed_route']=route['id']
                    proposals.append({'action_id':a['id'],'route':route['id'],'priority':records[a['id']]['priority'],
                                      'reason':'Feasible route under protected controls, ordinal row preference, shared rules and stable action priority'})
    checked=p.preview(candidate,document)
    if any(r['blocked'] for r in checked['rows']):
        candidate=copy.deepcopy(w);proposals=[]
        withheld.append({'action_ids':[],'reason':'Complete-plan checks found unresolved existing/proposed constraints; retain the draft'})
    claim = 'No eligible classified groups; existing draft retained' if not groups else 'Best found within bounded ordinal search' if limited else 'Best within enumerated feasible routes and stated ordinal policy'
    return {'kind':'controls_position_recommendations','schema_version':1,'candidate':candidate,'proposals':proposals,
            'withheld':withheld,'states':states,'search_limited':limited,'solution_found':bool(groups) and best is not None,
            'claim':claim,
            'automatic_adoption':False,'native_or_game_changes':False}
