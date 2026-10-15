import copy
import json
import unittest

from cat_vlog_h3 import core


def native_story():
    characters = {
        "protagonist": {"name_zh": "主角", "identity_prompt_en": "Brown tabby with a white face blaze.",
                        "must_not_change_en": ["white paws"], "reference_set": "protagonist", "wardrobe": None, "voice_prompt_en": "A light youthful Mandarin voice."},
        "roommate": {"name_zh": "室友", "identity_prompt_en": "Silver tabby with a black collar and round pendant.",
                     "must_not_change_en": ["black collar"], "reference_set": "roommate", "wardrobe": None, "voice_prompt_en": "A warmer lower Mandarin voice."},
        "interviewer": {"name_zh": "面试官", "identity_prompt_en": "An unseen dance-club interviewer.",
                        "must_not_change_en": ["remains offscreen"], "reference_set": None, "wardrobe": None, "voice_prompt_en": "A calm adult female Mandarin voice."},
    }
    shots = []
    for i in range(1, 11):
        shots.append({"id": i, "beat_zh": "主角学习动作", "time_of_day_zh": "下午", "location_zh": "排练室",
                      "camera_mode": "follow", "cast": [{"character_id": "protagonist", "views": ["front", "face"]}],
                      "duration_seconds": 175 / 24, "reference_assets": [], "first_frame_zh": "小猫站稳听节奏", "background_prompt_en": "", "mouth_policy": {"protagonist": "closed"},
                      "states": {"start": "Cat stands grounded.", "end": "Cat settles after two steps."},
                      "action_segments": [{"start_seconds": 0, "end_seconds": 175 / 24, "from_state": "start", "to_state": "end", "action_en": "Listen, step twice, settle.", "action_zh": "听拍、踏步、停住。"}],
                      "start_image_prompt_en": "The protagonist stands on the pale oak floor.",
                      "motion_prompt_en": "The camera holds a full-body shot as the protagonist takes two small steps.",
                      "ambience_prompt_en": "Soft paw contacts on wood and quiet room tone.",
                      "audio": {"utterances": [], "diegetic_music_prompt_en": "", "background_music_prompt_en": "", "cat_vocalizations_prompt_en": ""},
                      "must_preserve_en": ["white facial blaze"], "must_avoid_en": ["extra limbs"]})
    return {"schema_version": 4, "episode": {"title_zh": "面试", "theme_zh": "跳舞", "arc_zh": "从紧张到进步"},
            "characters": characters, "shots": shots}


def utterance(speaker="protagonist", mode="speech", text="我准备好了。"):
    return {"speaker_id": speaker, "mode": mode, "language": "Chinese", "text": text,
            "delivery_en": "A short natural delivery.", "cue_en": "After the first step."}


class NativeStoryTests(unittest.TestCase):
    def parse(self, story):
        for shot in story["shots"]:
            for item in shot["cast"]:
                cid = item["character_id"]
                shot["mouth_policy"][cid] = "speech" if any(u["speaker_id"] == cid and u["mode"] != "voiceover" for u in shot["audio"]["utterances"]) else "closed"
        try:
            return core.validate_story(json.dumps(story, ensure_ascii=False))
        except ValueError as error:
            self.fail(f"The native v4 contract must accept this case: {error}")

    def test_audio_modes_use_one_prompt_structure_and_preserve_words(self):
        base = native_story()
        for mode in ("quiet", "ambient", "speech", "duet", "voiceover", "singing", "dance"):
            story = copy.deepcopy(base)
            shot = story["shots"][0]
            if mode == "quiet": shot["ambience_prompt_en"] = "N/A"
            if mode in ("speech", "duet", "voiceover", "singing"):
                shot["audio"]["utterances"] = [utterance(
                    "interviewer" if mode == "voiceover" else "protagonist",
                    mode if mode in ("voiceover", "singing") else "speech", "你好，今天也要开心！")]
            if mode == "duet":
                shot["cast"].append({"character_id": "roommate", "views": ["side"]})
                shot["audio"]["utterances"].append(utterance("roommate", text="我们一起。"))
            if mode == "dance":
                shot["audio"]["diegetic_music_prompt_en"] = "A rehearsal speaker plays a 96 BPM drum groove."
                shot["audio"]["background_music_prompt_en"] = "Sparse piano notes."
            parsed = self.parse(story)
            prompt = core.compose_video_prompt(parsed, 1)
            self.assertEqual(prompt.count("<Picture 1> (from [Shot 1])"), 1)
            for field in ("integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
                self.assertIn(field, prompt)
            self.assertNotIn("no intelligible speech, no music", prompt)
            if shot["audio"]["utterances"]:
                self.assertIn("<d>[Chinese] 你好，今天也要开心！</d>", prompt)
            else:
                self.assertNotIn("<d>", prompt)
            if mode == "singing": self.assertIn("sings", prompt)
            if mode == "voiceover":
                self.assertIn("says in an off-screen voiceover", prompt)
                self.assertIn("lips remain closed", prompt)
            if mode == "duet":
                self.assertIn("<d>[Chinese] 我们一起。</d>", prompt)
                self.assertIn("Character roommate", prompt)
            if mode == "dance":
                self.assertIn("96 BPM drum groove", prompt)
                self.assertIn("non_diegetic_music: Sparse piano notes.", prompt)

    def test_image_inputs_match_cast_and_voice_only_roles_never_leak_into_picture(self):
        story = self.parse(native_story())
        single = core.compose_start_prompt(story, 1)
        self.assertNotIn("Silver tabby", single)
        self.assertNotIn("interviewer", single)
        story["shots"][0]["cast"].append({"character_id": "roommate", "views": ["side"]})
        dual = core.compose_start_prompt(story, 1)
        self.assertIn("INPUT IMAGE 3", dual)
        self.assertIn("Silver tabby", dual)
        self.assertIn("side", dual)
        self.assertNotIn("interviewer", dual)

    def test_rejects_visible_voice_only_actor_and_missing_speaker(self):
        story = native_story()
        story["shots"][0]["cast"].append({"character_id": "interviewer", "views": ["front"]})
        with self.assertRaisesRegex(ValueError, "reference_set"):
            core.validate_story(json.dumps(story))
        story = native_story()
        story["shots"][0]["audio"]["utterances"] = [utterance("unknown")]
        with self.assertRaisesRegex(ValueError, "speaker"):
            core.validate_story(json.dumps(story))

    def test_image_projection_excludes_all_voice_and_music_changes(self):
        story = self.parse(native_story())
        self.assertTrue(hasattr(core, "image_spec"))
        before = core.image_spec(story, 1)
        story["characters"]["protagonist"]["voice_prompt_en"] = "Different voice"
        story["shots"][0]["audio"]["utterances"] = [utterance()]
        story["shots"][0]["audio"]["background_music_prompt_en"] = "A piano song"
        story["shots"][0]["motion_prompt_en"] += " A longer pause."
        self.assertEqual(before, core.image_spec(story, 1))
        story["shots"][0]["start_image_prompt_en"] += " A red hat."
        self.assertNotEqual(before, core.image_spec(story, 1))

    def test_speaker_ids_remain_stable_across_independent_clips(self):
        story = native_story()
        story["shots"][0]["audio"]["utterances"] = [utterance("interviewer", "voiceover")]
        story["shots"][1]["audio"]["utterances"] = [utterance()]
        story["shots"][4]["audio"]["utterances"] = [utterance(text="我再试一次。")]
        story = self.parse(story)
        self.assertIn("(S1)", core.compose_video_prompt(story, 1))
        self.assertIn("(S2)", core.compose_video_prompt(story, 2))
        self.assertIn("(S2)", core.compose_video_prompt(story, 5))


if __name__ == "__main__":
    unittest.main()
