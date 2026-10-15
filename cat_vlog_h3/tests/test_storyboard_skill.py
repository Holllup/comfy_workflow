"""Exercise the Skill CLI against the real cat workflow contract."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]
SCRIPT = PROJECT / "skills/cat-vlog-storyboard/scripts/validate_story.py"


class StoryboardSkillTests(unittest.TestCase):
    def setUp(self):
        self.story = json.loads((PROJECT / "examples/rainy_day_cat_story.json").read_text())

    def run_cli(self, story, *arguments):
        self.assertTrue(SCRIPT.is_file(), "The Skill needs a working project-validation CLI")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "episode.json"
            original = json.dumps(story, ensure_ascii=False)
            source.write_text(original, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--project-root", str(PROJECT), *arguments],
                capture_output=True, text=True,
            )
            self.assertEqual(source.read_text(encoding="utf-8"), original)
            return result

    def test_valid_story_exposes_actual_composed_prompts_without_rewriting_source(self):
        result = self.run_cli(self.story, "--prompts")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(len(report["shots"]), 10)
        self.assertEqual(report['schema_version'], 4)
        self.assertEqual(report['shots'][0]['timing']['frames'], 175)
        self.assertEqual(len(report['shots'][0]['reference_inputs']), 2)
        self.assertFalse(report['model_quality_verified'])
        for source, shot in zip(self.story["shots"], report["shots"]):
            self.assertIn(source["start_image_prompt_en"], shot["start_prompt"])
            self.assertNotIn("end_prompt", shot)
            self.assertIn(source["motion_prompt_en"], shot["video_prompt"])
            self.assertIn(source["ambience_prompt_en"], shot["video_prompt"])
            self.assertIn(source["camera_mode"], shot["video_prompt"])
            for forbidden in source["must_avoid_en"]:
                self.assertIn(forbidden.replace("human hands", "human hands replacing the cats\' paws"), shot["start_negative_prompt"])
                self.assertNotIn(forbidden, shot["start_prompt"])

    def test_rejects_unsupported_duration_instead_of_claiming_it_controls_generation(self):
        self.story["shots"][0]["duration_seconds"] = 4
        result = self.run_cli(self.story)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duration_seconds", result.stderr)

    def test_cat_anatomy_rule_is_scoped_without_false_coverage_failure_on_case(self):
        self.story['shots'][0]['must_avoid_en'] = ['Human hands replacing the cat paws; extra cat limbs']
        result = self.run_cli(self.story, '--prompts')
        self.assertEqual(result.returncode, 0, result.stderr)
        prompt = json.loads(result.stdout)['shots'][0]['start_negative_prompt']
        self.assertIn("human hands replacing the cats' paws", prompt)

    def test_rejects_twelve_shots_and_missing_start_frame_via_real_project_validator(self):
        extra = copy.deepcopy(self.story)
        extra["shots"] += [dict(extra["shots"][-1], id=11), dict(extra["shots"][-1], id=12)]
        result = self.run_cli(extra)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ten", result.stderr)
        del self.story["shots"][0]["start_image_prompt_en"]
        result = self.run_cli(self.story)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("start_image_prompt_en", result.stderr)

    def test_explicit_missing_project_does_not_silently_use_a_different_contract(self):
        result = self.run_cli(self.story, "--project-root", str(PROJECT / "not-a-project"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("project", result.stderr.lower())

    def test_rejects_a_role_view_not_registered_in_the_actual_project(self):
        self.story["characters"]["roommate"] = {
            "name_zh": "室友", "identity_prompt_en": "Silver cat.",
            "must_not_change_en": ["black collar"], "reference_set": "roommate", "wardrobe": None, "voice_prompt_en": ""
        }
        self.story["shots"][0]["cast"].append({"character_id": "roommate", "views": ["left45"]})
        self.story["shots"][0]["mouth_policy"]["roommate"] = "closed"
        result = self.run_cli(self.story)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("roommate_left45", result.stderr)


if __name__ == "__main__":
    unittest.main()
