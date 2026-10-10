import importlib.util,json
from pathlib import Path
R=Path(__file__).parent
sp=importlib.util.spec_from_file_location('a',R/'audit_r6_access.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
d=json.loads((R/'DESIGN_R6.json').read_text());s=json.loads((R/'ACCESS_SUMMARY_R6.json').read_text())
assert s['parsed_variants']==3106 and s['rows_inherited']==2195 and s['unparsed_rows_not_scored']==28
for f,m in s['counts'].items():
 for mode,c in m.items(): assert sum(c.values())==3106
cases=[('COMPACT',['Alt','Q'],False,'DIRECT_MODEL_ROUTE'),('COMPACT',['Alt','Q'],True,'FINGER_MODEL_CONFLICT'),('COMPACT',['Ctrl','1'],True,'LAYER_MODEL_ROUTE'),('SPARSE',['Ctrl','1'],False,'LAYER_MODEL_ROUTE'),('SPARSE',['Ctrl','1'],True,'FINGER_MODEL_CONFLICT'),('SPARSE',['C','2'],False,'FINGER_MODEL_CONFLICT'),('SPARSE',['E','Up Arrow'],False,'CROSS_BANK_ONLY'),('SPARSE',['Numpad 1'],False,'OUTPUT_REVIEW'),('SPARSE',['W','S'],False,'FINGER_MODEL_CONFLICT'),('SPARSE',['W','A'],True,'DIRECT_MODEL_ROUTE')]
for f,k,m,expect in cases:
 v=d['variants'][f];got=a.routes(k,v['maps'],v['selectors'],d['position_map'],m)
 assert got['status']==expect,(f,k,m,got)
# NAV's thumb selector must not be incorrectly treated as little-finger reserved.
v=d['variants']['SPARSE'];result=a.routes(['Left Bracket'],{'NAV':v['maps']['NAV']},{'NAV':28},d['position_map'],False)
assert result['status']=='LAYER_MODEL_ROUTE'
result=a.routes(['Left Bracket'],{'NAV':v['maps']['NAV']},{'NAV':28},d['position_map'],True)
assert result['status']=='FINGER_MODEL_CONFLICT'
print('12 routing assertions plus count reconciliations passed; no live tests.')
(R/'QA_ACCESS_R6.json').write_text(json.dumps({'routing_assertions':12,'counts_reconciled':True,'inherited_variants':3106,'physical_tests':0,'gameplay_tests':0,'new_actual_frequency_measurements':0},indent=2)+'\n')
