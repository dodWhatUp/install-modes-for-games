"""Accessible standalone presentation of the same read-only projections."""
from html import escape
import json

from .explorer import build_view, graph_text
from .inventory import check_sources
from .overview import overview


def accessible_report(context, roots=None):
    view = build_view(context, roots)
    state = overview(check_sources(context, roots))
    def record(title, value):
        return '<li><details><summary>' + escape(title) + '</summary><pre>' + escape(json.dumps(value, ensure_ascii=False, indent=2)) + '</pre></details></li>'
    nodes = ''.join(record(n['label'] + ' · ' + n['source']['availability'] + ' · ' + n['runtime_load'], n) for n in view['nodes'])
    devices = ''.join(record(d['label'] + ' · ' + d['freshness'] + ' · live connection not observed', d) for d in state['devices'])
    events = ''.join(record(e['operation_id'] + ' · ' + e['state'] + ' · ' + e['coverage'], e) for e in state['events'])
    # Export is durable. Only explicitly source-owned summaries can appear;
    # no_store and session_only summaries and every detail body are omitted.
    activities = ''.join(record(str(a['goal']), a) for a in state['activities'] if a['retention'] == 'source_owned')
    omitted = sum(a['retention'] != 'source_owned' for a in state['activities'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>System control · selected source report</title>
<style>body{font:1rem/1.5 system-ui;margin:auto;padding:1rem;max-width:65rem;color:#172b3a;background:#fafcfd}nav{display:flex;flex-wrap:wrap;gap:1rem}input{font:inherit;width:95%;padding:.4rem}summary{cursor:pointer;padding:.5rem}details{border:1px solid #748594;border-radius:.3rem;margin:.5rem 0}li{overflow-wrap:anywhere}ul{padding-left:1.3rem}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:.6rem;font-size:.9rem}:focus-visible{outline:3px solid #005fcc;outline-offset:3px}section{margin-top:2rem}[hidden]{display:none}</style>
<a href="#main">Skip to report</a><header><h1>System control</h1>
<p>Selected source report. Runtime load and live connections are not observed. This page performs no operations.</p>
<nav aria-label="Report sections"><a href="#architecture">Architecture and instructions</a><a href="#devices">Devices</a><a href="#events">Changes and transfers</a><a href="#activities">Activity summaries</a></nav></header>
<main id="main"><label for="filter">Filter report records</label><input id="filter" type="search" autocomplete="off">
<p id="matches" role="status" aria-live="polite"></p>
<section id="architecture" aria-labelledby="architecture-title"><h2 id="architecture-title">Architecture and instructions</h2><ul>''' + nodes + '''</ul><details><summary>Dependencies as text</summary><pre>''' + escape(graph_text(view)) + '''</pre></details>
<details><summary>Coverage and unknowns</summary><pre>''' + escape(json.dumps({"unknowns":view['unknowns'], "unknown_coverage": context.get('unknown_coverage', []), "omissions":context.get('inventory_omissions', []), "revision":view['revision']}, indent=2)) + '''</pre></details></section>
<section id="devices" aria-labelledby="devices-title"><h2 id="devices-title">Devices</h2><ul>''' + devices + '''</ul></section>
<section id="events" aria-labelledby="events-title"><h2 id="events-title">Changes and transfers</h2><ul>''' + events + '''</ul></section>
<section id="activities" aria-labelledby="activities-title"><h2 id="activities-title">Activity summaries</h2><p>''' + str(omitted) + ''' private session summaries omitted. Full conversation and attachment content is never included in this report.</p><ul>''' + activities + '''</ul></section></main>
<script>const filter=document.getElementById('filter'),rows=[...document.querySelectorAll('section ul>li')];function apply(){const terms=filter.value.toLocaleLowerCase().split(/\\s+/).filter(Boolean);let count=0;for(const row of rows){row.hidden=!terms.every(t=>row.textContent.toLocaleLowerCase().includes(t));if(!row.hidden)count++}document.getElementById('matches').textContent=count+' matching records';}filter.addEventListener('input',apply);filter.addEventListener('keydown',e=>{if(e.key==='Escape'){filter.value='';apply()}});apply();</script></html>'''
