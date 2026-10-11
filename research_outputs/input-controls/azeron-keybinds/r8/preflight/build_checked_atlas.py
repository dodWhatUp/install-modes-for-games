#!/usr/bin/env python3
"""Build a checked display derivative from the exact R8 recovery, without altering it."""
import argparse, copy, hashlib, json, re
from pathlib import Path
from safe_io import ReviewError, read_regular, strict_json
from native_review import expected
ROOT=Path(__file__).parent

def build(r8,out):
 original=r8/'Azeron_R8_Action_Atlas_HE.html';raw,_=read_regular(original)
 if hashlib.sha256(raw).hexdigest()!='7db74e9baf356588c637e76a66afc179bddfc3776ddd277f18aaf6161969280d':raise ReviewError('Unexpected original Atlas version.')
 text=raw.decode();start='<script id="atlas-data" type="application/json">';i=text.index(start)+len(start);j=text.index('</script>',i)
 data=strict_json(text[i:j].encode());before_design=copy.deepcopy(data['design']);before_actions=copy.deepcopy(data['actions'])
 realizations={}
 for family in ['CORE5','SPARSE6']:
  snapshot=expected(r8/f'Azeron_R8_{family}_Profiles.zip',family);by={p['name']:p for p in snapshot['profiles']};maps={}
  for bank in data['design']['variants'][family]['maps']:
   p=by[f'SHARED R8 {family} - {bank}'];maps[bank]={str(b['id']):{'keys':[k for k in b['keyValues'] if k!='0'],
    'meta':[k for k in b['metaValues'] if k!='0'],'types':b['types']} for b in p['inputs']}
  realizations[family]=maps
 data['nativeRealizations']=realizations
 data['graphicsPolicy']={'source':'https://github.com/dodWhatUp/install-modes-for-games/blob/806f52e59ee8e5e16b20a40837134297b41144a9/docs/GRAPHICS-CONTROLS.md',
  'state':'GUIDANCE_ONLY_ACTUAL_ACTIVE_STACK_UNKNOWN','possibleOwners':{'Delete':'ReShade menu','Home':'OptiScaler menu','F12':'Game-engine interface / CET when supported','F11':'Personal neural-rendering settings slots when supported','F10':'Neural rendering on/off when supported','F7':'Neural-rendering dimensions when supported','F6':'Native SR quality adapter when supported'}}
 data['preflight']={'native_family':'R8_UNCHANGED','display_revision':'R8-PREFLIGHT','live_state':False,'source_kind':'Exact archive projection plus conditional owner-policy warnings'}
 text=text[:i]+json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+text[j:]
 anchor='<button id="clear" type="button">'
 assert text.count(anchor)==1
 text=text.replace(anchor,'<label><input id="toolHints" type="checkbox"> בדיקת חפיפה אפשרית לכלי גרפיקה</label>'+anchor)
 core=(ROOT/'atlas_checks.js').read_text();adapter=(ROOT/'atlas_checked_adapter.js').read_text()
 text=text.replace('</body>','<script>'+core+'</script><script>'+adapter+'</script></body>')
 text=text.replace('R8: פרופילים חדשים ומפת פעולות תואמת','R8: אותה פריסה, עם בדיקות לפני שימוש')
 text=text.replace('CORE5 ו־SPARSE6 הן חלופות — לא צריך לייבא את שתיהן.','CORE5 ו־SPARSE6 הן חלופות — לא צריך לייבא את שתיהן. נוספו בדיקת צד Ctrl/Shift/Alt ואזהרות כלי גרפיקה מותנות; לא זוהתה התקנה חיה.')
 assert before_design==data['design'] and before_actions==data['actions']
 with Path(out).open('x',encoding='utf-8') as f:f.write(text)
 return {'display_bytes':len(text.encode()),'native_design_unchanged':True,'action_records_unchanged':len(data['actions']['entries']),
   'new_profile_ids':0,'game_tested':False,'real_browser_rendered':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--r8',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.r8,a.out)))
