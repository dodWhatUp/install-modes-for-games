"""Disposable Windows filesystem transactions; no real game or store is touched."""
import copy, hashlib, importlib.util, json, os, shutil, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from control_service import ControlService, DEFAULTS, native_settings_path, patch_ini, sha, validate_values

HERE=Path(__file__).parent
class PureTests(unittest.TestCase):
    def test_ranges_and_dependencies(self):
        for key,value in [('duration',11),('regen',float('nan')),('fov_min',39),('fov_min',True),('modifier','..'),('width',True),('nr',True)]:
            with self.subTest(key=key,value=value):
                v=copy.deepcopy(DEFAULTS);v[key]=value
                with self.assertRaises(ValueError):validate_values(v)
        v=copy.deepcopy(DEFAULTS);v['fov_min']=65;v['fov_max']=60
        with self.assertRaises(ValueError):validate_values(v)
        self.assertEqual(validate_values(DEFAULTS),DEFAULTS)
    def test_ini_preserves_unknown_bytes(self):
        raw=b'\xef\xbb\xbf; header\r\n[General]\r\nDurationMult = 2.00 ; user note\r\nOther=keep\r\n\r\n[Else]\r\nDurationMult=9\r\n'
        expected=raw.replace(b'DurationMult = 2.00 ;',b'DurationMult = 3.50 ;')
        self.assertEqual(patch_ini(raw,'General',{'DurationMult':'3.50'}),expected)
        self.assertEqual(patch_ini(b'[General]\nOther=9\n','General',{'X':3}),b'[General]\nOther=9\nX = 3\n')
        self.assertEqual(patch_ini(b'[ADDON]\nLoadFromDllMain=\n[Luma]\nSRUserType=2\n','ADDON',{'LoadFromDllMain':'addon.dll'}),b'[ADDON]\nLoadFromDllMain=addon.dll\n[Luma]\nSRUserType=2\n')
        with self.assertRaises(ValueError):patch_ini(b'[General]\nX=1\nX=2\n','General',{'X':3})

    def test_missing_native_settings_are_not_created(self):
        with tempfile.TemporaryDirectory() as folder,patch.dict(os.environ,{'LOCALAPPDATA':folder}):
            with self.assertRaisesRegex(RuntimeError,'No settings file was created or reset'):
                native_settings_path(Path(folder))
            self.assertFalse((Path(folder)/'WB Games').exists())

    def test_invalid_native_binding_is_not_silently_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            base=Path(folder)
            (base/'control-panel-paths.json').write_text(json.dumps({'schema':1,'native_config_path':'relative/render.cfg'}))
            with self.assertRaisesRegex(ValueError,'absolute render.cfg'):native_settings_path(base)

@unittest.skipUnless(os.name=='nt','Original reviewed Bink/profile controller is Windows-only')
class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='shadow-control-test-');self.base=Path(self.tmp.name)
        self.game=self.base/'game/x64';self.game.mkdir(parents=True)
        def put(rel,data):
            p=self.game/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
        previous=b'fixture-previous-host';luma=b'fixture-luma-host';loader=b'fixture-loader';bink=b'fixture-stock-bink';exe=b'fixture-exe'
        components=[]
        for key,file in [('graphics','dxgi.dll'),('renodx','renodx-shadowofwar.addon64'),
            ('multi-skills','plugins/Multi Equip Skills.dll'),('elven-speed','plugins/Elven Speed.dll'),
            ('fov','plugins/FOV Extender.dll'),('luma','Luma-Middle-earth Shadow of War.addon'),
            ('nr','renodx-dlss5.addon64'),('dlss-runtime','nvngx_dlss.dll'),('nr-runtime','nvngx_dlssnr.dll')]:
            data=previous if key=='graphics' else key.encode();p=put(file+('.gametools-off' if key in ('luma','nr') else ''),data)
            c={'id':key,'name':key,'file':file,'sha256':sha(p)}
            if key=='graphics':c['allowed_hashes']=[sha(p),hashlib.sha256(luma).hexdigest().upper()]
            components.append(c)
        put('bink2w64.dll',loader);put('bink2w64_.dll',bink);put('ShadowOfWar.exe',exe)
        put('ReShade.ini',b'[ADDON]\nLoadFromDllMain=\n')
        put('modloader/Mod Loader.ini',b'[Plugins]\nMulti Equip Skills.dll=true\nElven Speed.dll=true\nFOV Extender.dll=true\n')
        put('plugins/config/Multi Equip Skills.ini',b'[General]\nToggleSkillEquip=527 0 0\nPlaySound=true\nToggleBehavior=false\nUnknown=preserve\n')
        put('plugins/config/Elven Speed.ini',b'[General]\nDurationMult=2.000000\nRegenRateMult=0.000000\n')
        put('plugins/config/FOV Extender.ini',b'[General]\nMinFOV=45.000000\nMaxFOV=60.000000\n')
        payloads=[]
        for name,data in [('payloads/previous/dxgi.dll',previous),('payloads/luma/dxgi.dll',luma)]:
            p=self.base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);payloads.append({'file':name,'sha256':sha(p)})
        for profile,config in [('previous',b'[ADDON]\nLoadFromDllMain=\n'),('luma',b'[ADDON]\nLoadFromDllMain=\n[Luma]\nSRUserType=2\n')]:
            p=self.base/f'profile-configs/{profile}/ReShade.ini';p.parent.mkdir(parents=True);p.write_bytes(config)
        save=self.base/'steam-save';save.mkdir();(save/'campaign.sav').write_bytes(b'Never change this save')
        manifest={'game_path':str(self.game),'save_path':str(save),'exe_sha256':sha(self.game/'ShadowOfWar.exe'),
            'original_bink_sha256':sha(self.game/'bink2w64_.dll'),'loader_sha256':sha(self.game/'bink2w64.dll'),
            'components':components,'payloads':payloads}
        (self.base/'graphics-profiles.json').write_text(json.dumps(manifest))
        (self.base/'graphics-profile-state.json').write_text('{"profile":"previous"}')
        native=self.base/'local/WB Games/Shadow of War/render.cfg';native.parent.mkdir(parents=True)
        native.write_bytes(b'"ScreenWidth16by9" "3840.000000"\r\n"ScreenHeight16by9" "2160.000000"\r\n"HDROut" "1.000000"\r\n')
        self.env=patch.dict(os.environ,{'LOCALAPPDATA':str(self.base/'local')});self.env.start()
        shutil.copy2(HERE/'graphics_profiles.py',self.base/'graphics_profiles.py')
        spec=importlib.util.spec_from_file_location('fixture_legacy_'+self.base.name,self.base/'graphics_profiles.py')
        b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
        def fixture_closed():self.assertTrue(b.G.resolve().is_relative_to(self.base.resolve()))
        b.closed=fixture_closed;self.b=b;self.service=ControlService(self.base,backend=b,native=native)
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def test_apply_readback_and_save_preservation(self):
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values'])
        v.update({'multi-skills':False,'duration':3.5,'regen':-0.25,'fov_min':50.,'fov_max':65.,'width':2560,'height':1440})
        result=self.service.apply(v,snapshot)
        self.assertTrue(result['changed']);self.assertEqual(self.service.read()['values'],v)
        self.assertIn('Unknown=preserve',(self.game/'plugins/config/Multi Equip Skills.ini').read_text())
        self.assertEqual((self.base/'steam-save/campaign.sav').read_bytes(),b'Never change this save')
        self.assertTrue((self.base/'last-applied-profile.json').exists())
        self.assertTrue(Path(result['recovery']).is_dir())

    def test_desktop_environment_uses_bound_file_and_preserves_its_recovery(self):
        native=self.service.native;original=native.read_bytes()
        (self.base/'control-panel-paths.json').write_text(json.dumps({'schema':1,'native_config_path':str(native)}))
        other=self.base/'different-desktop-appdata'
        with patch.dict(os.environ,{'LOCALAPPDATA':str(other)}):
            service=ControlService(self.base,backend=self.b)
            self.assertEqual(service.native,native)
            snapshot=service.read();v=copy.deepcopy(snapshot['values']);v['width']=2560
            result=service.apply(v,snapshot)
            recovery=Path(result['recovery'])/'controller-native-settings'
            self.assertEqual((recovery/'render.cfg').read_bytes(),original)
            self.assertEqual(json.loads((recovery/'location.json').read_text())['source'],str(native))
            self.assertEqual(service.read()['values']['width'],2560)
            self.assertFalse(other.exists())

    def test_native_binding_change_refuses_stale_apply(self):
        binding=self.base/'control-panel-paths.json'
        binding.write_text(json.dumps({'schema':1,'native_config_path':str(self.service.native)}))
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values']);v['duration']=3.
        binding.write_text(binding.read_text()+'\n')
        with self.assertRaisesRegex(RuntimeError,'Files changed'):self.service.apply(v,snapshot)
    def test_mid_transaction_failure_restores_files_and_positions(self):
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values']);v.update({'multi-skills':False,'duration':4.,'fov_min':50.})
        original=self.b.write
        def fail(p,data):
            if p.name=='FOV Extender.ini':raise OSError('simulated disk failure')
            return original(p,data)
        self.b.write=fail
        with self.assertRaises(OSError):self.service.apply(v,snapshot)
        self.assertEqual(self.service.read()['fingerprint'],snapshot['fingerprint'])
    def test_stale_binary_toggle_is_not_overwritten(self):
        snapshot=self.service.read();self.b.enable('fov',False);self.b.UNDO=[]
        v=copy.deepcopy(snapshot['values']);v['duration']=3.
        with self.assertRaisesRegex(RuntimeError,'Files changed'):self.service.apply(v,snapshot)
        self.assertFalse(self.b.module_state(self.b.module('fov')))
    def test_unrelated_ini_edit_preserves_loader_only_disable(self):
        p=self.game/'modloader/Mod Loader.ini'
        p.write_text(p.read_text().replace('FOV Extender.dll=true','FOV Extender.dll=false'))
        snapshot=self.service.read();self.assertFalse(snapshot['values']['fov'])
        v=copy.deepcopy(snapshot['values']);v['duration']=3.
        self.service.apply(v,snapshot)
        self.assertTrue(self.b.module_state(self.b.module('fov')))
        self.assertIn('FOV Extender.dll=false',p.read_text())
    def test_open_store_blocks_before_any_write(self):
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values']);v['duration']=3.
        def blocked():raise RuntimeError('Close Steam first')
        self.b.closed=blocked
        with self.assertRaisesRegex(RuntimeError,'Steam'):self.service.apply(v,snapshot)
        self.assertEqual(self.service.fingerprint(),snapshot['fingerprint'])
        self.assertFalse((self.base/'profile-snapshots').exists())
    def test_luma_neural_and_previous_roundtrip(self):
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values']);v.update({'profile':'luma','dlaa':True,'nr':True})
        self.service.apply(v,snapshot);self.assertEqual(self.service.read()['values'],v)
        v.update({'profile':'previous','dlaa':False,'nr':False})
        self.service.apply(v,self.service.read());self.assertEqual(self.service.read()['values'],v)
        self.assertFalse((self.game/'Luma-Middle-earth Shadow of War.addon').exists())
    def test_save_load_is_private_only_and_traversal_rejected(self):
        snapshot=self.service.read();v=copy.deepcopy(snapshot['values']);v['duration']=4.
        p=self.service.save_profile('My setup',v);self.assertTrue(p.exists())
        self.assertEqual(self.service.load_profile('My setup'),v)
        self.assertEqual(self.service.fingerprint(),snapshot['fingerprint'])
        for name in ['../escape','CON','LPT1','bad/path']:
            with self.assertRaises(ValueError):self.service.save_profile(name,v)
    def test_export_pins_and_no_game_save_binaries(self):
        entries=[]
        for name in ['Mod.Loader.zip','Multi.Equip.Skills.7z','Elven.Speed.7z','FOV.Extender.7z']:
            p=self.base/'downloads'/name;p.parent.mkdir(exist_ok=True);p.write_bytes(('fixture '+name).encode())
            entries.append({'file':name,'sha256':sha(p),'source':'https://example.invalid/source'})
        (self.base/'control-export-sources.json').write_text(json.dumps(entries))
        snapshot=self.service.read();out=self.service.export_vortex(snapshot)
        self.assertEqual(len(list((out/'original-archives').iterdir())),4)
        self.assertTrue((out/'READ-ME-FIRST.txt').exists())
        self.assertEqual(self.service.fingerprint(),snapshot['fingerprint'])
        self.assertFalse(list(out.rglob('*.sav')));self.assertFalse(list(out.rglob('*.exe')))
        (self.base/'downloads/Elven.Speed.7z').write_bytes(b'Changed archive')
        with self.assertRaisesRegex(ValueError,'changed'):self.service.export_vortex(snapshot)

if __name__=='__main__':unittest.main(verbosity=2)
