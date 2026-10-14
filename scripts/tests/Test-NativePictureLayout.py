"""Viewport size contracts; separate from actual native AHK acceptance."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from GameToolUnifiedPanel import native_viewport_size

class Viewport(unittest.TestCase):
    def test_wide_uses_available_size(self):
        self.assertEqual(native_viewport_size((1250, 920), (700, 785)), (1250, 920))
    def test_narrow_uses_scrollable_minimum(self):
        self.assertEqual(native_viewport_size((520, 430), (700, 785)), (700, 785))
    def test_bad_owner_metadata_uses_classic_minimum(self):
        for value in [(0, 0), (True, 785), (9000, 785), (700, "785"), (700,)]:
            self.assertEqual(native_viewport_size((600, 400), value), (976, 733))
    def test_extreme_canvas_is_bounded(self):
        self.assertEqual(native_viewport_size((90000, 90000), (700, 785)), (8192, 8192))

if __name__ == "__main__":
    unittest.main()
