import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from cat_vlog_h3 import core, nodes
from v4_fixture import v4_story


def make_catalog(root):
    definitions = {}
    for aid, purpose, owner, color in (("protagonist_front", "identity", "protagonist", "red"),
                                      ("protagonist_face", "identity", "protagonist", "green"),
                                      ("pink_skirt", "wardrobe", "protagonist", "pink"),
                                      ("studio", "scene", None, "blue")):
        Image.new("RGB", (32, 48), color).save(root / f"{aid}.png")
        definitions[aid] = {"path": f"{aid}.png", "purpose": purpose, "owner": owner}
    (root / "asset_catalog.json").write_text(json.dumps(definitions))
    return definitions


class V4ReferenceTests(unittest.TestCase):
    def test_photo_pack_contains_only_selected_assets_with_correct_roles(self):
        self.assertTrue(hasattr(core, "load_reference_catalog"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_catalog(root)
            catalog = core.load_reference_catalog(root)
            story = v4_story()
            story["characters"]["protagonist"]["wardrobe"] = {
                "prompt_en": "A pink skirt only.", "must_preserve_en": ["fixed waist"], "reference_asset_id": "pink_skirt"}
            story["shots"][0]["reference_assets"] = [{"asset_id": "studio", "purpose": "scene", "character_id": None}]
            packed = nodes.CatH3SelectReferences().select(json.dumps(story), 1, catalog)[0]
            self.assertEqual([item["asset_id"] for item in packed], ["protagonist_front", "protagonist_face", "pink_skirt", "studio"])
            self.assertEqual([item["purpose"] for item in packed], ["identity", "identity", "wardrobe", "scene"])
            self.assertEqual(tuple(packed[0]["image"].shape), (1, 48, 32, 3))
            np.testing.assert_array_equal(nodes._array(packed[-1]["image"])[0, 0, 0], [0, 0, 1])
            bad = dict(catalog)
            bad["pink_skirt"] = dict(bad["pink_skirt"], owner="roommate")
            with self.assertRaisesRegex(ValueError, "owner"):
                nodes.CatH3SelectReferences().select(json.dumps(story), 1, bad)
            bad = dict(catalog)
            bad['protagonist_front'] = dict(bad['protagonist_front'], view='back')
            with self.assertRaisesRegex(ValueError, 'view'):
                nodes.CatH3SelectReferences().select(json.dumps(story), 1, bad)

    def test_catalog_rejects_paths_outside_asset_root_and_missing_files(self):
        self.assertTrue(hasattr(core, "load_reference_catalog"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for path in ("../escape.png", "missing.png"):
                (root / "asset_catalog.json").write_text(json.dumps({"bad": {"path": path, "purpose": "scene", "owner": None}}))
                with self.assertRaises(ValueError):
                    core.load_reference_catalog(root)

    def test_encoder_delivers_every_actual_image_and_never_a_placeholder(self):
        self.assertTrue(hasattr(nodes, "CatH3JoyEncode"))
        photos = [{"asset_id": "angle", "purpose": "identity", "image": np.zeros((1, 2, 2, 3))},
                  {"asset_id": "outfit", "purpose": "wardrobe", "image": np.ones((1, 3, 2, 3))}]
        class Clip:
            def tokenize(self, prompt):
                return {"text": [[(n, 1.0) for n in range(len(prompt.split()))]]}
        def encode(clip, prompt, vae, images):
            return [{"prompt": prompt, "images": images}]
        native = types.ModuleType("comfy_extras.nodes_joyimage")
        native._encode = encode
        with patch.dict(sys.modules, {"comfy_extras": types.ModuleType("comfy_extras"), "comfy_extras.nodes_joyimage": native}):
            value = nodes.CatH3JoyEncode().encode(Clip(), object(), "Use both photos for their assigned roles.", photos)[0]
        self.assertEqual(len(value[0]["images"]), 2)
        self.assertIs(value[0]["images"][1], photos[1]["image"])
        self.assertEqual(value[0]["prompt"], "Use both photos for their assigned roles.")

    def test_over_budget_text_stops_before_native_encoding(self):
        class Clip:
            def tokenize(self, prompt):
                return {'text': [[(index, 1.0) for index in range(4097)]]}
        with self.assertRaisesRegex(ValueError, '4096'):
            nodes.CatH3JoyEncode().encode(Clip(), object(), 'A detailed scene.', [{'image': np.zeros((1, 2, 2, 3))}])


if __name__ == "__main__":
    unittest.main()
