import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np

from cat_vlog.core import concat_clips, encode_clip, freeze_reference, generate_story, parse_story


TIMES = ["早晨", "上午", "中午", "下午", "傍晚", "夜晚"]


def sample_story():
    return {
        "title": "小猫的雨天奇遇",
        "shots": [
            {
                "time": time,
                "beat_zh": f"第{index}镜的动作",
                "image_prompt": f"Photorealistic orange and white kitten scene {index}",
                "motion_prompt": f"The kitten looks at the camera in scene {index}.",
            }
            for index, time in enumerate(TIMES, 1)
        ],
    }


class StoryContractTests(unittest.TestCase):
    def test_accepts_six_chronological_shots(self):
        result = parse_story(json.dumps(sample_story(), ensure_ascii=False))
        self.assertEqual(result["title"], "小猫的雨天奇遇")
        self.assertEqual([shot["time"] for shot in result["shots"]], TIMES)
        self.assertEqual(len(result["shots"]), 6)

    def test_accepts_json_wrapped_in_markdown_fence(self):
        raw = "```json\n" + json.dumps(sample_story(), ensure_ascii=False) + "\n```"
        self.assertEqual(parse_story(raw)["title"], "小猫的雨天奇遇")

    def test_rejects_missing_sixth_shot(self):
        story = sample_story()
        story["shots"].pop()
        with self.assertRaisesRegex(ValueError, "exactly six"):
            parse_story(json.dumps(story, ensure_ascii=False))

    def test_rejects_nonchronological_timeline(self):
        story = sample_story()
        story["shots"][3]["time"] = "早晨"
        with self.assertRaisesRegex(ValueError, "chronological"):
            parse_story(json.dumps(story, ensure_ascii=False))

    def test_rejects_blank_generation_prompt(self):
        story = sample_story()
        story["shots"][2]["motion_prompt"] = "  "
        with self.assertRaisesRegex(ValueError, "motion_prompt"):
            parse_story(json.dumps(story, ensure_ascii=False))

    def test_retries_invalid_story_once(self):
        responses = iter(['{"shots":[]}', json.dumps(sample_story(), ensure_ascii=False)])
        prompts = []

        def complete(prompt):
            prompts.append(prompt)
            return next(responses)

        story = generate_story("雨天", 17, complete)
        self.assertEqual(len(story["shots"]), 6)
        self.assertEqual(len(prompts), 2)
        self.assertIn("雨天", prompts[0])


class ReferenceTests(unittest.TestCase):
    def test_reuses_first_generated_cat_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cat_reference.png"
            first = np.full((8, 6, 3), 0.25, dtype=np.float32)
            second = np.full((8, 6, 3), 0.75, dtype=np.float32)
            saved = freeze_reference(first, path)
            reused = freeze_reference(second, path)
            self.assertTrue(path.is_file())
            self.assertTrue(np.allclose(saved, reused, atol=1 / 255))
            self.assertLess(float(reused.mean()), 0.3)


class VideoTests(unittest.TestCase):
    def test_encodes_exactly_120_silent_frames(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "shot_01.mp4"
            frames = np.zeros((121, 16, 16, 3), dtype=np.float32)
            encode_clip(frames, path)
            result = subprocess.run(
                ["ffprobe", "-v", "error", "-count_frames", "-show_entries",
                 "stream=codec_type,nb_read_frames,duration", "-of", "json", str(path)],
                check=True, capture_output=True, text=True,
            )
            streams = json.loads(result.stdout)["streams"]
            self.assertEqual(len(streams), 1)
            self.assertEqual(streams[0]["codec_type"], "video")
            self.assertEqual(int(streams[0]["nb_read_frames"]), 120)
            self.assertAlmostEqual(float(streams[0]["duration"]), 5.0)

    def test_concatenates_six_clips_in_story_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for index in range(6):
                path = Path(tmp) / f"shot_{index + 1:02}.mp4"
                encode_clip(np.full((121, 16, 16, 3), index / 6, dtype=np.float32), path)
                paths.append(path)
            final = Path(tmp) / "cat_vlog.mp4"
            concat_clips(paths, final)
            decoded = subprocess.run(
                ["ffmpeg", "-v", "error", "-i", str(final), "-f", "rawvideo",
                 "-pix_fmt", "rgb24", "pipe:1"], check=True, capture_output=True,
            ).stdout
            frames = np.frombuffer(decoded, dtype=np.uint8).reshape(-1, 16, 16, 3)
            self.assertEqual(len(frames), 720)
            means = [float(frames[index * 120 + 60].mean()) for index in range(6)]
            self.assertEqual(means, sorted(means))
            self.assertGreater(means[-1], means[0] + 150)


if __name__ == "__main__":
    unittest.main()
