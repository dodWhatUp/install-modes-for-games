#!/usr/bin/env python3
"""Build a scoped published-default action supplement without changing raw rows.
The selected source sections were inspected in the R7 review. This is not the
user's effective configuration and not a whole-game completeness claim.
"""
import argparse,copy,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).parent
CONFIG={
'The Elder Scrolls V: Skyrim (original PC)':('skyrim-original','S1','PC original manual, not SE/AE or modded defaults','https://store.steampowered.com/manual/72850','PDF p3 image (printed p2), pp5–8 text',None),
'Warframe':('warframe','S2','Published quick-start keyboard guide, not a build-stamped effective preset','https://www.warframe.com/en/game/quickstart','Keyboard Controls',None),
'Tomb Raider (2013)':('tombraider2013','S3','Feral Mac port manual; single-player subset only','https://www.feralinteractive.com/en/manuals/tombraider/latest/steam/','Keyboard and Mouse',19),
'Shadow of the Tomb Raider: Definitive Edition':('shadowtr','S4','Feral Linux Definitive Edition manual','https://www.feralinteractive.com/en/manuals/shadowofthetombraider/latest/linux/','Keyboard',None),
'Alien: Isolation':('alienisolation','S5','Feral port manual, default keyboard subset','https://www.feralinteractive.com/en/manuals/alienisolation/latest/steam/','Keyboard',None),
'XCOM 2':('xcom2','S6','Feral Mac/Linux manual; tactical and general controls','https://www.feralinteractive.com/en/manuals/xcom2/latest/steam/','Controls / General and Tactical',21),
'FAIRY TAIL 2':('fairytail2','S7','Steam publisher web manual; field and battle are separate contexts','https://www.koeitecmoamerica.com/manual/fairytail2/en/2400.html','Keyboard & Mouse',None),
'OpenTTD':('openttd','S8','Project hotkey table; window/version qualifiers retained','https://wiki.openttd.org/en/Manual/Hotkeys','Ingame / Construction / Landscaping',None),
}
CATEGORIES={
 'movement':{'he':'תנועה','en':'Movement','color':'#76BFFF','symbol':'↟','icon':'move'},
 'weapons':{'he':'נשק והחלפה','en':'Weapons / switching','color':'#FFD17B','symbol':'⇄','icon':'swap'},
 'combat':{'he':'לחימה ויכולות','en':'Combat / abilities','color':'#FFAAAA','symbol':'◇','icon':'combat'},
 'interaction':{'he':'שימוש וחפצים','en':'Use / items','color':'#80DED0','symbol':'◎','icon':'use'},
 'menus':{'he':'תפריטים וניווט','en':'Menus / navigation','color':'#D1B6FF','symbol':'▤','icon':'menu'},
 'camera':{'he':'מצלמה ומידע','en':'Camera / information','color':'#C0D883','symbol':'◉','icon':'eye'},
 'communication':{'he':'תקשורת','en':'Communication','color':'#F6B8E2','symbol':'◌','icon':'chat'},
 'system':{'he':'מערכת וכלים','en':'System / tools','color':'#BECADB','symbol':'⚙','icon':'gear'},
 'unknown':{'he':'לא מאומת','en':'Unknown / review','color':'#BBC0CB','symbol':'?','icon':'unknown'}
}
def classify(action,context):
 t=(action+' '+context).lower()
 if re.search(r'chat|talk|marker|guide marks|emote|communication',t) and not re.search(r'interact|talk/interact',t):return 'communication'
 if re.search(r'pause|window mode|quick.?save|quick.?load|^save$',action,re.I):return 'system'
 if re.search(r'camera|zoom|peek|motion tracker|flashlight|survival instinct|first/third',t):return 'camera'
 if re.search(r'menu|journal|inventory|panel|map|^tabs$|categories|event log|favorite item|local map|magic|spells',t) and not re.search(r'spell slots',t):return 'menus'
 if re.search(r'reload|weapon|revolver|shotgun|flamethrower|bolt gun|stun baton|ready/sheath|bow/pistol',t):return 'weapons'
 if re.search(r'sprint|dash|jump|walk|crouch|sneak|dodge|scramble|swim|^move$|auto.run|movement',t):return 'movement'
 if re.search(r'interact|activate|context action|use|item|craft|healing|plant|^drop',t):return 'interaction'
 if re.search(r'attack|fire|melee|skill|ability|shout|power|block|bash|guard|awaken|magic|target|character swap|active character|overwatch',t):return 'combat'
 if 'ui' in t or 'construction' in t or 'landscape' in t or 'company' in t or 'list' in t:return 'menus'
 return 'unknown'
def specific_icon(action,category):
 t=action.lower()
 if 'jump' in t:return 'jump'
 if 'sprint' in t or 'dash' in t:return 'run'
 if 'crouch' in t or 'sneak' in t:return 'crouch'
 if 'reload' in t:return 'reload'
 if 'inventory' in t:return 'bag'
 if 'map' in t:return 'map'
 if 'healing' in t:return 'heal'
 if 'pause' in t:return 'pause'
 return CATEGORIES[category]['icon']

def build(INP,BASE):
 data=json.loads(INP.read_text());raw=data['records'];entries=[];games=[];sources=[]
 for g,(slug,sid,scope,url,locator,limit) in CONFIG.items():
  rs=[r for r in raw if r['row']['game']==g]
  if limit:rs=rs[:limit]
  if slug=='openttd':
   keep={'binding_944a44e537fc','binding_e151e6929b48','binding_6adab39006e9','binding_2934baf17cb8','binding_a61174d7ead8','binding_790c84631c07','binding_5af9ffc7c92f','binding_df311604d1dd','binding_d259b1e67084','binding_cc42bf471196','binding_6a450b3dcee9','binding_bc27f32bf6a6','binding_edcc47692d6f','binding_9ad1309b0390','binding_ef3e7292f344','binding_5a97c72f2a1c','binding_facdf4ddb466','binding_30f6813ad18c','binding_2209d7ff0765','binding_7cff4a33afb6','binding_6f2cf9cea91a'}
   rs=[r for r in rs if r['row']['id'] in keep]
  if slug=='skyrim-original':
   # Mouse hand assignment varies by context; omit those three combat rows from this display seed.
   rs=[r for r in rs if r['row']['id'] not in ['binding_2ea01abe5d29','binding_5a1162f3e6f8','binding_7d63ffaba2e0']]
  for r in rs:
   row=r['row'];variants=copy.deepcopy(r['syntax']['variants']);override=None
   if row['id']=='binding_7f25b18d54d6':
    variants=[[str(x)] for x in range(1,10)]+[['0']];override='Publisher table explicitly calls these abilities 1–10 on keys 1–0; row-scoped range resolution.'
   cat=classify(row['action'],row['context'])
   # Explicit semantic-review corrections; retained as authored taxonomy, not game facts.
   action_overrides={'Favorite hotkeys':'interaction','Aim':'combat','Aim/change focus':'camera',
      'Swap primary/secondary':'weapons','Equip melee':'weapons','Roll/evade':'movement',
      'Shoulder swap':'camera','Floor up/down':'camera','Confirm action':'interaction',
      'Waypoint move':'movement','End turn':'combat','Evac request':'interaction',
      'Center active unit':'camera','Avenger facilities':'menus','Move':'movement',
      'Character change':'combat','Extreme magic':'combat','Link choice':'combat',
      'Flee':'movement','Fast-forward hold':'system','Autorail':'interaction','Signals':'interaction',
      'Bridge':'interaction','Tunnel':'interaction','Removal tool':'interaction',
      'Land lower/raise/level':'interaction'}
   cat=action_overrides.get(row['action'],cat)
   ent={'id':'r7-'+row['id'],'game_id':slug,'source_row_id':row['id'],'source_id':sid,'raw_expression':row['key'],
      'variants':variants,'action':row['action'],'context':row['context'],'gesture':'not specified',
      'inherited_gesture':row['gesture'],'gesture_evidence':'NOT_ESTABLISHED_BY_KEY_TABLE',
      'category':cat,'icon':specific_icon(row['action'],cat),'category_origin':'analyst_semantic_tag_reviewed_not_game_schema',
      'evidence':'PUBLISHED_SCOPE_RECHECKED','effective_binding_verified':False,'physical_tested':False,
      'scope':scope,'checked_at':'2026-10-11','parsing_override':override,'notes':[]}
   if 'hold' in row['gesture'].lower() and 'documented' in row['gesture'].lower():ent['gesture']='hold'
   if row['id']=='add_fairytail2_021':ent['gesture']='hold'
   if row['id']=='binding_7586dcb75467':ent['gesture']='hold'
   if row['id']=='binding_cbf9fc73bb3b':ent['gesture']='hold'
   if row['id']=='binding_29d962b3d230':ent['gesture']='press'
   if row['id']=='binding_22012f5c4ae0':ent['gesture']='press/hold (shout strength)'
   if row['id']=='binding_063ec3fbfab9':ent['gesture']='hold Shift with direction'
   if slug=='shadowtr' and row['key'] in ['F1','F2','F3','F4']:ent['gesture']='hold'
   if slug=='warframe' and row['action']=='Sprint':ent['gesture']='hold'
   if slug=='warframe' and row['action']=='Crouch hold':ent['gesture']='hold'
   if slug=='alienisolation' and row['action']=='Radial menu':ent['gesture']='hold'
   if slug=='alienisolation' and row['action']=='Sprint':ent['gesture']='hold'
   if ent['gesture']!='not specified':ent['gesture_evidence']='SOURCE_EXPLICIT_IN_REVIEWED_SECTION'
   # Do not split paired numeric weapon names into invented individual actions automatically.
   if len(variants)>1:ent['notes'].append('Listed variants may represent separate actions or alternatives; original combined label is retained.')
   entries.append(ent)
  games.append({'id':slug,'title':g,'scope':scope,'status':'PUBLISHED_SAMPLE_NOT_EFFECTIVE','contexts':list(dict.fromkeys(e['context'] for e in entries if e['game_id']==slug))})
  sources.append({'id':sid,'url':url,'title':g+' — documented controls','locator':locator,'type':'publisher_or_project_manual','checked_at':'2026-10-11','limitation':scope+'; the current installed controls were not read.'})
 # One new scoped fact discovered during the original manual diagram review. Additive, no R1 rewrite.
 entries.append({'id':'r7-skyrim-skills-slash','game_id':'skyrim-original','source_row_id':None,'source_id':'S1','raw_expression':'/',
   'variants':[['Slash']],'action':'Skills menu','context':'menus','gesture':'not specified','gesture_evidence':'NOT_ESTABLISHED_BY_KEY_TABLE','inherited_gesture':None,'category':'menus','icon':'menu',
   'category_origin':'analyst_semantic_tag_reviewed_not_game_schema','evidence':'PUBLISHED_SCOPE_RECHECKED','effective_binding_verified':False,
   'physical_tested':False,'scope':CONFIG['The Elder Scrolls V: Skyrim (original PC)'][2],'checked_at':'2026-10-11',
   'parsing_override':None,'notes':['Additive discovery from original PC manual diagram: / opens Skills. Not promoted to SE/AE effective controls.']})
 entries.append({'id':'r7-tombraider-primary-fire-v','game_id':'tombraider2013','source_row_id':None,'source_id':'S3','raw_expression':'V',
   'variants':[['V']],'action':'Primary fire','context':'combat','gesture':'not specified','gesture_evidence':'NOT_ESTABLISHED_BY_KEY_TABLE','inherited_gesture':None,'category':'combat','icon':'combat',
   'category_origin':'analyst_semantic_tag_reviewed_not_game_schema','evidence':'PUBLISHED_SCOPE_RECHECKED','effective_binding_verified':False,
   'physical_tested':False,'scope':CONFIG['Tomb Raider (2013)'][2],'checked_at':'2026-10-11',
   'parsing_override':None,'notes':['Additive discovery: the reviewed Feral Mac manual lists primary fire on Left Mouse button OR V. The inherited corpus omitted the V alternative; it remains unchanged.']})
 # Keep explicitly requested but insufficiently supported controls visible as pending targets, not fabricated labels.
 for slug,title in [('poe2','Path of Exile 2'),('cyberpunk2077','Cyberpunk 2077'),('godofwar-ragnarok','God of War Ragnarök'),('doom-dark-ages','DOOM: The Dark Ages / Revelations'),('rdr','Red Dead Redemption'),('rdr2','Red Dead Redemption 2'),('gtav','Grand Theft Auto V'),('plague-requiem','A Plague Tale: Requiem'),('bayonetta-family','Bayonetta — select exact title/platform'),('dmc-family','Devil May Cry — select exact title/character')]:
  games.append({'id':slug,'title':title,'scope':'Effective/scoped current keys pending; see R6 GAME_READINESS_R6.json','status':'KEY_TABLE_PENDING','contexts':['pending']})
 result={'schema':'game-action-label-supplement/1','revision':'R7','status':'REVIEWED_REFERENCE_SAMPLES_NOT_LIVE_KEYS',
   'native_design_revision':'R6','native_design_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),
   'source_corpus_sha256':hashlib.sha256(INP.read_bytes()).hexdigest(),'sources':sources,'games':games,'categories':CATEGORIES,'entries':entries,
   'not_claimed':['Complete default tables','Effective user bindings','In-game or physical acceptance','Single best layout','Measured recognition speed benefit'],
   'cross_row_dependencies':[{'game_id':'fairytail2','components':['add_fairytail2_021','add_fairytail2_024'],'keys':['Tab','2/3/4'],'relation':'held_skill_bank_then_skill','status':'derived_from_adjacent_publisher_definitions_not_single_row'},
     {'game_id':'alienisolation','components':['binding_cc5b8d40d1ae'],'relation':'hold_V_with_direction','status':'publisher_explicit'},
     {'game_id':'skyrim-original','keys':['Alt','W/A/S/D'],'relation':'sprint_while_moving','status':'design_concurrency_requirement_grounded_in_manual'}]}
 (ROOT/'REVIEWED_ACTIONS_R7.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('reviewed row records',len(entries),'source games',len(CONFIG),'display targets',len(games))
 print('by source',[(g['id'],sum(e['game_id']==g['id'] for e in entries)) for g in games if g['status']!='KEY_TABLE_PENDING'])
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--corpus',type=Path,required=True);p.add_argument('--design',type=Path,required=True);a=p.parse_args();build(a.corpus,a.design)
