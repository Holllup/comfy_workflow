import copy
import json
import unittest

from cat_vlog_h3 import core
from v4_fixture import v4_story


class V4ContractTests(unittest.TestCase):
    def test_resolves_requested_seconds_before_authoring_actions(self):
        self.assertTrue(hasattr(core, "resolve_duration"), "v4 must resolve legal video length")
        for request, frames in ((5, 124), (6, 141), (8, 192), (10, 243), (175 / 24, 175)):
            result = core.resolve_duration(request)
            self.assertEqual(result["frames"], frames)
            self.assertEqual(result["seconds"], frames / 24)
        self.assertEqual(core.resolve_duration((124 + 141) / 48)["frames"], 141)
        for bad in (True, float("nan"), 4, 11):
            with self.assertRaises(ValueError):
                core.resolve_duration(bad)

    def test_validates_state_chain_timing_and_closed_mouth(self):
        story = v4_story()
        self.assertEqual(core.validate_story(json.dumps(story))["schema_version"], 4)
        for change in ("overlap", "overflow", "start", "speech"):
            invalid = copy.deepcopy(story)
            shot = invalid["shots"][0]
            if change == "overlap":
                shot["action_segments"].append(dict(shot["action_segments"][0], start_seconds=1))
            elif change == "overflow":
                shot["action_segments"][0]["end_seconds"] = 8
            elif change == "start":
                shot["action_segments"][0]["from_state"] = "end"
            else:
                cid = shot["cast"][0]["character_id"]
                invalid["characters"][cid]["voice_prompt_en"] = "A youthful voice."
                shot["audio"]["utterances"] = [{"speaker_id": cid, "mode": "speech", "language": "Chinese",
                                                  "text": "你好", "delivery_en": "Quietly.", "cue_en": "After raising the paw."}]
            with self.assertRaises(ValueError, msg=change):
                core.validate_story(json.dumps(invalid))

    def test_static_camera_action_and_background_survive_prompt_composition(self):
        story = v4_story()
        shot = story["shots"][0]
        shot["camera_mode"] = "static"
        shot["motion_prompt_en"] = "VIEW: front oblique full-body. CAMERA: locked tripod; no motion or cut."
        start = core.compose_start_prompt(story, 1)
        video = core.compose_video_prompt(story, 1)
        self.assertIn("locked", video.lower())
        self.assertNotIn("follow camera", video)
        self.assertIn(shot["action_segments"][0]["action_en"], video)
        self.assertIn(shot["states"]["start"], start)
        self.assertIn(shot["background_prompt_en"], start)
        self.assertIn(shot["background_prompt_en"], video)
        self.assertNotIn("walls and signs remain blank", video)
        self.assertIn("no meows", video.lower())
        self.assertNotIn("; human hands;", core.compose_start_negative_prompt(story, 1))
        self.assertIn('On the named cats only:', core.compose_start_negative_prompt(story, 1))

    def test_references_are_unique_and_wardrobe_has_a_separate_authority(self):
        story = v4_story()
        requests = core.reference_requests(story, 1)
        self.assertEqual(len(requests), 2)
        cid = story["shots"][0]["cast"][0]["character_id"]
        story["characters"][cid]["wardrobe"] = {"prompt_en": "Only a pale pink pleated skirt.",
            "must_preserve_en": ["fixed waistband", "tail outside the skirt"], "reference_asset_id": "pink_skirt"}
        story["shots"][0]["reference_assets"] = [{"asset_id": "studio", "purpose": "scene", "character_id": None}]
        requests = core.reference_requests(story, 1)
        self.assertEqual([item["purpose"] for item in requests], ["identity", "identity", "wardrobe", "scene"])
        start = core.compose_start_prompt(story, 1)
        self.assertIn("pink_skirt", start)
        self.assertIn("wardrobe", start.lower())
        self.assertIn("do not remove", start.lower())
        self.assertIn("tail outside the skirt", core.compose_video_prompt(story, 1))

    def test_video_changes_reuse_image_spec_but_start_state_and_clothes_do_not(self):
        story = v4_story()
        original = core.image_spec(story, 1)
        story["shots"][0]["duration_seconds"] = 8
        story["shots"][0]["action_segments"][0]["end_seconds"] = 8
        story["shots"][0]["action_segments"][0]["action_en"] = "Take a small step, then settle."
        story["shots"][0]["audio"]["background_music_prompt_en"] = "Soft piano."
        self.assertEqual(original, core.image_spec(story, 1))
        story["shots"][0]["states"]["start"] += " Left paw already raised."
        self.assertNotEqual(original, core.image_spec(story, 1))

    def test_unconnected_picture_and_invalid_chinese_review_field_are_rejected(self):
        story = v4_story()
        story['shots'][0]['motion_prompt_en'] += ' Use <Picture 2> for the outfit.'
        with self.assertRaisesRegex(ValueError, 'reference'):
            core.validate_story(json.dumps(story))
        story = v4_story()
        story['shots'][0]['video_overview_zh'] = []
        with self.assertRaisesRegex(ValueError, 'video_overview_zh'):
            core.validate_story(json.dumps(story))


if __name__ == "__main__":
    unittest.main()
