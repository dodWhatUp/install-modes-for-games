"""Optional authoring controls mounted in the SAME operator panel/worker/backend.
No extra mailbox, service, web UI, screen capture, or live-game inference.
"""
from __future__ import annotations
import json
from pathlib import Path
from tkinter import ttk,filedialog,messagebox,simpledialog
from .deps import require,read_json
from .core import snapshot,sha
from .packs import inspect_pack,import_pack_local,load_pin,bind_instance_local
from .effective import inspect_instance,intent_preview
from .authoring import scaffold,learn_difference


def mount(panel):
    panel.pack_pin=None;panel.instance_id=None
    area=ttk.LabelFrame(panel,text='Extend to another game · data packs and reviewed native adapters',padding=5)
    area.pack(fill='x',before=panel.out)
    panel._button(area,'Review / import game pack…',lambda:review_import(panel))
    panel._button(area,'Bind current game files…',lambda:bind_files(panel))
    panel._button(area,'Semantic change…',lambda:semantic_preview(panel))
    advanced=ttk.Menubutton(area,text='Authoring');advanced.pack(side='left',padx=3)
    import tkinter as tk
    menu=tk.Menu(advanced,tearoff=False);advanced.configure(menu=menu)
    menu.add_command(label='Preview a named preset…',command=lambda:panel.run(lambda:named_preset(panel)))
    menu.add_command(label='Create draft pack…',command=lambda:panel.run(lambda:new_draft(panel)))
    menu.add_command(label='Compare two controlled originals…',command=lambda:panel.run(lambda:learn(panel)))
    menu.add_command(label='Inspect current game instance',command=lambda:panel.run(lambda:instance_context(panel)))
    menu.add_command(label='List imported packs and game instances',command=lambda:panel.run(lambda:registered(panel)))
    panel.controls.append(advanced)


def review_import(panel):
    folder=filedialog.askdirectory(parent=panel,title='Select game pack folder containing pack.json')
    if not folder:return
    folder=Path(folder)
    def reviewed(report):
        panel.show(report)
        if not messagebox.askyesno('Import this exact data pack?',
            report['title']+'\nVersion '+report['version']+'\n\nThis imports definitions, not game files. '
            'Metadata is not game acceptance. Review sources, fields and fixtures before binding.\n\nSHA-256:\n'+report['pack_sha256'],parent=panel):return
        digest=report['pack_sha256']
        def done(value):
            panel.pack_pin=value['pin'];panel.instance_id=None;panel.show(value)
            panel.status.set('Pack imported but not activated. Bind only reviewed active game files.')
        panel.start(lambda:import_pack_local(panel.service,folder,digest,authorize=lambda r:r['pack_sha256']==digest),done)
    panel.start(lambda:inspect_pack(folder),reviewed)


def bind_files(panel):
    require(panel.pack_pin is not None,'PACK_REQUIRED','Import the reviewed game pack first.')
    pin=dict(panel.pack_pin);pack=load_pin(panel.service,pin)
    require(pack['evidence']['stage']!='draft','PACK_DRAFT','Review actual native fields and fill the draft before binding.')
    variants=[v['id'] for v in pack['variants']]
    variant=variants[0] if len(variants)==1 else simpledialog.askstring('Exact input variant','Choose one: '+', '.join(variants),parent=panel)
    if variant is None:return
    require(variant in variants,'VARIANT_UNKNOWN','Choose an exact listed variant.')
    ident=simpledialog.askstring('Game installation ID','Choose a short ID for this installation, for example game-steam.',parent=panel)
    if not ident:return
    files=next(v['files'] for v in pack['variants'] if v['id']==variant);bindings={};hashes={};display=[]
    for f in pack['files']:
        if f['id'] not in files:continue
        selected=filedialog.askopenfilename(parent=panel,title=pack['title']+' · select active '+f['id']+' ('+f['adapter']+')')
        if not selected:return
        p=Path(selected);hashes[f['id']]=sha(snapshot(p));bindings[f['id']]={'root':str(p.parent),'relative':p.name}
        display.append(f['id']+' → '+str(p))
    if not messagebox.askyesno('Confirm active configuration owners',
            '\n'.join(display)+'\n\nThese paths are local-only. Confirm that these are the active files for '+variant+
            ', not old backups or another account. This registers exact schema/paths; no bindings are changed.',parent=panel):return
    def done(value):
        panel.instance_id=ident;panel.show(value);panel.status.set('Game instance registered. Preview semantic changes next; no native configuration changed.')
    panel.start(lambda:bind_instance_local(panel.service,pin,ident,variant,bindings,hashes,authorize=lambda r:r['files']==hashes,
        evidence='Operator selected current active native files and exact variant through local file pickers.'),done)


def semantic_preview(panel):
    ident=panel.instance_id
    require(ident,'INSTANCE_REQUIRED','Bind an exact game instance first.')
    path=filedialog.askopenfilename(parent=panel,title='Semantic intent JSON with changes (action/context/key)',filetypes=[('JSON','*.json')])
    if not path:return
    payload=read_json(Path(path));require(set(payload)=={'changes'},'INVALID_ARGUMENTS','Use only changes, not paths or approval flags.')
    def job():
        state=inspect_instance(panel.service,ident)
        return intent_preview(panel.service,ident,payload['changes'],state['revision'])
    def done(value):
        panel.show(value);panel.plan=None
        panel.items=value.get('items_request') or None;panel.preview=value if panel.items else None
        panel.status.set('Semantic preview only; Stage copies and Apply use the existing approvals.' if panel.items else value['status'])
    panel.start(job,done)


def new_draft(panel):
    parent=filedialog.askdirectory(parent=panel,title='Parent folder for a new draft game pack')
    if not parent:return
    game=simpledialog.askstring('New game ID','Choose a portable game ID (letters, digits, hyphens).',parent=panel)
    if not game:return
    title=simpledialog.askstring('Game title','Readable game title:',parent=panel)
    if not title:return
    adapter=simpledialog.askstring('Text adapter','Adapter ID: json, jsonc, ini, ini-sparse, ue-ini, ue-chord, xml, cfg-bind, keyvalues, colon-lines',parent=panel)
    if not adapter:return
    from .deps import contained,slug
    destination=contained(Path(parent),slug(game))
    panel.start(lambda:scaffold(destination,game,title,adapter),lambda v:(panel.show(v),panel.status.set('Draft only. Fill selectors, native codes, sources, contexts and fixtures; no game support inferred.')))


def learn(panel):
    before=filedialog.askopenfilename(parent=panel,title='Original copy BEFORE one known keybinding change')
    if not before:return
    after=filedialog.askopenfilename(parent=panel,title='Original copy AFTER that one known keybinding change')
    if not after:return
    adapter=simpledialog.askstring('Adapter','Exact adapter ID for these copies:',parent=panel)
    if not adapter:return
    panel.start(lambda:learn_difference(Path(before),Path(after),adapter,include_values=True),
        lambda v:(panel.show(v),panel.status.set('LOCAL native-value comparison. No action meaning inferred and nothing sent to AI.')))


def instance_context(panel):
    ident=panel.instance_id
    require(ident,'INSTANCE_REQUIRED','Bind or select a registered game instance first.')
    panel.start(lambda:inspect_instance(panel.service,ident),lambda v:(panel.show(v),panel.status.set('Effective scalar owners, not observed live-game behavior. More pages are available via CLI/API.')))


def registered(panel):
    from .packs import list_packs
    from .effective import list_instances
    def done(value):
        panel.show(value)
        ident=simpledialog.askstring('Select saved instance','Optional exact instance ID from this list (Cancel leaves selection unchanged):',parent=panel)
        if not ident:return
        rec=inspect_instance(panel.service,ident);panel.instance_id=ident;panel.pack_pin=rec['pack_pin'];panel.show(rec)
        panel.status.set('Existing instance selected; no definitions or game files changed.')
    panel.start(lambda:{'packs':list_packs(panel.service),'instances':list_instances(panel.service)},done)


def named_preset(panel):
    ident=panel.instance_id
    require(ident,'INSTANCE_REQUIRED','Select a registered game instance first.')
    from .effective import instance,preset_preview
    rec=instance(panel.service,ident);p=load_pin(panel.service,rec['body']['pin'])
    names=[x['id'] for x in p['presets'] if x['variant']==rec['body']['variant_id']]
    require(names,'PRESET_UNKNOWN','This variant has no reviewed named preset.')
    selected=simpledialog.askstring('Preview named preset','Choose one: '+', '.join(names),parent=panel)
    if not selected:return
    require(selected in names,'PRESET_UNKNOWN','Choose an exact named preset.')
    def job():
        state=inspect_instance(panel.service,ident)
        return preset_preview(panel.service,ident,selected,state['revision'])
    def done(value):
        panel.items=value.get('items_request') or None;panel.preview=value if panel.items else None;panel.plan=None
        panel.show(value);panel.status.set('Named preset preview only. Stage and Apply still require review.')
    panel.start(job,done)
