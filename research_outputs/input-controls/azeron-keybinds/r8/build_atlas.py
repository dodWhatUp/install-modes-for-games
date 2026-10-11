#!/usr/bin/env python3
"""Generate a local, display-only UI on exact R6 geometry. No native changes.
SVG pictograms are authored UI assets. They are not game artwork or evidence.
"""
import argparse,hashlib,json
from pathlib import Path
P=Path(__file__).parent
ICONS={
'lock':'M6 10h12v11H6zM8 10V6a4 4 0 0 1 8 0v4M12 14v3',
'move':'M12 3v18M3 12h18M8 7l4-4 4 4M8 17l4 4 4-4M7 8l-4 4 4 4M17 8l4 4-4 4',
'run':'M14 4a1 1 0 1 0 .01 0M11 8l4 3 4-1M11 8l-3 4-4 1M12 10l-2 6-6 4M10 16l5 1 2 4',
'jump':'M5 20h14M12 17V4M7 9l5-5 5 5',
'crouch':'M14 5a1.5 1.5 0 1 0 .01 0M12 9l-2 5 6 3 3 3M10 14l-5 2 1 4M12 10l6 2',
'swap':'M4 7h15l-4-4M20 17H5l4 4',
'reload':'M19 8a8 8 0 1 0 1 7M19 3v5h-5',
'combat':'M4 3l12 12M3 4l12 12M12 15l4-4M14 17l3-3M17 17l3 3M20 3L8 15M21 4L9 16M7 14l3 3M4 20l3-3',
'use':'M6 20V9l3 1V4a2 2 0 0 1 4 0v7l4-1 3 4-3 6H6',
'menu':'M3 4h18v16H3zM3 9h18M7 13h10M7 16h7',
'bag':'M4 7h16v14H4zM8 7V4h8v3',
'map':'M3 5l6-2 6 2 6-2v16l-6 2-6-2-6 2zM9 3v16M15 5v16',
'eye':'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12M15 12a3 3 0 1 0-6 0 3 3 0 0 0 6 0',
'chat':'M3 4h18v13H9l-6 4V4M7 8h10M7 12h7',
'gear':'M12 3v3M12 18v3M3 12h3M18 12h3M5.5 5.5l2 2M16.5 16.5l2 2M5.5 18.5l2-2M16.5 7.5l2-2M17 12a5 5 0 1 0-10 0 5 5 0 0 0 10 0',
'heal':'M9 3h6v6h6v6h-6v6H9v-6H3V9h6z',
'pause':'M7 4v16M17 4v16',
'unknown':'M8 7a4 4 0 0 1 8 0c0 3-4 3-4 6M12 18v1'
}
ALIASES={
'Jump':['קפיצה','לקפוץ'], 'Sprint':['ריצה','ספרינט'], 'Activate':['שימוש','אינטראקציה'], 'Interact':['אינטראקציה','שימוש'],
'Inventory':['מלאי','תיק'], 'Map':['מפה'], 'Reload':['טעינה','נשק'], 'Skills menu':['כישורים'],
'Motion tracker':['גלאי תנועה'], 'Favorites':['מועדפים'], 'Shout/power':['צעקה','כוח'], 'Sneak':['התגנבות'],
'Context action':['אינטראקציה'], 'Swap primary/secondary':['החלפת נשק'], 'Melee attack':['תגרה'],
'Character menu':['תפריט דמות'],'Pause':['השהיה','תפריט'], 'Quick save':['שמירה מהירה'],'Quick load':['טעינה מהירה'],'Lock-on':['נעילה','מטרה'],'Evade':['התחמקות'],'Walk':['הליכה'],'Restore defaults':['ברירות מחדל','איפוס']}

def build(design_path,out):
 design_raw=design_path.read_bytes();design=json.loads(design_raw);actions=json.loads((P/'ACTIONS_R8.json').read_text())
 assert hashlib.sha256(design_raw).hexdigest()==actions['native_design_sha256']
 for e in actions['entries']:e['aliases']=ALIASES.get(e['action'],[])
 actions['categories']['camera']['he']='מצלמה ומידע'
 for e in actions['entries']:
  if e['game_id']=='bayonetta-pc' and e['action']=='Lock-on':e['icon']='lock'
  if e['action']=='Jump / double jump':e['aliases']=['קפיצה','קפיצה כפולה']
 payload=json.dumps({'design':design,'actions':actions,'icons':ICONS},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
 core=(P/'atlas_core.js').read_text()
 template=(P/'atlas_template.html').read_text()
 html=template.replace('__DATA__',payload).replace('__CORE__',core)
 out.write_text(html,encoding='utf-8');print(out)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--design',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.design,a.output)
