"""The Hub must allow its declared reviewed pages and reject unknown code names."""
import ast,importlib.util,sys,unittest
from pathlib import Path
SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
class Tests(unittest.TestCase):
    def test_every_literal_page_call_is_allowlisted(self):
        tree=ast.parse((SCRIPTS/'Game-Tool-Hub.py').read_text(encoding='utf-8'))
        loader=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='load_catalog_module')
        allowed=next(set(ast.literal_eval(n.comparators[0]))for n in ast.walk(loader)if isinstance(n,ast.Compare)and isinstance(n.ops[0],ast.NotIn))
        used={n.args[0].value for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Name)and n.func.id=='load_catalog_module'and n.args and isinstance(n.args[0],ast.Constant)}
        self.assertFalse(used-allowed,'A declared reviewed page cannot load')
    def test_unknown_modules_remain_refused(self):
        spec=importlib.util.spec_from_file_location('profiles_loader_regression',SCRIPTS/'Game-Tool-Hub.py');hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)
        with self.assertRaises(ValueError):hub.load_catalog_module('UnreviewedHelper')
if __name__=='__main__':unittest.main()
