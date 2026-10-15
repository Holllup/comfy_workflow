import copy
import json
import unittest

from cat_vlog_h3 import core
from v4_fixture import v4_story


def legacy_story():
    story = v4_story()
    story['schema_version'] = 3
    for character in story['characters'].values():
        character.pop('wardrobe', None)
    for shot in story['shots']:
        for key in ('duration_seconds', 'reference_assets', 'first_frame_zh', 'background_prompt_en', 'states', 'action_segments', 'mouth_policy'):
            shot.pop(key)
        shot['audio'].pop('cat_vocalizations_prompt_en')
        shot['action_timeline_zh'] = ['0–2秒：轻轻举爪', '2–7.29秒：收回并停住']
        shot['motion_prompt_en'] = 'VIEW: full body. CAMERA: fixed. ACTION 0–2s: Gently raise one paw. 2–7.29s: Return the paw and settle. END STATE: Both paws lowered.'
    return story


class V4MigrationTests(unittest.TestCase):
    def test_migration_keeps_dialogue_music_and_original_source_for_review(self):
        self.assertTrue(hasattr(core, 'migrate_v3_story'))
        old = legacy_story()
        old['characters']['protagonist']['voice_prompt_en'] = 'Warm Mandarin voice.'
        old['shots'][0]['audio'].update({'utterances': [{'speaker_id': 'protagonist', 'mode': 'speech', 'language': 'Chinese',
                                                      'text': '我再试一次。', 'delivery_en': 'Quietly.', 'cue_en': 'After the paw returns.'}],
                                       'background_music_prompt_en': 'Slow warm piano.'})
        original = copy.deepcopy(old)
        migrated, report = core.migrate_v3_story(old)
        self.assertEqual(old, original)
        self.assertEqual(report['source_story'], original)
        self.assertTrue(report['editorial_review_required'])
        self.assertEqual(core.validate_story(json.dumps(migrated))['schema_version'], 4)
        self.assertEqual(core.resolve_duration(migrated['shots'][0]['duration_seconds'])['frames'], 175)
        self.assertEqual(migrated['shots'][0]['audio']['utterances'], old['shots'][0]['audio']['utterances'])
        prompt = core.compose_video_prompt(migrated, 1)
        for text in ('Gently raise one paw.', 'Return the paw and settle.', '我再试一次。', 'Slow warm piano.'):
            self.assertIn(text, prompt)

    def test_untimed_legacy_motion_is_retained_as_one_explicit_segment(self):
        self.assertTrue(hasattr(core, 'migrate_v3_story'))
        old = legacy_story()
        old['shots'][0]['motion_prompt_en'] = 'The cat sniffs a leaf, takes one small step and then looks up.'
        migrated, report = core.migrate_v3_story(old)
        self.assertEqual(migrated['shots'][0]['action_segments'][0]['action_en'], old['shots'][0]['motion_prompt_en'])
        self.assertEqual(migrated['shots'][0]['action_segments'][0]['end_seconds'], 175 / 24)
        self.assertIn(1, report['untimed_shots_requiring_review'])

    def test_explicit_meow_and_mouth_prop_action_are_not_replaced_by_closed_mouth_rules(self):
        old = legacy_story()
        old['shots'][0]['motion_prompt_en'] = 'The cat gently takes a ribbon in its mouth, releases it and gives one soft meow.'
        migrated, _ = core.migrate_v3_story(old)
        self.assertEqual(migrated['shots'][0]['mouth_policy']['protagonist'], 'expressive')
        self.assertTrue(migrated['shots'][0]['audio']['cat_vocalizations_prompt_en'])


if __name__ == '__main__':
    unittest.main()
