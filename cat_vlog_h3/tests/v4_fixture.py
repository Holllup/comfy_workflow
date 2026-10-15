import copy
import json
from pathlib import Path


def v4_story():
    source = Path(__file__).resolve().parents[1] / "examples/rainy_day_cat_story.json"
    story = copy.deepcopy(json.loads(source.read_text()))
    story["schema_version"] = 4
    for character in story["characters"].values():
        character["wardrobe"] = None
    for shot in story["shots"]:
        shot.pop("action_timeline_zh", None)
        shot.update({
            "duration_seconds": 175 / 24,
            "reference_assets": [],
            "first_frame_zh": "小猫在左侧，两后爪稳落地，前爪自然弯曲，闭嘴看向前方。",
            "background_prompt_en": "A few softly blurred human students remain behind the cat.",
            "mouth_policy": {item["character_id"]: "closed" for item in shot["cast"]},
            "states": {"start": "The cat is grounded, paws lowered and mouth closed.",
                       "end": "The cat is grounded, paws lowered and mouth closed."},
            "action_segments": [{"start_seconds": 0, "end_seconds": 175 / 24,
                                 "from_state": "start", "to_state": "end",
                                 "action_en": "Raise one forepaw slowly, then return it to the chest and settle.",
                                 "action_zh": "慢慢举起一只前爪，再收回胸前稳定停住。"}],
            "motion_prompt_en": "VIEW: full-body cat shot. CAMERA: a small smooth push toward the cat; no cuts.",
        })
        shot["audio"]["cat_vocalizations_prompt_en"] = ""
    return story
