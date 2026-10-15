import copy
import importlib
import importlib.util
import json
import tempfile
import unittest
import shutil
import subprocess
from pathlib import Path

import numpy as np


def story_v3():
    frame = {
        'beat_zh': '沿山肩飞行', 'camera_position': 'above a lane',
        'camera_direction': 'toward the ridge', 'camera_path_from_next_frame': 'back off the ridge',
        'shared_landmarks': ['church'], 'transition_object': 'hill shoulder',
        'transition_object_screen_position': 'right 40%', 'entry_state': 'lane',
        'exit_state': 'ridge', 'end_frame_constraints': ['solid depth'],
        'must_preserve': ['church roof'], 'must_not_generate': ['flat painting'],
        'image_prompt_en': 'A cinematic photograph of a village with solid buildings.'}
    shot = {'beat_zh': '绕过山肩', 'start_state': 'lane', 'camera_path': 'forward and up',
            'speed_profile': 'slow then ease out', 'parallax': 'near wall moves faster',
            'environment_motion': 'leaves move', 'transition_approach': 'hill covers right half',
            'final_quarter_target_state': 'match next frame', 'transition_type': 'generic_occlusion',
            'motion_prompt_en': 'A photoreal continuous flight.', 'transition_zh': '山体遮挡'}
    return {'schema_version': 3, 'conditioning_mode': 'photoreal_to_artwork',
            'artwork': {'title': 'Test landscape', 'artist': 'Test', 'year': '1889', 'place': 'imagined village'},
            'source_links': [{'label': 'museum', 'url': 'https://www.moma.org/collection/works/79802'}],
            'verified_context': ['The painting has a village.'], 'imagined_context': ['The lane is invented.'],
            'visual_anchors': ['church', 'ridge'],
            'artwork_extension': {'prompt_en': 'Extend the landscape at the sides in the same painting style.'},
            'keyframes': [dict(copy.deepcopy(frame), id=i) for i in range(1, 6)],
            'shots': [dict(copy.deepcopy(shot), id=i) for i in range(1, 5)],
            'morph': {'camera_locked': True, 'motion_prompt_en': 'With a locked camera, surfaces become pigment.',
                      'material_progression_en': 'Real materials become brushstrokes while landmarks stay still.'}}


class RealismTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('masterpiece_flight2.realism'), 'v3 pipeline is not implemented')
        self.m = importlib.import_module('masterpiece_flight2.realism')

    def project(self, root):
        store = self.m.ProjectStore(root, 'demo')
        token = store.initialize(json.dumps(story_v3()), np.full((4, 4, 3), 90, np.uint8), (8, 4))
        return store, token

    def endpoints(self, store, token):
        art = store.restore_original(np.full((4, 8, 3), 20, np.uint8))
        store.save_draft('art', art, token)
        for i in range(1, 4):
            store.save_draft(f'r5_candidate_{i}', np.full((4, 8, 3), 40 + i, np.uint8), token)
        store.approve_endpoints(2)

    def frames(self, store, token):
        for i in (4, 3, 2, 1):
            store.save_draft(f'r{i}', np.full((4, 8, 3), i, np.uint8), token)
        store.approve_frames()

    def test_v3_requires_five_real_frames_four_flights_and_locked_morph(self):
        self.assertEqual(self.m.validate_story_v3(json.dumps(story_v3()))['schema_version'], 3)
        bad = story_v3(); bad['keyframes'].pop()
        with self.assertRaisesRegex(ValueError, 'five|5'):
            self.m.validate_story_v3(json.dumps(bad))

    def test_public_validator_routes_v3_without_breaking_v2(self):
        from masterpiece_flight2 import core
        try:
            result = core.validate_story(json.dumps(story_v3()))
        except ValueError as exc:
            self.fail(f'public validator rejected v3: {exc}')
        self.assertEqual(len(result['keyframes']), 5)
        bad = story_v3(); bad['morph']['camera_locked'] = False
        with self.assertRaisesRegex(ValueError, 'camera_locked'):
            self.m.validate_story_v3(json.dumps(bad))

    def test_extension_restores_original_pixels_and_preserves_generated_sides(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, _ = self.project(Path(tmp))
            result = store.restore_original(np.full((4, 8, 3), 20, np.uint8))
            np.testing.assert_array_equal(result[:, 2:6], np.full((4, 4, 3), 90, np.uint8))
            np.testing.assert_array_equal(result[:, :2], np.full((4, 2, 3), 20, np.uint8))

    def test_drafts_require_explicit_approval_and_selected_endpoint_is_loaded(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp))
            store.save_draft('art', store.restore_original(np.zeros((4, 8, 3), np.uint8)), token)
            with self.assertRaisesRegex(ValueError, 'approved'):
                store.load_approved('art')
            self.endpoints(store, token)
            self.assertEqual(int(store.load_approved('r5')[0, 0, 0]), 42)
            self.frames(store, token)
            self.assertEqual(int(store.load_approved('r1')[0, 0, 0]), 1)

    def test_changed_story_invalidates_approvals_and_old_queue_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            changed = story_v3(); changed['shots'][0]['camera_path'] = 'turn left'
            newer = store.initialize(json.dumps(changed), np.full((4, 4, 3), 90, np.uint8), (8, 4))
            self.assertNotEqual(token, newer)
            with self.assertRaisesRegex(ValueError, 'approved'):
                store.load_approved('r5')
            with self.assertRaisesRegex(ValueError, 'stale'):
                store.save_draft('art', np.zeros((4, 8, 3), np.uint8), token)

    def test_story_file_edit_cannot_reuse_old_project_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            changed = story_v3(); changed['morph']['motion_prompt_en'] = 'Different transformation'
            (store.path / 'story_v3.json').write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'story.*changed'):
                store.load_approved('r5')

    def test_changed_source_image_resets_approvals(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            newer = store.initialize(json.dumps(story_v3()), np.full((4, 4, 3), 150, np.uint8), (8, 4))
            self.assertNotEqual(token, newer)
            with self.assertRaisesRegex(ValueError, 'approved'):
                store.load_approved('art')

    def test_regenerated_frame_invalidates_dependent_frames_and_flight_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token); self.frames(store, token)
            store.save_clip('flight1', np.zeros((124, 4, 8, 3), np.uint8), token, {'seed': 1})
            store.save_draft('r3', np.full((4, 8, 3), 80, np.uint8), token)
            with self.assertRaisesRegex(ValueError, 'approved|stale'):
                store.load_approved('r2')
            with self.assertRaisesRegex(ValueError, 'approved|stale'):
                store.load_clip('flight1')

    def test_morph_cache_needs_approval_and_is_invalidated_by_endpoint_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            store.save_clip('morph', np.zeros((124, 4, 8, 3), np.uint8), token, {'seed': 3})
            with self.assertRaisesRegex(ValueError, 'approved'):
                store.load_morph()
            store.approve_morph()
            self.assertEqual(store.load_morph().shape, (124, 4, 8, 3))
            self.frames(store, token)
            self.assertEqual(store.load_morph().shape[0], 124)
            store.save_draft('r5_candidate_2', np.full((4, 8, 3), 77, np.uint8), token)
            with self.assertRaisesRegex(ValueError, 'approved|stale'):
                store.load_morph()

    def test_tampered_approved_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            state = store.state()
            path = store.path / state['assets']['r5_candidate_2']['path']
            path.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'changed|stale'):
                store.load_approved('r5')

    def test_review_code_changes_with_the_candidate_being_reviewed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store, token = self.project(Path(tmp)); self.endpoints(store, token)
            self.assertTrue(callable(getattr(store, 'review_code', None)))
            before = store.review_code('endpoints', 2)
            store.save_draft('r5_candidate_2', np.full((4, 8, 3), 70, np.uint8), token)
            self.assertNotEqual(before, store.review_code('endpoints', 2))

    def test_join_has_640_frames_without_duplicate_seam_frames(self):
        clips = [np.full((124, 2, 4, 3), i, np.uint8) for i in range(1, 6)]
        for i in range(1, 5): clips[i][0] = 99
        result = list(self.m.iter_joined_frames(clips, np.full((2, 4, 3), 8, np.uint8)))
        self.assertEqual(len(result), 640)
        self.assertEqual(int(result[123][0, 0, 0]), 1)
        self.assertEqual(int(result[124][0, 0, 0]), 2)
        self.assertEqual(int(result[615][0, 0, 0]), 5)
        self.assertEqual(int(result[616][0, 0, 0]), 8)
        self.assertEqual(int(result[-1][0, 0, 0]), 8)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg is required for encoding integration test')
    def test_stream_encoder_produces_silent_video_at_requested_size(self):
        self.assertTrue(callable(getattr(self.m, 'encode_frames', None)))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'a video.mp4'
            self.m.encode_frames((np.full((4, 8, 3), i * 80, np.uint8) for i in range(3)), output, (32, 16))
            result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-of', 'json', str(output)], capture_output=True, text=True, check=True)
            streams = json.loads(result.stdout)['streams']
            self.assertEqual(len(streams), 1)
            self.assertEqual((streams[0]['width'], streams[0]['height'], streams[0]['nb_read_frames']), (32, 16, '3'))


if __name__ == '__main__':
    unittest.main()
