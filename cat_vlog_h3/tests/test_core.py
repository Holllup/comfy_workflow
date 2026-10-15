import json
import unittest


def sample_story():
    shots = []
    modes = ("follow", "selfie", "pov", "follow", "follow", "selfie", "pov", "follow", "selfie", "follow")
    for index, mode in enumerate(modes, 1):
        shots.append({
            "id": index,
            "beat_zh": f"小猫探索第 {index} 个地方",
            "time_of_day_zh": "下午",
            "location_zh": f"地点 {index}",
            "camera_mode": mode,
            "cast": [{"character_id": "protagonist", "views": ["front", "face"] if mode != "pov" else ["side", "face"]}],
            "audio": {"utterances": [], "diegetic_music_prompt_en": "", "background_music_prompt_en": "", "cat_vocalizations_prompt_en": "one quiet meow"},
            "duration_seconds": 175 / 24, "reference_assets": [], "first_frame_zh": "小猫站稳，准备探索", "background_prompt_en": "", "mouth_policy": {"protagonist": "expressive"},
            "states": {"start": "Kitten stands grounded.", "end": "Kitten looks back."},
            "action_segments": [{"start_seconds": 0, "end_seconds": 175 / 24, "from_state": "start", "to_state": "end", "action_en": "Walk, sniff, then look back.", "action_zh": "走两步、嗅闻、回头。"}],
            "start_image_prompt_en": f"The same kitten at location {index}, beginning a small adventure.",
            "motion_prompt_en": "The kitten walks, sniffs a safe object, and looks back at the camera.",
            "ambience_prompt_en": "Soft paws on the floor, light breeze and one quiet meow.",
            "must_preserve_en": ["white face blaze", "striped fluffy tail"],
            "must_avoid_en": ["human hands", "extra legs"],
        })
    return {
        "schema_version": 4,
        "episode": {"title_zh": "雨后的一天", "theme_zh": "小猫发现城市的小惊喜", "arc_zh": "从好奇出门到满足回家"},
        "characters": {"protagonist": {
            "name_zh": "团团",
            "reference_set": "protagonist", "voice_prompt_en": "", "wardrobe": None,
            "identity_prompt_en": "The same brown tabby and white kitten, pink nose, white face blaze, chest and paws, fluffy ringed tail.",
            "must_not_change_en": ["coat markings", "face blaze", "eye color"],
        }},
        "shots": shots,
    }


class StoryCoreTests(unittest.TestCase):
    def test_accepts_one_complete_ten_shot_story(self):
        try:
            from cat_vlog_h3.core import validate_story
        except ImportError as exc:
            self.fail(f"cat_vlog_h3.core is not implemented: {exc}")
        plan = validate_story(json.dumps(sample_story(), ensure_ascii=False))
        self.assertEqual(plan["schema_version"], 4)
        self.assertEqual([shot["id"] for shot in plan["shots"]], list(range(1, 11)))

    def test_rejects_shot_without_its_start_image_prompt(self):
        from cat_vlog_h3.core import validate_story
        story = sample_story()
        del story["shots"][3]["start_image_prompt_en"]
        with self.assertRaisesRegex(ValueError, "start_image_prompt_en"):
            validate_story(json.dumps(story, ensure_ascii=False))

    def test_rejects_more_than_two_cat_reference_views_per_shot(self):
        from cat_vlog_h3.core import validate_story
        story = sample_story()
        story["shots"][0]["cast"][0]["views"] = ["front", "side", "face"]
        with self.assertRaisesRegex(ValueError, "cast.views"):
            validate_story(json.dumps(story, ensure_ascii=False))

    def test_rejects_one_reference_view_because_both_image_inputs_are_used(self):
        from cat_vlog_h3.core import validate_story
        story = sample_story()
        story["shots"][0]["cast"][0]["views"] = ["front"]
        with self.assertRaisesRegex(ValueError, "cast.views"):
            validate_story(json.dumps(story, ensure_ascii=False))

    def test_rejects_unrecognized_camera_mode(self):
        from cat_vlog_h3.core import validate_story
        story = sample_story()
        story["shots"][0]["camera_mode"] = "teleport"
        with self.assertRaisesRegex(ValueError, "camera_mode"):
            validate_story(json.dumps(story, ensure_ascii=False))

    def test_prompts_keep_cat_identity_and_ambient_sound_instruction(self):
        try:
            from cat_vlog_h3.core import compose_start_prompt, compose_video_prompt
        except ImportError as exc:
            self.fail(f"Prompt composition is missing: {exc}")
        story = sample_story()
        start = compose_start_prompt(story, 1)
        video = compose_video_prompt(story, 1)
        self.assertIn("white face blaze", start)
        self.assertIn("INPUT IMAGE 1", start)
        self.assertIn("approved face view", start)
        self.assertIn("Soft paws on the floor", video)
        self.assertIn("one quiet meow", video)
        self.assertIn("non_diegetic_music: N/A", video)

    def test_start_prompt_names_selected_non_face_detail_view(self):
        from cat_vlog_h3.core import compose_start_prompt
        story = sample_story()
        story["shots"][0]["cast"][0]["views"] = ["front", "left45"]
        self.assertIn("approved left45 view", compose_start_prompt(story, 1))


if __name__ == "__main__":
    unittest.main()
