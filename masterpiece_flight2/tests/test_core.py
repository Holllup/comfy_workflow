import json
import tempfile
import unittest
from pathlib import Path

import numpy as np


def story():
    return {
        "artwork": {"title": "The Starry Night", "artist": "Vincent van Gogh", "year": "1889", "place": "Saint-Rémy"},
        "source_links": [{"label": "MoMA", "url": "https://www.moma.org/collection/works/79802"}],
        "verified_context": ["The village was not visible from the artist's window."],
        "imagined_context": ["A route through a village inspired by the painting."],
        "visual_anchors": ["cypress", "village", "swirling sky"],
        "keyframes": [
            {"id": i, "beat_zh": f"关键帧{i}", "image_prompt_en": f"Oil painting, flight position {i}"}
            for i in range(1, 5)
        ],
        "shots": [
            {"id": i, "beat_zh": f"镜头{i}", "motion_prompt_en": f"Continuous forward camera flight {i}", "transition_zh": "遮挡衔接"}
            for i in range(1, 5)
        ],
    }


class CoreTests(unittest.TestCase):
    def setUp(self):
        try:
            from masterpiece_flight2 import core
        except ImportError as exc:
            self.fail(f"core module is missing: {exc}")
        self.core = core

    def test_story_accepts_json_fence_and_rejects_missing_motion(self):
        raw = "```json\n" + json.dumps(story()) + "\n```"
        self.assertEqual(self.core.validate_story(raw)["shots"][3]["id"], 4)
        bad = story()
        bad["shots"][2]["motion_prompt_en"] = ""
        with self.assertRaisesRegex(ValueError, "motion_prompt_en"):
            self.core.validate_story(json.dumps(bad))

    def test_story_requires_four_ordered_keyframes_and_sources(self):
        bad = story()
        bad["keyframes"][1]["id"] = 4
        with self.assertRaisesRegex(ValueError, "keyframes"):
            self.core.validate_story(json.dumps(bad))
        bad = story()
        bad["source_links"] = []
        with self.assertRaisesRegex(ValueError, "source_links"):
            self.core.validate_story(json.dumps(bad))

    def test_canvas_preserves_entire_portrait_and_centered_color_borders(self):
        painting = np.zeros((4, 2, 3), dtype=np.uint8)
        painting[:, 0] = [255, 0, 0]
        painting[:, 1] = [0, 0, 255]
        result = self.core.fit_canvas(painting, 8, 8)
        self.assertEqual(result.shape, (8, 8, 3))
        np.testing.assert_array_equal(result[4, 2], [255, 0, 0])
        np.testing.assert_array_equal(result[4, 5], [0, 0, 255])
        np.testing.assert_array_equal(result[:, 0], np.tile([127, 0, 127], (8, 1)))

    def test_project_rejects_reusing_id_for_different_source(self):
        with tempfile.TemporaryDirectory() as temp:
            painting = np.zeros((4, 4, 3), dtype=np.uint8)
            self.core.init_project(Path(temp), "starry", json.dumps(story()), painting)
            painting[0, 0] = [255, 255, 255]
            with self.assertRaisesRegex(ValueError, "project_id"):
                self.core.init_project(Path(temp), "starry", json.dumps(story()), painting)

    def test_draft_refresh_does_not_overwrite_approved_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            painting = np.zeros((4, 4, 3), dtype=np.uint8)
            self.core.init_project(root, "starry", json.dumps(story()), painting)
            first = np.full((720, 1280, 3), 50, dtype=np.uint8)
            next_draft = np.full((720, 1280, 3), 200, dtype=np.uint8)
            self.core.save_keyframe(root, "starry", 1, first)
            self.core.save_keyframe(root, "starry", 1, next_draft)
            approved = self.core.read_png(root / "starry" / "approved" / "frame_01.png")
            draft = self.core.read_png(root / "starry" / "draft" / "frame_01.png")
            self.assertEqual(int(approved[0, 0, 0]), 50)
            self.assertEqual(int(draft[0, 0, 0]), 200)

    def test_load_project_uses_approved_files_and_requires_all_four(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            painting = np.zeros((4, 4, 3), dtype=np.uint8)
            self.core.init_project(root, "starry", json.dumps(story()), painting)
            frame = np.full((720, 1280, 3), 80, dtype=np.uint8)
            for i in range(1, 5):
                self.core.save_keyframe(root, "starry", i, frame)
            (root / "starry" / "approved" / "frame_03.png").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "frame_03"):
                self.core.load_project(root, "starry")
            self.core.save_keyframe(root, "starry", 3, frame)
            project = self.core.load_project(root, "starry")
            self.assertEqual(len(project["frames"]), 4)
            self.assertEqual(project["ending"].shape, (720, 1280, 3))
            self.assertEqual(project["story"]["artwork"]["title"], "The Starry Night")

    def test_bridge_video_has_exact_approved_start_and_target_frames(self):
        generated = np.zeros((5, 2, 4, 3), dtype=np.uint8)
        generated[:] = [20, 30, 40]
        start = np.full((4, 4, 3), 80, dtype=np.uint8)
        target = np.full((4, 4, 3), 200, dtype=np.uint8)
        result = self.core.bridge_video_frames(generated, start, target, blend_frames=3)
        self.assertEqual(result.shape, (5, 4, 4, 3))
        np.testing.assert_array_equal(result[0], start)
        np.testing.assert_array_equal(result[-1], target)
        self.assertGreater(int(result[-2, 0, 0, 0]), int(result[-3, 0, 0, 0]))


if __name__ == "__main__":
    unittest.main()
