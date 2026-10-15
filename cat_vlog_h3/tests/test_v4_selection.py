import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from cat_vlog_h3 import core, nodes
from v4_fixture import v4_story


class V4SelectionTests(unittest.TestCase):
    def setUp(self):
        self.story = v4_story()
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, CAT_VLOG_H3_OUTPUT_ROOT=self.temp.name)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.temp.cleanup)

    def test_selection_is_explicit_and_full_video_waits_for_model_acceptance(self):
        self.assertTrue(hasattr(core, "parse_shot_selection"))
        self.assertEqual(core.parse_shot_selection("1,5,7"), (1, 5, 7))
        self.assertEqual(core.parse_shot_selection("all"), tuple(range(1, 11)))
        for invalid in ("", "0", "11", "1,1", "not-a-shot"):
            with self.assertRaises(ValueError):
                core.parse_shot_selection(invalid)
        with self.assertRaisesRegex(ValueError, "quality|验收"):
            nodes.CatH3Story().prepare(json.dumps(self.story), "run", 100, nodes.RENDER,
                                       selected_shots="all", model_quality="pending")

    def _review(self, selected="1,5"):
        result = nodes.CatH3Story().prepare(json.dumps(self.story), "run", 100, nodes.REVIEW,
                                           selected_shots=selected, model_quality="pending")
        raw, run_id, seed, phase, context, selection = result
        paths = {f"frame_{index:02d}": "" for index in range(1, 11)}
        image = np.zeros((1, 768, 1344, 3), dtype=np.float32)
        keys = {}
        for index in core.parse_shot_selection(selected):
            fields = nodes.CatH3ShotFields().split(raw, seed, index)
            keys[index] = fields[4]
            saved = nodes.CatH3SaveFrame().save(run_id, phase, context, index, fields[4], image,
                                               selected_shots=selection)
            paths[f"frame_{index:02d}"] = saved["result"][1]
        nodes.CatH3Stage().run(run_id, phase, context, selected_shots=selection, **paths)
        return raw, context, selection, paths, keys

    def test_partial_review_never_requests_or_approves_missing_other_shots(self):
        self.assertIn("selected_shots", nodes.CatH3Story.INPUT_TYPES()["required"])
        raw, context, selection, paths, keys = self._review()
        saver = nodes.CatH3SaveFrame()
        self.assertEqual(saver.check_lazy_status(phase=nodes.REVIEW, index=2, selected_shots=selection), [])
        skipped = saver.save("run", nodes.REVIEW, context, 2, "unused", selected_shots=selection)
        self.assertEqual(skipped["result"][1], "")
        result = nodes.CatH3Story().prepare(raw, "run", 100, nodes.RENDER,
                                           selected_shots=selection, model_quality="pending")
        ready = nodes.CatH3Stage().run("run", nodes.RENDER, result[4], selected_shots=selection, **paths)["result"][0]
        approved = nodes._approved(ready)
        self.assertEqual(approved["selected"], [1, 5])
        self.assertEqual(nodes.CatH3SaveAV().check_lazy_status(phase=nodes.RENDER, index=2, selected_shots=selection), [])
        review = json.loads((Path(self.temp.name) / "run/review.json").read_text())
        self.assertEqual(set(review["frames"]), {"1", "5"})

    def test_saved_clip_is_reused_only_for_the_same_frame_and_video_conditions(self):
        self.assertIn("video_key", nodes.CatH3SaveAV.INPUT_TYPES()["required"])
        raw, context, selection, paths, keys = self._review("1")
        ready = nodes.CatH3Stage().run("run", nodes.RENDER, context, selected_shots="1", **paths)["result"][0]
        saver = nodes.CatH3SaveAV()
        image = np.broadcast_to(np.zeros((1, 1, 1, 3)), (175, 768, 1344, 3))
        def encode(images, audio, destination, **kwargs):
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(b"a verified encoded clip")
        with patch("cat_vlog_h3.nodes.core.encode_av_clip", side_effect=encode):
            saver.save(nodes.RENDER, "run", 1, ready, image, {}, selected_shots="1", video_key="video-A", frame_count=175)
        self.assertEqual(saver.check_lazy_status(phase=nodes.RENDER, run_id="run", index=1, ready=ready,
                                                selected_shots="1", video_key="video-A", frame_count=175), [])
        self.assertEqual(saver.check_lazy_status(phase=nodes.RENDER, run_id="run", index=1, ready=ready,
                                                selected_shots="1", video_key="video-B", frame_count=175), ["images", "audio"])

    def test_finish_only_joins_ten_matching_clips_in_number_order(self):
        self.assertIn("context", nodes.CatH3Finish.INPUT_TYPES()["required"])
        raw, context, selection, paths, keys = self._review("all")
        ready = nodes.CatH3Stage().run("run", nodes.RENDER, context, selected_shots="all", **paths)["result"][0]
        args = {}
        def encode(images, audio, destination, **kwargs):
            destination.write_bytes(destination.name.encode())
        for index in range(1, 11):
            fields = nodes.CatH3ShotFields().split(raw, 100, index)
            image = np.broadcast_to(np.zeros((1, 1, 1, 3)), (fields[6], 768, 1344, 3))
            with patch("cat_vlog_h3.nodes.core.encode_av_clip", side_effect=encode):
                result = nodes.CatH3SaveAV().save(nodes.RENDER, "run", index, ready, image, {},
                                                 video_key=fields[7], frame_count=fields[6])
            args.update({f"clip_{index:02d}": result[0], f"frame_key_{index:02d}": fields[4], f"video_key_{index:02d}": fields[7]})
        seen = []
        def join(clips, destination, **kwargs):
            seen.extend(path.name for path in clips)
            self.assertEqual(kwargs["frame_counts"], [175] * 10)
            destination.write_bytes(b"final")
        with patch("cat_vlog_h3.nodes.core.join_av_clips", side_effect=AssertionError("model quality still pending")):
            pending = nodes.CatH3Finish().finish(nodes.RENDER, "run", raw, ready, context=context, **args)
        self.assertEqual(pending['result'], ('',))
        manifest_path = Path(self.temp.name) / 'run/manifest.json'
        manifest = json.loads(manifest_path.read_text())
        manifest['model_quality'] = 'accepted'
        manifest_path.write_text(json.dumps(manifest))
        with patch("cat_vlog_h3.nodes.core.join_av_clips", side_effect=join):
            result = nodes.CatH3Finish().finish(nodes.RENDER, "run", raw, ready, context=context, **args)
        self.assertTrue(result["result"][0].endswith("cat_vlog_h3.mp4"))
        self.assertEqual(seen, [f"shot_{index:02d}.mp4" for index in range(1, 11)])
        args["video_key_02"] = "changed"
        with patch("cat_vlog_h3.nodes.core.join_av_clips", side_effect=AssertionError("stale clip was joined")):
            result = nodes.CatH3Finish().finish(nodes.RENDER, "run", raw, ready, context=context, **args)
        self.assertEqual(result["result"], ("",))
        self.assertIn("2", result["ui"]["text"][0])


if __name__ == "__main__":
    unittest.main()
