"""Preparation hints never activate layers or change selection/ownership."""
from pathlib import Path
import configparser,copy,importlib.util,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import GameToolOverlay as api
spec=importlib.util.spec_from_file_location('prepared_fixtures',Path(__file__).with_name('Test-GameToolOverlay.py'))
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)

class PreparedHints(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='PreparedOverlay-');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);_,source=fixtures.fixture(self.root)
        self.store=api.Store(self.root/'store');self.store.import_manifest(source,'absent')
        self.value,sha=self.store.load()
        self.value['preferences'].update(enabled=True,display=True,display_target='studio')
        self.store.write(self.value,sha)
        self.result={'render':True,'asset_id':'asset-combined','display_target':'studio','group_id':self.value['manifest']['groups'][0]['id'],
                     'game_id':'game','layer_state':'Event-tracked','foreground_exe':'Gameplay.exe'}
    def relay(self,result=None):
        api.relay(self.store,result or self.result,self.store.directory,now=1800000000.)
        parser=configparser.ConfigParser(interpolation=None);parser.read(self.store.directory/'overlay-selection.ini')
        return parser['Overlay']
    def test_hints_only_current_group_context_view(self):
        fields=self.relay()
        self.assertEqual(fields['WarmCount'],'1')
        current=next(a for a in self.value['manifest']['assets'] if a['id']=='asset-combined')
        self.assertEqual(fields['WarmSHA2561'],current['sha256'])
        self.assertEqual(fields['File'],fields['WarmFile1'])
        self.assertEqual(fields['Active'],'1')
    def test_inactive_selection_has_no_preparation_hints(self):
        fields=self.relay({'render':False,'reason':'Native profile changed'})
        self.assertEqual(fields['Active'],'0');self.assertNotIn('WarmCount',fields)
    def test_hints_cannot_skip_current_image_integrity(self):
        fields=self.relay();path=Path(fields['File']);path.write_bytes(path.read_bytes()+b'changed')
        with self.assertRaises(api.OverlayError):self.relay()
    def test_many_registered_layers_are_bounded_without_selection(self):
        value,sha=self.store.load();manifest=value['manifest'];keymap=manifest['keymaps'][0]
        asset=next(a for a in manifest['assets'] if a['id']=='asset-combined')
        for n in range(10):
            name='L'+str(n);layer=copy.deepcopy(keymap['layers'][0]);layer['id']=name
            keymap['layers'].append(layer);keymap['blank_masks'][name]=[]
            row=copy.deepcopy(asset);row.update(id='warm-'+str(n),layer=name)
            manifest['assets'].append(row);manifest['groups'][0]['asset_ids'].append(row['id'])
        self.store.write(value,sha);before=self.store.path.read_bytes()
        fields=self.relay()
        self.assertEqual(fields['WarmCount'],'8');self.assertNotIn('WarmFile9',fields)
        self.assertEqual(self.store.path.read_bytes(),before)
        self.assertEqual(fields['File'],str((self.store.directory/asset['path']).absolute()))

if __name__=='__main__':unittest.main()
