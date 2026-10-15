import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from cat_vlog_h3 import nodes, core


REVIEW = "1_生成首帧并审查"
RENDER = "2_已审查_生成视频"


class ReviewFlowTests(unittest.TestCase):
    def setUp(self):
        self.story = json.loads((Path(__file__).resolve().parents[1] / "examples/rainy_day_cat_story.json").read_text())
        self.story["schema_version"] = 4
        for shot in self.story["shots"]:
            shot.pop("end_image_prompt_en", None)
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, CAT_VLOG_H3_OUTPUT_ROOT=self.temp.name)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.temp.cleanup)

    def test_first_only_story_and_explicit_legacy_migration_notice(self):
        parsed = core.validate_story(json.dumps(self.story))
        self.assertEqual(parsed["schema_version"], 4)
        legacy = json.loads(json.dumps(self.story))
        legacy["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "migrate legacy"):
            core.validate_story(json.dumps(legacy))

    def test_review_never_demands_video_inputs_and_render_checks_approval_first(self):
        for cls in (nodes.CatH3SaveAV, nodes.CatH3Finish):
            self.assertTrue(hasattr(cls, "check_lazy_status"), f"{cls.__name__} must disable its upstream branch")
            obj = cls()
            self.assertEqual(obj.check_lazy_status(phase=REVIEW), [])
            self.assertEqual(obj.check_lazy_status(phase=RENDER), ["ready"])
            requested = obj.check_lazy_status(phase=RENDER, ready="approved:" + json.dumps({"selected": list(range(1, 11)), "frames": {"1": {"sha256": "test"}}}))
            self.assertTrue(requested)
        self.assertEqual(nodes.CatH3SaveFrame().check_lazy_status(phase=RENDER), [])
        self.assertEqual(nodes.CatH3SaveFrame().check_lazy_status(phase=REVIEW), ["image"])

    def _prepare_frames(self):
        self.assertTrue(hasattr(nodes.CatH3SaveFrame, "check_lazy_status"))
        raw = json.dumps(self.story)
        normalized, run_id, seed, phase, context, selection = nodes.CatH3Story().prepare(raw, "review_case", 100, REVIEW)
        image = np.full((1, 768, 1344, 3), 0.123, dtype=np.float32)
        paths, keys = {}, {}
        for index in range(1, 11):
            key = nodes.CatH3ShotFields().split(normalized, seed, index, 0)[4]
            result = nodes.CatH3SaveFrame().save(run_id, phase, context, index, key, image)
            paths[f"frame_{index:02d}"] = result["result"][1]
            keys[index] = key
        nodes.CatH3Stage().run(run_id, phase, context, **paths)
        return raw, run_id, context, paths, keys

    def test_render_reloads_reviewed_png_without_generator_and_rejects_tampering(self):
        raw, run_id, context, paths, keys = self._prepare_frames()
        nodes.CatH3Story().prepare(raw, run_id, 100, RENDER, model_quality="accepted")
        result = nodes.CatH3SaveFrame().save(run_id, RENDER, context, 1, keys[1])
        expected = np.asarray(Image.open(paths["frame_01"]), dtype=np.float32)[None] / 255
        np.testing.assert_array_equal(nodes._array(result["result"][0]), expected)
        ready = nodes.CatH3Stage().run(run_id, RENDER, context, **paths)["result"][0]
        self.assertTrue(ready.startswith("approved:"))
        Image.new("RGB", (1344, 768), "red").save(paths["frame_01"])
        marker = nodes.CatH3SaveFrame.IS_CHANGED()
        self.assertNotEqual(marker, marker)  # Always recheck external files, even if graph inputs are cached.
        with self.assertRaisesRegex(ValueError, "review|审查"):
            nodes.CatH3SaveFrame().save(run_id, RENDER, context, 1, keys[1])

    def test_new_story_or_unreviewed_seed_cannot_reuse_old_approval(self):
        raw, run_id, context, paths, keys = self._prepare_frames()
        with self.assertRaisesRegex(ValueError, "review|审查"):
            nodes.CatH3SaveFrame().save(run_id, RENDER, context, 1, "unreviewed-variation")
        self.story["shots"][0]["start_image_prompt_en"] += " New hat."
        with self.assertRaisesRegex(ValueError, "review|审查"):
            nodes.CatH3Story().prepare(json.dumps(self.story), run_id, 100, RENDER, model_quality="accepted")

    def test_audio_and_motion_edits_reuse_review_but_only_changed_image_demands_joyai(self):
        raw, run_id, context, paths, keys = self._prepare_frames()
        self.story["shots"][0]["motion_prompt_en"] += " Hold briefly."
        self.story["shots"][0]["audio"]["background_music_prompt_en"] = "A quiet piano melody."
        self.story["characters"]["protagonist"]["voice_prompt_en"] = "A warm voice."
        updated = nodes.CatH3Story().prepare(json.dumps(self.story), run_id, 100, RENDER, model_quality="accepted")
        self.assertEqual(updated[4], context)
        nodes.CatH3SaveFrame().save(run_id, RENDER, updated[4], 1, keys[1])
        self.story["shots"][0]["start_image_prompt_en"] += " New small bench."
        normalized, _, seed, phase, new_context, _ = nodes.CatH3Story().prepare(json.dumps(self.story), run_id, 100, REVIEW)
        saver = nodes.CatH3SaveFrame()
        for index, expected in ((1, ["image"]), (2, [])):
            key = nodes.CatH3ShotFields().split(normalized, seed, index, 0)[4]
            needed = saver.check_lazy_status(run_id=run_id, phase=phase, context=new_context, index=index, frame_key=key)
            self.assertEqual(needed, expected)

    def test_render_before_first_review_fails_without_generating_images(self):
        with self.assertRaisesRegex(ValueError, "review|审查"):
            nodes.CatH3Story().prepare(json.dumps(self.story), "empty_case", 100, RENDER, model_quality="accepted")

    def test_only_used_reference_photos_invalidate_review(self):
        raw, run_id, context, _, _ = self._prepare_frames()
        bank = nodes._reference_bank()
        changed_photo = Path(self.temp.name) / "changed_reference.png"
        Image.new("RGB", (300, 500), "blue").save(changed_photo)
        bank["roommate_face"]["path"] = str(changed_photo)
        result = nodes.CatH3Story().prepare(raw, run_id, 100, RENDER, bank, model_quality="accepted")
        self.assertEqual(result[4], context)  # This story only casts protagonist.
        bank["protagonist_face"]["path"] = str(changed_photo)
        with self.assertRaisesRegex(ValueError, "review|审查"):
            nodes.CatH3Story().prepare(raw, run_id, 100, RENDER, bank, model_quality="accepted")


if __name__ == "__main__":
    unittest.main()
