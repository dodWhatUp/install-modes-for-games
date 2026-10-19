"""Browser semantics/keyboard/layout acceptance; run in the isolated guest."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SCRIPTS))
from game_system_control.inventory import load_context
from game_system_control.report import accessible_report
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright=None


@unittest.skipUnless(sync_playwright,"Browser acceptance uses the existing isolated guest runtime.")
class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver=sync_playwright().start()
        cls.browser=cls.driver.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close();cls.driver.stop()

    def setUp(self):
        self.root=SCRIPTS.parent/"examples/system-control"
        self.doc=load_context(self.root/"context.example.json")
        self.page=self.browser.new_page(viewport={"width":1100,"height":760})
        self.requests=[];self.page.on("request",lambda r:self.requests.append(r.url))
        self.page.set_content(accessible_report(self.doc,self.root))

    def tearDown(self):
        self.page.close()

    def test_semantic_regions_filter_status_and_escape(self):
        p=self.page
        self.assertEqual(p.get_by_role("main").count(),1)
        self.assertEqual(p.get_by_role("navigation",name="Report sections").count(),1)
        box=p.get_by_role("searchbox",name="Filter report records");box.fill("unknown")
        self.assertEqual(p.get_by_role("status").inner_text(),"1 matching records")
        self.assertIn("Example computer B",p.locator("body").inner_text())
        self.assertNotIn("Example computer A",p.locator("body").inner_text())
        box.press("Escape")
        self.assertEqual(box.input_value(),"")
        self.assertIn("Example computer A",p.locator("body").inner_text())

    def test_native_keyboard_tab_and_enter_expand_source(self):
        p=self.page;box=p.get_by_role("searchbox",name="Filter report records")
        box.focus();p.keyboard.press("Tab")
        self.assertEqual(p.evaluate("document.activeElement.tagName"),"SUMMARY")
        p.keyboard.press("Enter")
        self.assertTrue(p.locator("section li details").first.get_attribute("open") is not None)
        self.assertIn("instructions.example.md",p.locator("section li details[open]").inner_text())
        p.keyboard.press("Enter")
        self.assertIsNone(p.locator("section li details").first.get_attribute("open"))

    def test_narrow_long_name_and_large_text_have_no_horizontal_overflow(self):
        self.doc["nodes"][0]["label"]="Long source label "+"context "*100
        self.page.set_viewport_size({"width":390,"height":844})
        self.page.set_content(accessible_report(self.doc,self.root))
        self.page.evaluate("document.documentElement.style.fontSize='200%'")
        self.page.locator("section li summary").first.click()
        self.assertLessEqual(self.page.evaluate("document.documentElement.scrollWidth"),390)
        self.assertTrue(self.page.get_by_role("searchbox",name="Filter report records").is_visible())

    def test_stale_missing_unknown_labels_survive_filtering(self):
        self.doc["sources"][0]["sha256"]="0"*64
        node=deepcopy(self.doc["nodes"][0]);node.update(id="missing-node",label="Missing source",source_id="missing-source")
        self.doc["nodes"].append(node)
        self.doc["sources"].append({"id":"missing-source","owner":"fixture","locator":"absent.md","binding":"selected_project","sha256":"0"*64,"availability":"missing"})
        self.page.set_content(accessible_report(self.doc,self.root))
        box=self.page.get_by_role("searchbox",name="Filter report records");box.fill("unreadable")
        self.assertIn("Missing source",self.page.locator("body").inner_text())
        box.fill("stale")
        self.assertIn("Example computer A",self.page.locator("body").inner_text())
        box.fill("unknown")
        self.assertIn("live connection not observed",self.page.locator("body").inner_text())

    def test_no_private_session_body_or_network_request(self):
        self.doc["activities"][0]["goal"]="PRIVATE-NO-STORE-CANARY"
        self.page.set_content(accessible_report(self.doc,self.root))
        self.assertNotIn("PRIVATE-NO-STORE-CANARY",self.page.content())
        self.assertNotIn("Authored detail",self.page.content())
        self.assertEqual(self.requests,[])


if __name__=="__main__":
    unittest.main(verbosity=2)
