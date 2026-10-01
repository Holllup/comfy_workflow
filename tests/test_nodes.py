import json
import os
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from cat_vlog.nodes import CatFinish, CatImageGate, CatReference, CatSaveClip, CatSaveFrame, CatShotFields, CatStoryPlanner, CatVideoGate, _complete_story
from test_core import sample_story


class ShotNodeTests(unittest.TestCase):
    def test_local_story_adapter_decodes_only_generated_tokens(self):
        class FakeTokenizer:
            eos_token_id = 0

            def apply_chat_template(self, messages, **kwargs):
                self.messages = messages
                return np.array([[10, 11]])

            def decode(self, tokens, **kwargs):
                self.decoded = list(tokens)
                return "six-shot JSON"

        class FakeModel:
            def generate(self, inputs, **kwargs):
                self.options = kwargs
                return np.array([[10, 11, 65, 66]])

        tokenizer, model = FakeTokenizer(), FakeModel()
        seeded = []
        fake_torch = SimpleNamespace(
            random=SimpleNamespace(fork_rng=lambda devices: nullcontext()),
            manual_seed=seeded.append,
            inference_mode=nullcontext,
        )
        with patch.dict(sys.modules, {"torch": fake_torch}):
            with patch("cat_vlog.nodes._load_story_model", return_value=(tokenizer, model)):
                result = _complete_story("cat vlog", 17)
        self.assertEqual(result, "six-shot JSON")
        self.assertEqual(tokenizer.decoded, [65, 66])
        self.assertEqual(seeded, [17])
        self.assertNotIn("generator", model.options)

    def test_planner_creates_a_fresh_story_and_run_id_each_click(self):
        valid = json.dumps(sample_story(), ensure_ascii=False)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CAT_VLOG_ROOT": tmp}):
            with patch("cat_vlog.nodes.secrets.randbits", side_effect=[17, 18]):
                with patch("cat_vlog.nodes._complete_story", return_value=valid):
                    first = CatStoryPlanner().plan("雨天", True, 0)
                    second = CatStoryPlanner().plan("雨天", True, 0)
        self.assertNotEqual(first[1], second[1])
        self.assertEqual((first[2], second[2]), (17, 18))
        self.assertEqual(len(json.loads(first[0])["shots"]), 6)

    def test_third_shot_uses_its_own_prompts_and_seeds(self):
        raw = json.dumps(sample_story(), ensure_ascii=False)
        third = CatShotFields().split(raw, 100, 3)
        fourth = CatShotFields().split(raw, 100, 4)
        self.assertIn("scene 3", third[0])
        self.assertIn("scene 3", third[1])
        self.assertNotEqual(third[2:], fourth[2:])

    def test_serial_gates_require_previous_step_completion(self):
        for gate in (CatImageGate(), CatVideoGate()):
            self.assertEqual(gate.allow("cat looks at lens", 17, "shot_01.png", 2), ("cat looks at lens", 17))
            with self.assertRaisesRegex(ValueError, "previous"):
                gate.allow("cat looks at lens", 17, "", 2)


class OutputNodeTests(unittest.TestCase):
    def test_reference_node_keeps_same_cat_across_runs(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CAT_VLOG_ROOT": tmp}):
            first = np.full((1, 8, 6, 3), 0.25, dtype=np.float32)
            next_run = np.full((1, 8, 6, 3), 0.75, dtype=np.float32)
            saved = CatReference().lock(first)[0]
            reused = CatReference().lock(next_run)[0]
            self.assertEqual(saved.shape, (1, 8, 6, 3))
            self.assertTrue(np.allclose(saved, reused))

    def test_saves_each_keyframe_in_the_run_directory(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CAT_VLOG_ROOT": tmp}):
            image = np.full((1, 8, 6, 3), 0.5, dtype=np.float32)
            returned, path = CatSaveFrame().save(image, "run_123", 2)
            self.assertIs(returned, image)
            self.assertEqual(path, str(Path(tmp) / "run_123" / "shot_02.png"))
            self.assertTrue(Path(path).is_file())

    def test_saves_video_segment_and_returns_serial_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CAT_VLOG_ROOT": tmp}):
            frames = np.zeros((121, 16, 16, 3), dtype=np.float32)
            token = CatSaveClip().save(frames, "run_123", 4)[0]
            self.assertEqual(token, str(Path(tmp) / "run_123" / "shot_04.mp4"))
            self.assertTrue(Path(token).is_file())

    def test_final_node_writes_story_and_thirty_second_video(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {"CAT_VLOG_ROOT": tmp}):
            clips = []
            for index in range(1, 7):
                frames = np.zeros((121, 16, 16, 3), dtype=np.float32)
                clips.append(CatSaveClip().save(frames, "run_123", index)[0])
            story = json.dumps(sample_story(), ensure_ascii=False)
            result = CatFinish().finish(*clips, story, "run_123")
            final = Path(result["result"][0])
            self.assertTrue(final.is_file())
            self.assertTrue((final.parent / "story.json").is_file())
            self.assertEqual(json.loads((final.parent / "story.json").read_text())["title"], "小猫的雨天奇遇")


if __name__ == "__main__":
    unittest.main()
