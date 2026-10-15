import tempfile
import unittest
import zipfile
from pathlib import Path


class CatBundleTests(unittest.TestCase):
    def test_bundle_contains_workflows_character_and_audio_installer_without_model_weights(self):
        try:
            from cat_vlog_h3.build_package import build_bundle
        except ImportError as exc:
            self.fail(f"Installable bundle builder is missing: {exc}")
        with tempfile.TemporaryDirectory() as temp:
            path = build_bundle(Path(temp) / "cat_vlog_h3_bundle.zip")
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                required = {
                    "cat_vlog_h3/__init__.py", "cat_vlog_h3/nodes.py", "cat_vlog_h3/core.py",
                    "cat_vlog_h3/scripts/ensure_models.py", "cat_vlog_h3/assets/character/front.png",
                    "cat_vlog_h3/assets/character/face.png", "cat_vlog_h3/examples/rainy_day_cat_story.json",
                    "cat_vlog_h3/workflows/01_one_pass_10x7s_h3_cu128.json",
                    "cat_vlog_h3/AGENTS.md", "cat_vlog_h3/PROMPT_ChatGPT_十镜编剧.md",
                    "cat_vlog_h3/skills/cat-vlog-storyboard/SKILL.md",
                    "cat_vlog_h3/assets/reference_sets.json", "cat_vlog_h3/assets/roommate/face.png",
                    "cat_vlog_h3/storyboards/dance_club_audition_story.json",
                    "cat_vlog_h3/assets/asset_catalog.json", "cat_vlog_h3/scripts/preflight.py",
                    "cat_vlog_h3/scripts/migrate_story_v4.py", "cat_vlog_h3/acceptance/acceptance_story.json",
                    "cat_vlog_h3/acceptance/README.md",
                    "cat_vlog_h3/skills/cat-vlog-storyboard/references/detailed-prompt-standard.md",
                    "cat_vlog_h3/skills/cat-vlog-storyboard/scripts/resolve_timing.py",
                }
                self.assertTrue(required <= names)
                self.assertFalse(any("pilot" in name for name in names))
                self.assertFalse(any(name.endswith(".safetensors") for name in names))
                self.assertIsNone(archive.testzip())


if __name__ == "__main__":
    unittest.main()
