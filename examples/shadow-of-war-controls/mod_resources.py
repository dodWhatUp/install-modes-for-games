"""Reviewed mod links and text documentation; no installation or deployment."""
from pathlib import Path
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

COLLECTION='https://github.com/ReaperAnon/Shadow-Of-War-Mods'
README='https://raw.githubusercontent.com/ReaperAnon/Shadow-Of-War-Mods/88aa2d6058fe7287f5b9387f1995c8522e0447a1/README.md'
MODS=[
 {'id':'multi-skills','name':'Multi Equip Skills','category':'Gameplay / quality of life',
  'page':COLLECTION+'#multi-equip-skills','reader':README,'section':'Multi-Equip Skills',
  'folder':'plugins','config':'plugins/config','file':'plugins/Multi Equip Skills.dll',
  'summary':'Equip multiple skill upgrades using the configured modifier. Native unlock and purchase requirements remain.',
  'notes':'Requires Middle Earth Mod Loader. Equipped combinations can persist in the save; gameplay combinations remain unverified.'},
 {'id':'elven-speed','name':'Elven Speed','category':'Movement / quality of life',
  'page':COLLECTION+'#elven-speed','reader':README,'section':'Elven Speed',
  'folder':'plugins','config':'plugins/config','file':'plugins/Elven Speed.dll',
  'summary':'Adjust ability duration and focus regeneration using the original plugin settings.',
  'notes':'Requires Middle Earth Mod Loader. Values change movement balance. Changes here are previews until Apply.'},
 {'id':'fov','name':'FOV Extender','category':'Camera / quality of life',
  'page':COLLECTION+'#fov-extender','reader':README,'section':'FOV Extender',
  'folder':'plugins','config':'plugins/config','file':'plugins/FOV Extender.dll',
  'summary':'Set the camera FOV limits exposed by the original plugin.',
  'notes':'Requires Middle Earth Mod Loader. Supported limits are 40 to 70; minimum must not exceed maximum.'},
 {'id':'gameplay','name':'Middle Earth Mod Loader','category':'Shared gameplay loader',
  'page':'https://github.com/ReaperAnon/Middle-Earth-Mod-Loader',
  'reader':'https://raw.githubusercontent.com/ReaperAnon/Middle-Earth-Mod-Loader/loaderfix/README.md',
  'folder':'modloader','config':'modloader','file':'bink2w64.dll',
  'summary':'Loads the gameplay plugins and their shared F12 menu. The reviewed loaderfix version forwards to the preserved original Bink runtime.',
  'notes':'Keep one DLL loader. A manager extension may install its own loader automatically; review ownership before deployment.'},
 {'id':'renodx','name':'RenoDX for Shadow of War','category':'Graphics / HDR',
  'page':'https://www.nexusmods.com/middleearthshadowofwar/mods/130',
  'folder':'.','config':'.','file':'renodx-shadowofwar.addon64',
  'summary':'Game-specific HDR, tonemapping and color controls in the reviewed ReShade graphics stack.',
  'notes':'RHI retains graphics ownership. Use Delete in the game for its native graphics panel. These settings are not a second live in-game overlay.'},
 {'id':'graphics','name':'ReShade graphics host','category':'Graphics host',
  'page':'https://reshade.me/','folder':'.','config':'.','file':'dxgi.dll',
  'summary':'Hosts the reviewed graphics add-ons and shader controls.',
  'notes':'Use Delete for the in-game menu. ReShade and Luma hosts are separate reviewed profiles; do not stack competing proxy DLLs.'},
 {'id':'luma','name':'Luma (disabled trial)','category':'Experimental graphics',
  'page':'https://github.com/Filoppi/Luma-Framework/wiki','folder':'Luma','config':'.',
  'file':'Luma-Middle-earth Shadow of War.addon',
  'summary':'Retained experimental game integration with native-resolution DLAA support.',
  'notes':'The recorded NVIDIA-driver shutdown fault is unresolved. Keep the trial off. This game integration does not provide lower-resolution DLSS SR.'},
 {'id':'nr','name':'DLSS 5 Generic (disabled trial)','category':'Experimental neural rendering',
  'page':'https://github.com/RankFTW/RHI','folder':'.','config':'.','file':'renodx-dlss5.addon64',
  'summary':'Retained Generic 8.5.0-rc10 neural-rendering trial in the separate Luma profile.',
  'notes':'Neural delivery is unverified; the Luma shutdown fault remains. Graphics files stay under the reviewed local profiles and RHI.'},
 {'id':'textures','name':'Official UHD texture pack','category':'Official Steam DLC',
  'page':'https://store.steampowered.com/app/561950/','folder':'..','config':None,
  'summary':'The official high-resolution texture pack is installed. Steam owns its installation and on/off checkbox.',
  'notes':'This official DLC is not included in manager handoff packages.'},
]
EDIT_FIELDS={
 'multi-skills':('multi-skills','modifier','toggle','sound'),
 'elven-speed':('elven-speed','duration','regen'),
 'fov':('fov','fov_min','fov_max'),
 'gameplay':('gameplay',),
}

def resources(game,workspace,native):
    game,workspace,native=Path(game),Path(workspace),Path(native)
    result=[]
    for item in MODS:
        entry=dict(item)
        entry['locations']={'Mod files':game/item['folder'],'Game folder':game,
                            'Original downloads':workspace/'downloads'}
        if item['config']:entry['locations']['Mod settings']=game/item['config']
        entry['locations']['Native render settings']=native.parent
        if item.get('file'):
            active=game/item['file'];off=Path(str(active)+'.gametools-off')
            entry['installed_file']=active if active.exists() else off if off.exists() else active
        entry['editable']=item['id'] in EDIT_FIELDS
        result.append(entry)
    return result

def get_mod(key):
    return next(item for item in MODS if item['id']==key)

def safe_web_url(url):
    parsed=urlsplit(url)
    if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Only a public HTTPS source link is supported.')
    return url

def read_author_page(key):
    """Fetch one reviewed text URL on demand; never execute remote markup."""
    item=get_mod(key);url=item.get('reader')
    if not url:return 'This source has no text reader. The mod information is available here; use Open author page for its full website.'
    safe_web_url(url)
    request=Request(url,headers={'User-Agent':'ShadowOfWar-ModControl/1.1'})
    with urlopen(request,timeout=12) as response:
        if urlsplit(response.geturl()).hostname!='raw.githubusercontent.com':
            raise ValueError('The author text moved to an unexpected host.')
        raw=response.read(131073)
    if len(raw)>131072:raise ValueError('The author page is too large for this text reader. Open the full website instead.')
    text=raw.decode('utf-8-sig')
    if item.get('section'):
        match=re.search(r'^### '+re.escape(item['section'])+r'\s*\n(.*?)(?=^### |^## |\Z)',text,re.M|re.S)
        if not match:raise ValueError('The author section moved. Use Open author page for the full documentation.')
        text='### '+item['section']+'\n\n'+match[1].strip()
    # Show text rather than embedded HTML/images, scripts or download buttons.
    text=re.sub(r'!\[[^]]*\]\([^)]*\)','',text)
    return 'AUTHOR DOCUMENTATION (read-only)\n'+item['page']+'\n\n'+text
