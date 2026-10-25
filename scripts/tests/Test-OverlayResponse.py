"""Cache isolation, invalidation and fresh-byte guards. No app/native input."""
from pathlib import Path
import copy,importlib.util,os,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
spec=importlib.util.spec_from_file_location('overlay_fixture',Path(__file__).with_name('Test-GameToolOverlay.py'))
fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)

class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='OverlayResponseFixture-');self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);_,manifest=fixture_module.fixture(self.root)
        self.store=api.Store(self.root/'private');self.store.import_manifest(manifest,'absent')
        self.value,self.sha=self.store.load();self.asset=self.value['manifest']['assets'][0]

    def test_load_cache_drafts_are_independent(self):
        with patch.object(api,'decode',wraps=api.decode) as decode:
            first,_=self.store.load();first['manifest']['games'][0]['label']='changed draft'
            second,digest=self.store.load()
            self.assertNotEqual(first,second);self.assertEqual(second,self.value)
            self.assertEqual(digest,self.sha);decode.assert_not_called()

    def test_same_length_same_mtime_registry_change_is_seen(self):
        path=self.store.path;stamp=path.stat();raw=path.read_bytes()
        changed=raw.replace(b'Long synthetic',b'New! synthetic')
        self.assertEqual(len(raw),len(changed));self.assertNotEqual(raw,changed)
        path.write_bytes(changed);os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
        loaded,digest=self.store.load()
        self.assertIn('New!',loaded['manifest']['games'][0]['label']);self.assertNotEqual(digest,self.sha)

    def test_invalid_registry_never_uses_old_cache(self):
        path=self.store.path;raw=path.read_bytes()
        path.write_bytes(raw.replace(b'overlay_store',b'invalid_store'))
        with self.assertRaises(api.OverlayError):self.store.load()
        path.write_bytes(raw);self.assertEqual(self.store.load()[0],self.value)

    def test_deleted_registry_does_not_return_cache(self):
        self.store.path.unlink()
        self.assertEqual(self.store.load(),(api.empty_store(),'absent'))

    def test_image_metadata_reused_but_every_hit_checks_content(self):
        with patch.object(api,'image_bytes',wraps=api.image_bytes) as decoder:
            raw,first=self.store.asset(self.asset);first['width']=999
            _,second=self.store.asset(self.asset)
            self.assertNotEqual(first,second);self.assertEqual(decoder.call_count,1)
            path=self.store.directory/self.asset['path'];stamp=path.stat()
            changed=bytearray(raw);changed[-1]^=1;path.write_bytes(changed)
            os.utime(path,ns=(stamp.st_atime_ns,stamp.st_mtime_ns))
            with self.assertRaises(api.OverlayError):self.store.asset(self.asset)
            self.assertEqual(decoder.call_count,1)

    def test_missing_image_never_uses_cached_metadata(self):
        self.store.asset(self.asset);(self.store.directory/self.asset['path']).unlink()
        with self.assertRaises(OSError):self.store.asset(self.asset)

    def test_image_metadata_cache_is_bounded(self):
        from PIL import Image
        import io
        for i in range(20):
            data=io.BytesIO();Image.new('RGB',(2,2),(i,1,2)).save(data,format='PNG');raw=data.getvalue()
            row=copy.deepcopy(self.asset);row['path']=f'overlay-assets/cache-{i}.png';row['sha256']=api.sha(raw)
            (self.store.directory/row['path']).write_bytes(raw);self.store.asset(row)
        self.assertEqual(len(self.store._image_info),16)

    def test_fast_relay_is_not_blocked_by_unchanged_inspector_rebuilds(self):
        import GameToolOverlayPanel as panel_api
        from types import SimpleNamespace
        self.value['preferences'].update(enabled=True,display=True,display_target='studio')
        self.value['preferences']['selections']['game']={'layer':'BASIC','context':'gameplay','view':'Combined'}
        self.store.write(self.value,self.sha)
        panel=panel_api.OverlayPanel.__new__(panel_api.OverlayPanel)
        panel.value,panel.fingerprint=self.store.load();panel.store=self.store
        events=[];clock=[1000.0]
        panel.parent=SimpleNamespace(after=lambda ms,fn:events.append(('after',ms)))
        panel.closed=False;panel.peek_held=False;panel.follow_layer=SimpleNamespace(get=lambda:True)
        native={'available':True,'state':'Observed','at':1000.0,'profile_id':'installed-BASIC','profile_sha256':'c'*64,'outputs_sha256':'a'*64}
        panel.layer_follower=SimpleNamespace(start=lambda fn:None,snapshot=lambda:dict(native))
        panel.foreground=lambda:{'exe':'C:\\Games\\Gameplay.exe','own':False,'at':clock[0]}
        panel.renderer=SimpleNamespace(hide=lambda:None)
        panel.note=SimpleNamespace(set=lambda text:events.append(('note',text)))
        panel.details=SimpleNamespace(delete=lambda *args:events.append(('details',None)),insert=lambda *args:None)
        panel._status_signature=None;panel._next_status_at=0
        with patch.object(panel_api.time,'monotonic',side_effect=lambda:clock[0]),patch.object(api,'relay',side_effect=lambda *args:events.append(('relay',None))):
            panel.tick()
            for i in range(5):
                clock[0]+=.02;panel.tick()
            self.assertEqual(sum(e[0]=='relay' for e in events),6)
            self.assertEqual(sum(e[0]=='details' for e in events),1)
            self.assertLess(next(i for i,e in enumerate(events) if e[0]=='relay'),next(i for i,e in enumerate(events) if e[0]=='details'))
            self.assertTrue(all(e[1]==20 for e in events if e[0]=='after'))
            native['profile_id']='installed-MENUS';panel.tick()
            self.assertEqual(sum(e[0]=='details' for e in events),2)
            clock[0]+=.3;panel.tick()
            self.assertEqual(sum(e[0]=='details' for e in events),3)

if __name__=='__main__':unittest.main()
