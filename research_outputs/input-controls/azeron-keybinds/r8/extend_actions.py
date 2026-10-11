#!/usr/bin/env python3
"""Add a newly read publisher-manual scope to the preserved R7 supplement.
The original 179 records retain their evidence status. No effective config claim.
"""
import argparse,copy,hashlib,json
from pathlib import Path
P=Path(__file__).parent

def run(prior,design):
 old=json.loads(prior.read_text());d=copy.deepcopy(old);d.update(revision='R8',native_design_revision='R8',native_design_sha256=hashlib.sha256(design.read_bytes()).hexdigest(),prior_actions_sha256=hashlib.sha256(prior.read_bytes()).hexdigest())
 sid='BAYO-PC-MANUAL';scope='Bayonetta PC publisher manual, pages 5–7; not Bayonetta 2/3/Origins or user overrides.'
 d['sources'].append({'id':sid,'url':'https://store.steampowered.com/manual/460790','title':'SEGA — Bayonetta PC manual',
  'locator':'Printed pages 5–7; keyboard table p5 visually inspected and controls text p6–7 extracted.',
  'type':'publisher_manual','checked_at':'2026-10-11','limitation':scope,
  'document_sha256':'621188b7c779e3a6edecb3bd908e6d35beb3cdf3f138061a76f9ed89f72e61f0',
  'document_bytes':13301067,'read_method':'Exact official Steam PDF retrieved through authorized text-only remote host; PDFKit document page render (not desktop capture). No OCR.',
  'redirect_url':'https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/460790/manuals/BAYO_STEAM_MANUAL_HR.pdf?t=1763677459'})
 def add(action,variants,cat,context='gameplay',gesture='not specified',icon=None,notes=None):
  e={'id':'r8-bayo-'+str(len([e for e in d['entries'] if e['game_id']=='bayonetta-pc'])+1).zfill(2),'game_id':'bayonetta-pc','source_row_id':None,'source_id':sid,
   'raw_expression':' / '.join(' + '.join(v) for v in variants),'variants':variants,'action':action,'context':context,'gesture':gesture,'inherited_gesture':None,
   'gesture_evidence':'SOURCE_EXPLICIT' if gesture!='not specified' else 'NOT_ESTABLISHED_BY_TABLE','category':cat,'icon':icon or d['categories'][cat]['icon'],
   'category_origin':'reviewed_display_taxonomy_not_game_schema','evidence':'PUBLISHED_SCOPE_RECHECKED','effective_binding_verified':False,'physical_tested':False,
   'scope':scope,'checked_at':'2026-10-11','parsing_override':None,'notes':notes or []}
  d['entries'].append(e)
 add('Move',[[k] for k in 'WASD'],'movement')
 add('Walk',[['Ctrl']],'movement',gesture='hold')
 add('Punch',[['Mouse Left']],'combat',gesture='press / hold for follow-up shots')
 add('Kick',[['Mouse Right']],'combat',gesture='press / hold for follow-up shots')
 add('Jump / double jump',[['Space']],'movement',gesture='press; press again in air',icon='jump')
 add('Shoot / action',[['Mouse Middle']],'combat',gesture='press / hold rapid fire')
 add('Gravity reset',[['F']],'movement',notes=['Relevant while Witch Walk is active.'])
 add('Action',[['E']],'interaction')
 add('Taunt',[['Q']],'combat',gesture='press')
 add('Change weapon set',[['Mouse Wheel']],'weapons')
 add('Lock-on',[['Alt']],'combat',gesture='hold',notes=['Movement while lock-on is active is walking, not running, per p6.'])
 add('Evade',[['Shift']],'movement',gesture='press with direction',notes=['Witch Time is triggered by correctly timed evasion, not an independent keyboard action.'])
 add('Camera',[['Mouse Movement']],'camera')
 add('Camera up',[['Home']],'camera',notes=['In menus Home restores defaults; do not mix the two contexts.','Home may also be an OptiScaler shortcut under the existing toolkit policy, if that tool is active; no active-stack inspection was performed.'])
 add('Camera down',[['End']],'camera')
 add('Camera left',[['Delete']],'camera',notes=['Possible ReShade Delete collision only when such a tool is actually active; not tested here.'])
 add('Camera right',[['Page Down']],'camera')
 add('Item — left slot',[['1']],'interaction')
 add('Item — upper slot',[['2']],'interaction')
 add('Item — right slot',[['3']],'interaction')
 add('Game menu',[['Tab']],'menus')
 add('Pause menu',[['Esc']],'system',icon='pause')
 add('Reset camera',[['Insert']],'camera')
 add('Navigate options',[[k] for k in 'WASD'],'menus','menus')
 add('Select',[['Mouse Left']],'menus','menus')
 add('Cancel / back',[['Mouse Right'],['Esc']],'menus','menus')
 add('Scroll options',[['Mouse Wheel']],'menus','menus')
 add('Move cursor',[['Mouse Movement']],'menus','menus')
 add('Restore defaults',[['Home']],'system','menus',notes=['Changes game settings if used there. The Atlas never sends this input.'])
 for g in d['games']:
  if g['id']=='bayonetta-family':g['title']='Bayonetta 2 / 3 / Origins — platform and controls pending'
 d['games'].append({'id':'bayonetta-pc','title':'Bayonetta — PC manual','scope':scope,'status':'PUBLISHED_SAMPLE_NOT_EFFECTIVE','contexts':['gameplay','menus']})
 d['cross_row_dependencies']+= [
  {'game_id':'bayonetta-pc','keys':['Alt','W/A/S/D'],'relation':'held_lock_on_with_movement','status':'publisher_p6_p7; simultaneous access inferred from movement under lock'},
  {'game_id':'bayonetta-pc','keys':['Shift','W/A/S/D'],'relation':'directional_evade','status':'publisher_p6_explicit'},
  {'game_id':'bayonetta-pc','relation':'witch_time_is_result_of_timed_evade','status':'publisher_p6; no dedicated key created'}]
 assert len(d['entries'])==208 and d['entries'][:179]==old['entries']
 (P/'ACTIONS_R8.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');return d
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--prior',type=Path,required=True);a.add_argument('--design',type=Path,required=True);x=a.parse_args();d=run(x.prior,x.design);print(len(d['entries']),'records;',len(d['games']),'targets;',len(d['sources']),'manual sources')
