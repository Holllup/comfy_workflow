import json
import unittest

import numpy as np

from masterpiece_flight.core import fit_canvas, hold_frames, parse_plan


def example_plan(count=4):
    return {
        "painting_observation_zh": "旋涡夜空、柏树、村庄",
        "historical_caveat_zh": "想象重构，不等于实景复原",
        "shots": [
            {
                "beat_zh": f"镜头 {i + 1} 向村庄飞行",
                "keyframe_prompt": f"Painted village vantage {i + 1}",
                "motion_prompt": f"Continuous camera flight {i + 1}",
            }
            for i in range(count)
        ],
    }


class MasterpieceCoreTests(unittest.TestCase):
    def test_story_plan_accepts_fenced_json_but_rejects_missing_motion(self):
        plan = example_plan()
        self.assertEqual(parse_plan("```json\n" + json.dumps(plan) + "\n```", 4), plan)
        plan["shots"][2]["motion_prompt"] = ""
        with self.assertRaisesRegex(ValueError, "motion_prompt"):
            parse_plan(json.dumps(plan), 4)

    def test_story_plan_rejects_wrong_number_of_shots(self):
        with self.assertRaisesRegex(ValueError, "4"):
            parse_plan(json.dumps(example_plan(3)), 4)

    def test_canvas_contains_entire_source_image_without_cropping(self):
        painting = np.zeros((2, 4, 3), dtype=np.float32)
        painting[:, 0] = [1, 0, 0]
        painting[:, 3] = [0, 0, 1]
        result = fit_canvas(painting, 8, 8)
        self.assertEqual(result.shape, (8, 8, 3))
        np.testing.assert_allclose(result[3, 0], [1, 0, 0], atol=0.02)
        np.testing.assert_allclose(result[3, 7], [0, 0, 1], atol=0.02)

    def test_still_sequence_is_24_frames_of_the_original(self):
        image = np.array([[[0.1, 0.2, 0.3]]], dtype=np.float32)
        result = hold_frames(image, 24)
        self.assertEqual(result.shape, (24, 1, 1, 3))
        np.testing.assert_array_equal(result[0], image)
        np.testing.assert_array_equal(result[-1], image)


if __name__ == "__main__":
    unittest.main()
