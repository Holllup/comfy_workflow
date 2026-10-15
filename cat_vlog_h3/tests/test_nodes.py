import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from test_core import sample_story
from cat_vlog_h3 import nodes, NODE_CLASS_MAPPINGS


class CatNodeTests(unittest.TestCase):
    def test_registered_nodes_and_visible_reference_photos(self):
        self.assertTrue(all(hasattr(cls, "INPUT_TYPES") for cls in NODE_CLASS_MAPPINGS.values()))
        result = nodes.CatH3References().load()
        self.assertTrue(nodes.CatH3References.OUTPUT_NODE)
        self.assertIn("images", result["ui"])
        bank, = result["result"]
        self.assertEqual({item["owner"] for item in bank.values()}, {"protagonist", "roommate"})
        self.assertEqual(sum(item["owner"] == "protagonist" for item in bank.values()), 6)
        self.assertEqual({item["view"] for item in bank.values() if item["owner"] == "roommate"}, {"front", "side", "back", "face"})
        self.assertTrue(all(Path(item["path"]).is_file() for item in bank.values()))

    def test_fields_expose_only_start_and_motion_and_variation_changes_frame_key(self):
        raw = json.dumps(sample_story())
        values = nodes.CatH3ShotFields().split(raw, 1234, 2, 0)
        self.assertEqual(len(values), 8)
        self.assertIn("location 2", values[0])
        self.assertIn("non_diegetic_music: N/A", values[1])
        self.assertEqual(values[2:4], (3235, 3237))
        changed = nodes.CatH3ShotFields().split(raw, 1234, 2, 1)
        self.assertNotEqual(changed[4], values[4])
        self.assertEqual(changed[5], values[5])
        self.assertEqual(changed[3], values[3])

    def test_story_rejects_path_escape(self):
        with self.assertRaisesRegex(ValueError, "run_id"):
            nodes.CatH3Story().prepare(json.dumps(sample_story()), "../escape", 100, nodes.REVIEW)

    def test_video_gate_requires_review_and_prior_completion(self):
        image = np.zeros((1, 1, 1, 3))
        clip = type("Clip", (), {"tokenize": lambda self, prompt: {"text": [[(1, 1.0)]]}})()
        ready = "approved:" + json.dumps({"selected": [1, 2], "frames": {"1": {"sha256": "test"}, "2": {"sha256": "test"}}})
        with self.assertRaisesRegex(ValueError, "review"):
            nodes.CatH3VideoGate().allow(image, "review_pending:run", "done", 1, clip, "prompt")
        with self.assertRaisesRegex(ValueError, "prior"):
            nodes.CatH3VideoGate().allow(image, ready, "", 2, clip, "prompt")
        self.assertIs(nodes.CatH3VideoGate().allow(image, ready, "done", 2, clip, "prompt")[0], image)

    def test_review_output_nodes_do_not_write_clips(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, CAT_VLOG_H3_OUTPUT_ROOT=temp):
            self.assertEqual(nodes.CatH3SaveAV().save(nodes.REVIEW, "run", 1), ("skipped:run:1",))
            result = nodes.CatH3Finish().finish(nodes.REVIEW, "run", json.dumps(sample_story()))
            self.assertEqual(result["result"], ("",))
            self.assertFalse(list(Path(temp).rglob("*.mp4")))



if __name__ == "__main__":
    unittest.main()
