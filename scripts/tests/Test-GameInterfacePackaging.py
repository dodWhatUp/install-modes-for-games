import ast,importlib.util,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from GameToolInterfaceViews import InterfacePreference
spec=importlib.util.spec_from_file_location('interface_builder',Path(__file__).parents[1]/'Build-GameInterfaceRelease.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
SOURCE=b"class Integration:\n    def __init__(self):\n        self.routes['mod-controls']=self.mod_controls\n        self.runtime_owner='newer extension preserved'\n    def can_close(self):\n        return self.runtime.can_close()\n    def close(self):\n        self.runtime.close()\n"
class Tests(unittest.TestCase):
    def test_hub_literal_optional_calls_match_its_reviewed_allowlist(self):
        tree=ast.parse((Path(__file__).parents[1]/'Game-Tool-Hub.py').read_text(encoding='utf-8'))
        loader=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='load_catalog_module')
        allowed=next(set(ast.literal_eval(n.comparators[0]))for n in ast.walk(loader)if isinstance(n,ast.Compare)and isinstance(n.ops[0],ast.NotIn))
        used={n.args[0].value for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='load_catalog_module'and n.args and isinstance(n.args[0],ast.Constant)}
        self.assertFalse(used-allowed,'A declared optional page is refused by the Hub loader')
    def test_profiles_loader_fix_keeps_unknown_modules_refused(self):
        raw=b'''def load_catalog_module(name):
    if name not in {"Original"}:raise ValueError("Unsupported")
    return name
def page():return load_catalog_module('GameToolGameProfilesUI')
'''
        scope={};exec(builder.enable_profiles_page(raw),scope);self.assertEqual(scope['page'](),'GameToolGameProfilesUI')
        with self.assertRaises(ValueError):scope['load_catalog_module']('UnknownHelper')
    def test_patch_preserves_newer_runtime_owner_and_line_endings(self):
        for raw in [SOURCE,SOURCE.replace(b'\n',b'\r\n')]:
            updated=builder.integrate_owner(raw);self.assertIn(b"self.runtime_owner='newer extension preserved'",updated);self.assertIn(b'self.runtime.close()',updated);self.assertIn(b'self.runtime.can_close()',updated);self.assertEqual(b'\r\n' in updated,b'\r\n' in raw)
    def test_unknown_hook_or_duplicate_install_is_refused(self):
        with self.assertRaises(ValueError):builder.integrate_owner(SOURCE.replace(b'def close(self)',b'def finish(self)'))
        with self.assertRaises(ValueError):builder.integrate_owner(builder.integrate_owner(SOURCE))
    def test_preference_default_unknown_fields_and_explicit_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'view.json';p=InterfacePreference(path);self.assertEqual(p.read()['interface'],'Existing');self.assertFalse(path.exists());path.write_text(json.dumps({'schema_version':1,'interface':'Existing','extra':{'keep':True}}));p.select('New');self.assertEqual(p.read()['extra'],{'keep':True});self.assertEqual(p.read()['interface'],'New')
    def test_corrupt_preference_is_retained_without_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'view.json';path.write_bytes(b'broken');p=InterfacePreference(path)
            with self.assertRaises(ValueError):p.select('New')
            self.assertEqual(path.read_bytes(),b'broken')
    def test_invalid_selection_keeps_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=InterfacePreference(Path(tmp)/'view.json')
            with self.assertRaises(ValueError):p.select('invalid')
            self.assertFalse(p.path.exists())
if __name__=='__main__':unittest.main()
