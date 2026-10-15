import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from masterpiece_flight2.core import validate_story
from masterpiece_flight2.build_package import build_bundle


ROOT = Path(__file__).resolve().parents[1]


class RealismArtifactTests(unittest.TestCase):
    def test_example_runs_through_public_validator_and_all_prompt_roles(self):
        path = ROOT / 'examples' / 'starry_night_realism_v3.json'
        self.assertTrue(path.is_file(), 'The new reusable example is missing')
        plan = validate_story(path.read_text(encoding='utf-8'))
        self.assertEqual(plan['schema_version'], 3)
        self.assertEqual(len(plan['keyframes']), 5)
        self.assertEqual(len(plan['shots']), 4)
        self.assertIs(plan['morph']['camera_locked'], True)

    def test_bundle_ships_all_v3_runtime_dependencies_and_four_stage_graphs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = build_bundle(Path(tmp) / 'bundle.zip')
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                for file in ('realism.py', 'realism_nodes.py', 'realism_workflows.py', 'README_FLUX_H3.md',
                             'scripts/realism_install.py', 'skills/masterpiece-flight-storyboard/references/story-schema-v3.md'):
                    self.assertIn('masterpiece_flight2/' + file, names)
                stages = [name for name in names if '/workflows/flux_h3_v3/' in name and name.endswith('.json')]
                self.assertEqual(len(stages), 4)


if __name__ == '__main__': unittest.main()
