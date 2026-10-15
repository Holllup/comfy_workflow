import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from cat_vlog_h3 import core, nodes
from test_native_story import native_story


class ReferenceBankTests(unittest.TestCase):
    def test_roommate_sheet_extracts_distinct_views_and_removes_label_strip(self):
        self.assertTrue(hasattr(core, "prepare_roommate_views"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sheet = np.zeros((1024, 1536, 3), dtype=np.uint8)
            sheet[:927, :496] = [220, 20, 20]
            sheet[:927, 500:1048] = [20, 210, 20]
            sheet[:927, 1052:] = [20, 20, 220]
            sheet[927:] = 255
            source = root / "sheet.png"
            Image.fromarray(sheet).save(source)
            outputs = core.prepare_roommate_views(source, root / "views")
            self.assertEqual(set(outputs), {"front", "side", "back", "face"})
            for name, color in {"front": (220,20,20), "side": (20,210,20), "back": (20,20,220), "face": (220,20,20)}.items():
                pixels = np.asarray(Image.open(outputs[name]))
                self.assertTrue(np.all(pixels == color), name)

    def test_single_character_uses_only_its_own_photos_and_two_character_uses_roommate(self):
        story = native_story()
        with tempfile.TemporaryDirectory() as directory:
            bank = {}
            for cid, colors in {"protagonist": {"front":"red", "face":"green"}, "roommate": {"side":"blue"}}.items():
                
                for view, color in colors.items():
                    path = Path(directory) / f"{cid}_{view}.png"
                    Image.new("RGB", (300, 500), color).save(path)
                    bank[f"{cid}_{view}"] = {"path": str(path), "purpose": "identity", "owner": cid, "view": view}
            self.assertIn("references", nodes.CatH3SelectReferences.INPUT_TYPES()["required"])
            packed = nodes.CatH3SelectReferences().select(json.dumps(story), 1, bank)[0]
            primary, detail = packed[0]["image"], packed[1]["image"]
            self.assertEqual(len(packed), 2)
            self.assertEqual(tuple(primary.shape), (1,500,300,3))
            story["shots"][0]["cast"].append({"character_id":"roommate", "views":["side"]})
            story["shots"][0]["mouth_policy"]["roommate"] = "closed"
            packed = nodes.CatH3SelectReferences().select(json.dumps(story), 1, bank)[0]
            primary, detail = packed[0]["image"], packed[1]["image"]
            self.assertAlmostEqual(float(nodes._array(packed[2]["image"])[0,10,10,2]), 1.0)
            self.assertAlmostEqual(float(nodes._array(primary)[0,10,10,0]), 1.0)
            self.assertAlmostEqual(float(nodes._array(detail)[0,10,10,1]), 128/255)


if __name__ == "__main__":
    unittest.main()
