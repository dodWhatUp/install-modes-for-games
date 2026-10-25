import unittest
from floating import popup_rectangle


class Placement(unittest.TestCase):
    def test_corners_edges_and_negative_monitor_coordinates(self):
        for area in ((0, 0, 1920, 1040), (-1920, -200, 0, 840)):
            left, top, right, bottom = area
            for pointer in ((left, top), (right - 1, bottom - 1),
                            (left + 250, top + 150), (right - 50, top + 50)):
                width, height, x, y = popup_rectangle(pointer, (610, 570), area)
                self.assertGreaterEqual(x, left + 8)
                self.assertGreaterEqual(y, top + 8)
                self.assertLessEqual(x + width, right - 8)
                self.assertLessEqual(y + height, bottom - 8)
                self.assertLessEqual(min(abs(pointer[0] - x), abs(pointer[0] - x - width)), 20)

    def test_large_popup_is_bounded_by_work_area(self):
        self.assertEqual(popup_rectangle((50, 50), (1500, 1400), (0, 0, 800, 600)),
                         (784, 584, 8, 8))


if __name__ == '__main__':
    unittest.main(verbosity=2)
