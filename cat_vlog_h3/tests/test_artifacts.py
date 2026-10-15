import unittest
import json
from pathlib import Path

from cat_vlog_h3.core import validate_story


ROOT = Path(__file__).resolve().parents[1]


class DeliveredStoryboardTests(unittest.TestCase):
    def test_example_story_is_usable_by_all_ten_lanes(self):
        path = ROOT / "examples" / "rainy_day_cat_story.json"
        self.assertTrue(path.is_file())
        story = validate_story(path.read_text(encoding="utf-8"))
        self.assertEqual(len(story["shots"]), 10)
        self.assertTrue({"follow", "selfie", "pov"} <= {shot["camera_mode"] for shot in story["shots"]})
        self.assertTrue(all(len(shot["cast"][0]["views"]) == 2 for shot in story["shots"]))

    def test_delivered_workflow_uses_ten_first_frames_and_no_pilot(self):
        self.assertFalse((ROOT / "workflows/00_pilot_1x7s_h3_cu128.json").exists())
        for name, expected_h3 in (("01_one_pass_10x7s_h3_cu128.json", 10),):
            path = ROOT / "workflows" / name
            self.assertTrue(path.is_file(), name)
            graph = json.loads(path.read_text(encoding="utf-8"))
            types = [node["type"] for node in graph["nodes"]]
            self.assertEqual(types.count("MiniMaxH3ImageToVideo"), expected_h3)
            self.assertEqual(types.count("VAEDecodeAudio"), expected_h3)
            self.assertEqual(types.count("CatH3SaveFrame"), expected_h3)


if __name__ == "__main__":
    unittest.main()
