#!/usr/bin/env python3
"""Offline structural and logic checks; never records or injects keyboard input."""
from pathlib import Path
import hashlib, importlib.util, json, collections, sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit', ROOT/'build_corpus_audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def check(corpus_html, layout_file):
    report=json.loads((ROOT/'CORPUS_AUDIT_R4.json').read_text())
    layout=json.loads(layout_file.read_text());m=layout['maps'];b=layout_file.read_bytes()
    git_blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    assert git_blob=='b689507023491d7eafb28dd886a18923dbf2ae08', 'Wrong baseline layout'
    h=corpus_html.read_text();start=h.index('const data=')+len('const data=')
    rows,_=json.JSONDecoder().raw_decode(h[start:])
    assert rows==[r['row'] for r in report['records']], 'Inherited row content changed'
    assert len(rows)==2195 and len({r['game'] for r in rows})==94
    assert sum(g['rows'] for g in report['games'])==2195
    assert sum(report['summary']['syntax_status'].values())==2195
    assert sum(report['summary']['variant_routes'].values())==report['summary']['listed_variants']
    for r in report['records']:
        assert r['player_frequency'] is None and r['runtime_verified'] is False
        assert (len(r['variants'])==len(r['syntax']['variants']))
    expectations=[
      (['C','2'],False,'FINGER_MODEL_CONFLICT'),(['C','4'],False,'FINGER_MODEL_CONFLICT'),
      (['C','1'],False,'DIRECT_BUTTON_ROUTE'),(['Shift','C'],False,'FINGER_MODEL_CONFLICT'),
      (['E','Up Arrow'],False,'NO_SINGLE_BANK'),(['Numpad 1'],False,'UNMAPPED_OUTPUT'),
      (['1'],False,'DIRECT_BUTTON_ROUTE'),(['Plus'],False,'SYMBOL_LAYOUT_REVIEW'),
      (['Shift','F2'],False,'FINGER_MODEL_CONFLICT'),(['Shift','F8'],False,'FINGER_MODEL_CONFLICT'),
      (['Ctrl','1'],True,'LAYERED_BUTTON_ROUTE'),(['Ctrl','Shift','8'],True,'LAYERED_BUTTON_ROUTE'),
      (['Mouse Left'],True,'MOUSE_ONLY'),(['W','A'],False,'STICK_COMMAND_ROUTE'),
      (['W','S'],False,'FINGER_MODEL_CONFLICT'),(['Up Arrow'],True,'FINGER_MODEL_CONFLICT')]
    for keys,moving,status in expectations:
        got=audit.route(keys,m,moving)
        assert got['status']==status,(keys,status,got)
    assert audit.route(['Left Shift'],m)['side_unverified']==['Left Shift']
    assert audit.alternatives('Shift+A')['variants']!=audit.alternatives('A')['variants']
    # Nothing in the report silently turns a command's stick route into independent movement.
    byid={r['row']['id']:r for r in report['records']}
    assert byid['binding_5a97c72f2a1c']['variants'][0]['movement_stress']['status']=='STICK_ROLE_CONFLICT'
    raw_variants=[v for r in report['records'] for v in r['variants']]
    recomputed=dict(collections.Counter(v['isolated']['status'] for v in raw_variants))
    assert recomputed==report['summary']['variant_routes']
    rebuilt=audit.run(corpus_html,layout_file,ROOT)
    assert rebuilt['records']==report['records'] and rebuilt['summary']==report['summary']
    result={'schema_version':'1.0','status':'OFFLINE_AUDIT_CHECKED_NOT_RUNTIME',
      'date':'2026-10-10','map_git_blob':git_blob,'map_unchanged':True,
      'raw_rows_preserved_exactly_as_R2_derivative':2195,'games':94,
      'parser_unit_cases':audit.self_test(),'routing_assertions':len(expectations)+3,
      'independent_count_reconciliation':True,'repeat_run_semantics_identical':True,
      'full_source_recheck':False,'native_export_verified':False,'device_tested':False,
      'frequency_measured':False,'gameplay_tested':False,
      'source_of_corpus':'Existing R2 HTML derivative; not reconstructed AI_MASTER.json'}
    (ROOT/'QA_R4.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    check(Path(sys.argv[1]),Path(sys.argv[2]))
