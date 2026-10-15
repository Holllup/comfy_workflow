import importlib
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_realism import story_v3
from masterpiece_flight2.realism import ProjectStore


class RealismNodeTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('masterpiece_flight2.realism_nodes'))
        self.n = importlib.import_module('masterpiece_flight2.realism_nodes')
        self.temp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get('ART_PROJECT_ROOT')
        os.environ['ART_PROJECT_ROOT'] = self.temp.name
        self.store = ProjectStore(Path(self.temp.name), 'demo')
        self.token = self.store.initialize(json.dumps(story_v3()), np.full((4, 4, 3), 90, np.uint8), (8, 4))
        self.store.save_draft('art', np.zeros((4, 8, 3), np.uint8), self.token)
        for i in range(1, 4):
            self.store.save_draft(f'r5_candidate_{i}', np.full((4, 8, 3), 30 + i, np.uint8), self.token)

    def tearDown(self):
        if hasattr(self, 'temp'):
            if self.previous is None: os.environ.pop('ART_PROJECT_ROOT', None)
            else: os.environ['ART_PROJECT_ROOT'] = self.previous
            self.temp.cleanup()

    def test_endpoint_loader_requires_current_review_code(self):
        loader = self.n.ArtV3LoadEndpoints()
        with self.assertRaisesRegex(ValueError, 'approved'):
            loader.run('demo', 2, '')
        code = self.store.review_code('endpoints', 2)
        result = loader.run('demo', 2, code)
        self.assertEqual(tuple(result[0].shape), (1, 4, 8, 3))
        self.assertAlmostEqual(float(result[0][0, 0, 0, 0]), 32 / 255, places=6)
        self.store.save_draft('r5_candidate_2', np.full((4, 8, 3), 99, np.uint8), self.token)
        with self.assertRaisesRegex(ValueError, 'approval_code'):
            loader.run('demo', 2, code)

    def test_old_prepare_rejects_v3_instead_of_silently_using_four_frames(self):
        from masterpiece_flight2.nodes import ArtPrepare
        with self.assertRaisesRegex(ValueError, 'ArtV3Prepare'):
            ArtPrepare().run(np.zeros((1, 4, 4, 3), np.float32), 'wrong_pipeline', json.dumps(story_v3()))

    def test_frame_prompt_describes_real_adjacent_view_and_morph_is_locked(self):
        prompt, seed = self.n.ArtV3Prompt().run('demo', self.token, 'frame4', 100, 0)
        self.assertIn('photoreal', prompt.lower())
        self.assertIn('R5', prompt)
        self.assertIn('solid depth', prompt)
        self.assertNotIn('abstract shuffled', prompt)
        morph, _ = self.n.ArtV3Prompt().run('demo', self.token, 'morph', 100, 0)
        self.assertIn('locked', morph.lower())
        self.assertIsInstance(seed, int)

    def test_keyframe_stage_requires_explicit_morph_approval(self):
        self.store.approve_endpoints(1)
        self.store.save_clip('morph', np.zeros((124, 4, 8, 3), np.uint8), self.token, {'seed': 1})
        loader = self.n.ArtV3KeyframeStart()
        with self.assertRaisesRegex(ValueError, 'approved'):
            loader.run('demo', '')
        result = loader.run('demo', self.store.review_code('morph'))
        self.assertEqual(tuple(result[0].shape), (1, 4, 8, 3))

    def test_full_loader_does_not_promote_unreviewed_frames(self):
        self.store.approve_endpoints(1)
        self.store.save_clip('morph', np.zeros((124, 4, 8, 3), np.uint8), self.token, {'seed': 1})
        self.store.approve_morph()
        for i in (4, 3, 2, 1): self.store.save_draft(f'r{i}', np.full((4, 8, 3), i, np.uint8), self.token)
        loader = self.n.ArtV3LoadFrames()
        with self.assertRaisesRegex(ValueError, 'approved'):
            loader.run('demo', '')
        result = loader.run('demo', self.store.review_code('frames'))
        self.assertEqual(len(result), 8)
        self.assertAlmostEqual(float(result[0][0, 0, 0, 0]), 1 / 255, places=6)


if __name__ == '__main__': unittest.main()
