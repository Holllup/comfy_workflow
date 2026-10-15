import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


class CharacterReferenceTests(unittest.TestCase):
    def test_extracts_six_unlabelled_views_from_the_two_approved_sheets(self):
        try:
            from cat_vlog_h3.core import prepare_reference_views
        except ImportError as exc:
            self.fail(f"Reference view extraction is missing: {exc}")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = np.full((1086, 1448, 3), 255, dtype=np.uint8)
            first[:, :430] = (230, 20, 20)
            first[:, 434:1015] = (20, 210, 20)
            first[:, 1019:] = (20, 20, 220)
            second = np.full((1295, 1214, 3), 255, dtype=np.uint8)
            second[:640, 405:807] = (230, 200, 20)
            second[:640, 811:] = (180, 20, 190)
            second[650:, 405:807] = (220, 110, 20)
            second[:50] = 0  # synthetic label strip, absent from final views
            second[650:700] = 0
            first_path, second_path = root / "sheet1.png", root / "sheet2.png"
            Image.fromarray(first).save(first_path)
            Image.fromarray(second).save(second_path)
            views = prepare_reference_views(first_path, second_path, root / "views")
            self.assertEqual(set(views), {"front", "side", "back", "left45", "right45", "face"})
            colors = {
                "front": (230, 20, 20), "side": (20, 210, 20), "back": (20, 20, 220),
                "left45": (230, 200, 20), "right45": (180, 20, 190), "face": (220, 110, 20),
            }
            for name, expected in colors.items():
                with Image.open(views[name]) as image:
                    self.assertGreater(image.width, 250)
                    self.assertGreater(image.height, 450)
                    self.assertEqual(image.getpixel((image.width // 2, image.height // 2)), expected)
                    self.assertNotEqual(image.getpixel((image.width // 2, 0)), (0, 0, 0))
            with Image.open(first_path) as image:
                self.assertEqual(image.size, (1448, 1086))


if __name__ == "__main__":
    unittest.main()
