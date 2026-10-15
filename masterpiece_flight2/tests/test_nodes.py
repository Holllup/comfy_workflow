import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_core import story


class NodeTests(unittest.TestCase):
    def setUp(self):
        try:
            from masterpiece_flight2 import nodes
        except ImportError as exc:
            self.fail(f"ComfyUI node module is missing: {exc}")
        self.nodes = nodes
        self.temp = tempfile.TemporaryDirectory()
        self.previous_root = os.environ.get("ART_PROJECT_ROOT")
        os.environ["ART_PROJECT_ROOT"] = self.temp.name

    def tearDown(self):
        if self.previous_root is None:
            os.environ.pop("ART_PROJECT_ROOT", None)
        else:
            os.environ["ART_PROJECT_ROOT"] = self.previous_root
        self.temp.cleanup()

    def test_prepare_saves_full_source_and_tail_frame(self):
        painting = np.full((1, 4, 2, 3), 0.5, dtype=np.float32)
        canvas, raw, project_id = self.nodes.ArtPrepare().run(painting, "starry", json.dumps(story()))
        self.assertEqual(tuple(canvas.shape), (1, 720, 1280, 3))
        self.assertEqual(project_id, "starry")
        self.assertEqual(json.loads(raw)["artwork"]["year"], "1889")
        project = Path(self.temp.name) / "starry"
        self.assertTrue((project / "source.png").exists())
        self.assertTrue((project / "ending.png").exists())
        self.assertTrue((project / "manifest.json").exists())

    def test_frame_fields_and_saved_approved_roundtrip(self):
        painting = np.full((1, 4, 2, 3), 0.5, dtype=np.float32)
        self.nodes.ArtPrepare().run(painting, "starry", json.dumps(story()))
        fields = self.nodes.ArtFrameText().run(json.dumps(story()), 3, 100)
        self.assertEqual(fields, ("Oil painting, flight position 3", 103))
        for i in range(1, 5):
            frame = np.full((1, 720, 1280, 3), i / 10, dtype=np.float32)
            returned, path = self.nodes.ArtSaveKeyframe().run(frame, "starry", i)
            self.assertEqual(tuple(returned.shape), tuple(frame.shape))
            self.assertTrue(Path(path).exists())
        result = self.nodes.ArtLoadApproved().run("starry")
        self.assertEqual(len(result), 7)
        self.assertEqual(tuple(result[0].shape), (1, 720, 1280, 3))
        self.assertEqual(self.nodes.ArtMotionText().run(result[5], 4)[0], "Continuous forward camera flight 4")
        self.assertEqual(self.nodes.ArtOutputPrefix().run(result[6], "final"), ("masterpiece_flight2/starry/final",))
        project = Path(self.temp.name) / "starry"
        self.assertTrue((project / "render_settings.json").exists())
        self.assertEqual(json.loads((project / "manifest.json").read_text())["status"], "approved_loaded")

    def test_hold_repeats_original_frame_for_one_second(self):
        image = np.full((1, 2, 3, 3), 0.75, dtype=np.float32)
        batch = self.nodes.ArtHoldFrames().run(image, 24)[0]
        self.assertEqual(tuple(batch.shape), (24, 2, 3, 3))
        np.testing.assert_array_equal(np.asarray(batch[0]), image[0])
        np.testing.assert_array_equal(np.asarray(batch[-1]), image[0])

    def test_approved_file_change_invalidates_loader_cache(self):
        painting = np.full((1, 4, 2, 3), 0.5, dtype=np.float32)
        self.nodes.ArtPrepare().run(painting, "starry", json.dumps(story()))
        frame = np.zeros((1, 720, 1280, 3), dtype=np.float32)
        for i in range(1, 5):
            self.nodes.ArtSaveKeyframe().run(frame, "starry", i)
        before = self.nodes.ArtLoadApproved.IS_CHANGED("starry")
        path = Path(self.temp.name) / "starry" / "approved" / "frame_02.png"
        from PIL import Image
        Image.fromarray(np.full((720, 1280, 3), 128, dtype=np.uint8)).save(path)
        after = self.nodes.ArtLoadApproved.IS_CHANGED("starry")
        self.assertNotEqual(before, after)

    def test_bridge_node_returns_video_batch_at_original_canvas_size(self):
        generated = np.full((5, 2, 4, 3), 0.2, dtype=np.float32)
        start = np.full((1, 4, 4, 3), 0.4, dtype=np.float32)
        target = np.full((1, 4, 4, 3), 0.8, dtype=np.float32)
        images = self.nodes.ArtBridgeFrames().run(generated, start, target, 3)[0]
        self.assertEqual(tuple(images.shape), (5, 4, 4, 3))
        np.testing.assert_allclose(np.asarray(images[0]), start[0], atol=1 / 255)
        np.testing.assert_allclose(np.asarray(images[-1]), target[0], atol=1 / 255)

    def test_wan_loader_records_actual_generation_model(self):
        painting = np.full((1, 4, 2, 3), 0.5, dtype=np.float32)
        self.nodes.ArtPrepare().run(painting, "starry", json.dumps(story()))
        frame = np.zeros((1, 720, 1280, 3), dtype=np.float32)
        for i in range(1, 5):
            self.nodes.ArtSaveKeyframe().run(frame, "starry", i)
        self.nodes.ArtLoadApproved().run("starry", "Wan2.2 5B TI2V")
        settings = json.loads((Path(self.temp.name) / "starry" / "render_settings.json").read_text())
        self.assertEqual(settings["video_model"], "Wan2.2 5B TI2V")
        self.assertEqual(settings["latent_height"], 704)

    def test_wan_video_prefix_is_distinct_from_ltx_output(self):
        self.assertEqual(
            self.nodes.ArtOutputPrefix().run("starry", "wan_final"),
            ("masterpiece_flight2/starry/wan_final",),
        )

    def test_join_frames_keeps_clip_order_and_ends_with_original_hold(self):
        first = np.full((2, 2, 2, 3), 0.1, dtype=np.float32)
        second = np.full((2, 2, 2, 3), 0.2, dtype=np.float32)
        hold = np.full((1, 2, 2, 3), 0.9, dtype=np.float32)
        joined = self.nodes.ArtJoinFrames().run(first, hold, second)[0]
        self.assertEqual(tuple(joined.shape), (5, 2, 2, 3))
        self.assertAlmostEqual(float(joined[0, 0, 0, 0]), 0.1, places=5)
        self.assertAlmostEqual(float(joined[2, 0, 0, 0]), 0.2, places=5)
        self.assertAlmostEqual(float(joined[-1, 0, 0, 0]), 0.9, places=5)

    def test_take_last_frame_preserves_exact_video_tail(self):
        frames = np.zeros((3, 2, 2, 3), dtype=np.float32)
        frames[2] = 0.75
        last = self.nodes.ArtLastFrame().run(frames)[0]
        self.assertEqual(tuple(last.shape), (1, 2, 2, 3))
        np.testing.assert_array_equal(last[0], frames[2])

    def test_one_pass_output_has_its_own_project_prefix(self):
        self.assertEqual(
            self.nodes.ArtOutputPrefix().run("new_painting", "onepass_final"),
            ("masterpiece_flight2/new_painting/onepass_final",),
        )


if __name__ == "__main__":
    unittest.main()
