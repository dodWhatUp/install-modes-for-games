"""Synthetic DOOM-shaped data; no host game/profile/config writes."""
from pathlib import Path
import copy,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from game_keybind_ops.documents import Document
from game_keybind_ops.core import compile_changes,validate_spec
from game_keybind_ops.deps import Error

RAW=b'\xef\xbb\xbfconfigVersion 19\r\n// keep\r\nbindset 0\r\nunbindall\r\nbindMulti "R" "_shield"\r\nbindMulti "R" "_spear"\r\nbindMulti "H" "_hint"\r\nbindMulti "MOUSE1" "_attack"\r\nbindset 5\r\nunbindall\r\nbindMulti "R" "_menu"\r\nr_swapInterval "1"\r\n'
def spec(root,doc):
    vocab={k:k for k in ('R','H','U','MOUSE1')}
    return {'schema_version':1,'target_id':'fixture-idtech','game_id':'synthetic-doom','root':str(root),
      'relative':'fixture.cfg','adapter':'idtech-bindset','inventory_complete':True,'stopped_processes':['synthetic.exe'],
      'evidence':'Synthetic format fixture, not gameplay acceptance.',
      'fields':[{'id':'field-'+str(i),'selector':c.selector,'keys':vocab,'collision_group':c.group,
                 'linked_group':'bundle' if c.selector.get('command') in ('_shield','_spear') else '',
                 'locked':c.value=='MOUSE1'} for i,c in enumerate(doc.cells) if c.writer=='token']}

class IdTechTests(unittest.TestCase):
    def test_roundtrip_and_separate_contexts(self):
        d=Document(RAW,'idtech-bindset');self.assertEqual(d.render([]),RAW)
        self.assertEqual(d.select({'bindset':5,'kind':'bindMulti','command':'_menu','occurrence':0}).value,'R')
        self.assertEqual(d.select({'header':'configVersion'}).value,19)
    def test_bundle_swap_preserves_mouse_cvars_bom_and_other_set(self):
        d=Document(RAW,'idtech-bindset')
        with tempfile.TemporaryDirectory() as t:
            s=validate_spec(spec(Path(t),d));out,diff=compile_changes(RAW,s,{'field-1':'H','field-2':'H','field-3':'U'})
        expected=RAW.replace(b'"R" "_shield"',b'"H" "_shield"').replace(b'"R" "_spear"',b'"H" "_spear"').replace(b'"H" "_hint"',b'"U" "_hint"')
        self.assertEqual(out,expected);self.assertEqual(len(diff),3)
    def test_partial_bundle_and_new_collisions_refused(self):
        d=Document(RAW,'idtech-bindset')
        with tempfile.TemporaryDirectory() as t:
            s=validate_spec(spec(Path(t),d))
            for changes in ({'field-1':'U'},{'field-1':'H','field-2':'H'}):
                with self.assertRaises(Error):compile_changes(RAW,s,changes)
    def test_unlisted_collision_still_refused(self):
        d=Document(RAW,'idtech-bindset')
        with tempfile.TemporaryDirectory() as t:
            s=spec(Path(t),d);s['fields']=[f for f in s['fields'] if f['id']!='field-3']
            with self.assertRaises(Error):compile_changes(RAW,validate_spec(s),{'field-1':'H','field-2':'H'})
    def test_future_reset_duplicate_and_exec_syntax_refused(self):
        for raw in (RAW.replace(b'19',b'20',1),RAW.replace(b'unbindall\r\n',b'',1),RAW+b'bindset 0\r\nunbindall\r\n',RAW+b'exec "other.cfg"\r\n',RAW+b'bind "F" "_x"\r\n'):
            with self.assertRaises(Error):Document(raw,'idtech-bindset')
    def test_occurrences_and_secondary_are_explicit(self):
        raw=RAW.replace(b'r_swapInterval',b'bindSecondary "U" "_menu"\r\nbindMulti "H" "_menu"\r\nr_swapInterval')
        d=Document(raw,'idtech-bindset')
        self.assertEqual(d.select({'bindset':5,'kind':'bindMulti','command':'_menu','occurrence':1}).value,'H')
        self.assertEqual(d.select({'bindset':5,'kind':'bindSecondary','command':'_menu','occurrence':0}).value,'U')

if __name__=='__main__':unittest.main()
