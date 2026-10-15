"""Storyboard and media helpers for the independent MiniMax H3 cat vlog."""

from __future__ import annotations

import json
import copy
import math
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image


CAMERA_MODES = ("static", "follow", "selfie", "pov")
REFERENCE_VIEWS = ("front", "side", "back", "left45", "right45", "face")
FPS = 24
MAX_PROMPT_CHARS = 24000


def resolve_duration(seconds):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or not math.isfinite(seconds) or not 5 <= seconds <= 10:
        raise ValueError("duration_seconds must be a finite number from 5 to 10")
    block = max(7, min(14, math.floor((seconds * FPS - 5) / 17 + 0.5 + 1e-10)))
    frames = 17 * block + 5
    return {"requested_seconds": seconds, "frames": frames, "seconds": frames / FPS, "fps": FPS}


def parse_shot_selection(value):
    if value == "all":
        return tuple(range(1, 11))
    if not isinstance(value, str) or not value.strip():
        raise ValueError("selected_shots must be all or comma-separated shot numbers")
    selected = []
    for part in value.split(','):
        part = part.strip()
        if not part.isdigit() or not 1 <= int(part) <= 10:
            raise ValueError("selected_shots contains an invalid shot number; use 1–10")
        selected.append(int(part))
    if len(set(selected)) != len(selected):
        raise ValueError("selected_shots contains repeated numbers")
    return tuple(sorted(selected))


def prepare_reference_views(first_sheet: Path, second_sheet: Path, destination: Path) -> dict[str, Path]:
    """Extract faithful, unlabelled crops from the two approved cat contact sheets."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    outputs = {}
    with Image.open(first_sheet) as image:
        image = image.convert("RGB")
        width, height = image.size
        edge1 = round(width * 430 / 1448)
        edge2 = round(width * 1017 / 1448)
        boxes = {
            "front": (8, 18, edge1 - 8, height - 10),
            "side": (edge1 + 8, 18, edge2 - 8, height - 10),
            "back": (edge2 + 8, 18, width - 8, height - 10),
        }
        for name, box in boxes.items():
            path = destination / f"{name}.png"
            image.crop(box).save(path)
            outputs[name] = path
    with Image.open(second_sheet) as image:
        image = image.convert("RGB")
        width, height = image.size
        third = round(width / 3)
        half = round(height / 2)
        label_clearance = max(55, round(height * 0.06))
        boxes = {
            "left45": (third + 8, label_clearance, third * 2 - 8, half - 8),
            "right45": (third * 2 + 8, label_clearance, width - 8, half - 8),
            "face": (third + 8, half + label_clearance, third * 2 - 8, height - 8),
        }
        for name, box in boxes.items():
            path = destination / f"{name}.png"
            image.crop(box).save(path)
            outputs[name] = path
    return outputs


def _nonempty_text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def prepare_roommate_views(sheet: Path, destination: Path) -> dict[str, Path]:
    """Faithful crops from the supplied 1536×1024 roommate triptych; exclude bottom labels."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    boxes = {"front": (8, 8, 488, 919), "side": (508, 8, 1040, 919),
             "back": (1060, 8, 1528, 919), "face": (90, 80, 420, 490)}
    paths = {}
    with Image.open(sheet) as image:
        image = image.convert("RGB")
        for name, box in boxes.items():
            scaled = tuple(round(value * (image.width / 1536 if i % 2 == 0 else image.height / 1024)) for i, value in enumerate(box))
            path = destination / f"{name}.png"
            image.crop(scaled).save(path)
            paths[name] = path
    return paths


def _text_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


CHARACTER_FIELDS = {"name_zh", "identity_prompt_en", "must_not_change_en", "reference_set", "voice_prompt_en", "wardrobe"}
SHOT_FIELDS = {"id", "beat_zh", "time_of_day_zh", "location_zh", "camera_mode", "cast", "duration_seconds",
               "reference_assets", "first_frame_zh", "video_overview_zh", "sound_notes_zh", "background_prompt_en", "states", "action_segments", "mouth_policy",
               "start_image_prompt_en", "motion_prompt_en", "ambience_prompt_en", "audio", "must_preserve_en", "must_avoid_en"}
AUDIO_FIELDS = {"utterances", "diegetic_music_prompt_en", "background_music_prompt_en", "cat_vocalizations_prompt_en"}
UTTERANCE_FIELDS = {"speaker_id", "mode", "language", "text", "delivery_en", "cue_en"}


def _keys(data, allowed, label):
    if not isinstance(data, dict):
        raise ValueError(f"{label} must be an object")
    extra = set(data) - allowed
    if extra:
        raise ValueError(f"{label}: unsupported fields {', '.join(sorted(extra))}")


def validate_story(raw: str) -> dict:
    story = json.loads(raw)
    if not isinstance(story, dict) or story.get("schema_version") != 4:
        raise ValueError("schema_version 4 required: migrate legacy 1/2/3 explicitly; original text is not discarded")
    _keys(story, {"schema_version", "episode", "characters", "shots"}, "story")
    episode = story.get("episode")
    _keys(episode, {"title_zh", "theme_zh", "arc_zh", "visual_style_prompt_en"}, "episode")
    if not all(_nonempty_text(episode.get(k)) for k in ("title_zh", "theme_zh", "arc_zh")):
        raise ValueError("episode requires title_zh, theme_zh and arc_zh")
    characters = story.get("characters")
    if not isinstance(characters, dict) or not characters:
        raise ValueError("characters must define at least one named character ID")
    for cid, character in characters.items():
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", cid):
            raise ValueError(f"Invalid character ID: {cid}")
        _keys(character, CHARACTER_FIELDS, f"characters.{cid}")
        if not all(_nonempty_text(character.get(k)) for k in ("name_zh", "identity_prompt_en")) or not _text_list(character.get("must_not_change_en")):
            raise ValueError(f"characters.{cid} requires name, identity and must_not_change_en")
        if "reference_set" not in character or (character["reference_set"] is not None and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", str(character["reference_set"]))):
            raise ValueError(f"characters.{cid}.reference_set must be a library ID or null for offscreen roles")
        if not isinstance(character.get("voice_prompt_en"), str):
            raise ValueError(f"characters.{cid}.voice_prompt_en must be a string, empty for silent characters")
        if "wardrobe" not in character:
            raise ValueError(f"characters.{cid}.wardrobe is required; use null when no episode outfit is specified")
        wardrobe = character["wardrobe"]
        if wardrobe is not None:
            _keys(wardrobe, {"prompt_en", "must_preserve_en", "reference_asset_id"}, f"characters.{cid}.wardrobe")
            if not _nonempty_text(wardrobe.get("prompt_en")) or not _text_list(wardrobe.get("must_preserve_en")):
                raise ValueError(f"characters.{cid}.wardrobe requires prompt_en and must_preserve_en")
            if "reference_asset_id" not in wardrobe or (wardrobe["reference_asset_id"] is not None and not _nonempty_text(wardrobe["reference_asset_id"])):
                raise ValueError(f"characters.{cid}.wardrobe.reference_asset_id must be an asset ID or null")
            if re.search(r"\bno (?:clothes|clothing)\b", character["identity_prompt_en"], re.I):
                raise ValueError(f"characters.{cid}: move clothing instructions out of body identity before specifying wardrobe")
    shots = story.get("shots")
    if not isinstance(shots, list) or len(shots) != 10 or [s.get("id") if isinstance(s, dict) else None for s in shots] != list(range(1, 11)):
        raise ValueError("Story must have ten ordered shots with ids 1–10")
    for shot in shots:
        label = f"shot {shot['id']}"
        _keys(shot, SHOT_FIELDS, label)
        for key in ("beat_zh", "time_of_day_zh", "location_zh", "start_image_prompt_en", "motion_prompt_en", "ambience_prompt_en", "first_frame_zh"):
            if not _nonempty_text(shot.get(key)):
                raise ValueError(f"{label}.{key} must be nonempty")
        for key in ('video_overview_zh', 'sound_notes_zh'):
            if key in shot and not _nonempty_text(shot[key]):
                raise ValueError(f'{label}.{key} must be nonempty text when present')
        if shot.get("camera_mode") not in CAMERA_MODES:
            raise ValueError(f"{label}.camera_mode must be static, follow, selfie or pov")
        duration = resolve_duration(shot.get("duration_seconds"))
        if not isinstance(shot.get("background_prompt_en"), str):
            raise ValueError(f"{label}.background_prompt_en must be a string")
        cast = shot.get("cast")
        if not isinstance(cast, list) or not 1 <= len(cast) <= 2:
            raise ValueError(f"{label}.cast must contain one or two visible characters")
        visible = []
        for order, item in enumerate(cast):
            _keys(item, {"character_id", "views"}, f"{label}.cast")
            cid = item.get("character_id")
            if cid not in characters or cid in visible:
                raise ValueError(f"{label}.cast has missing or repeated character_id")
            visible.append(cid)
            if not characters[cid]["reference_set"]:
                raise ValueError(f"{label}: visible character {cid} needs reference_set")
            views = item.get("views")
            if not isinstance(views, list) or len(views) != (2 if order == 0 else 1) or any(v not in REFERENCE_VIEWS for v in views) or len(set(views)) != len(views):
                raise ValueError(f"{label}.cast.views: first character needs two distinct views, second needs one")
        for key in ("must_preserve_en", "must_avoid_en"):
            if not _text_list(shot.get(key)):
                raise ValueError(f"{label}.{key} must contain nonempty strings")
        audio = shot.get("audio")
        _keys(audio, AUDIO_FIELDS, f"{label}.audio")
        if not isinstance(audio.get("utterances"), list):
            raise ValueError(f"{label}.audio.utterances must be a list")
        for key in ("diegetic_music_prompt_en", "background_music_prompt_en", "cat_vocalizations_prompt_en"):
            if not isinstance(audio.get(key), str):
                raise ValueError(f"{label}.audio.{key} must be a string (empty when absent)")
        for utterance in audio["utterances"]:
            _keys(utterance, UTTERANCE_FIELDS, f"{label}.utterance")
            speaker = utterance.get("speaker_id")
            if speaker not in characters:
                raise ValueError(f"{label}: unknown speaker_id {speaker}")
            if utterance.get("mode") not in ("speech", "singing", "voiceover"):
                raise ValueError(f"{label}: utterance mode must be speech, singing or voiceover")
            if utterance["mode"] == "speech" and speaker not in visible:
                raise ValueError(f"{label}: offscreen speaker must use voiceover mode")
            if not characters[speaker]["voice_prompt_en"].strip():
                raise ValueError(f"{label}: speaker {speaker} requires voice_prompt_en")
            for key in ("language", "text", "delivery_en", "cue_en"):
                if not _nonempty_text(utterance.get(key)):
                    raise ValueError(f"{label}.utterance.{key} must be nonempty")
            if "<d>" in utterance["text"] or "</d>" in utterance["text"]:
                raise ValueError(f"{label}: utterance text must not contain control tags")
        policy = shot.get("mouth_policy")
        if not isinstance(policy, dict) or set(policy) != set(visible) or any(value not in ("closed", "speech", "expressive") for value in policy.values()):
            raise ValueError(f"{label}.mouth_policy must define closed/speech/expressive for every visible cat")
        for line in audio["utterances"]:
            if line["mode"] != "voiceover" and line["speaker_id"] in policy and policy[line["speaker_id"]] == "closed":
                raise ValueError(f"{label}: closed mouth conflicts with speech or singing")
        if audio["cat_vocalizations_prompt_en"].strip() and all(value == "closed" for value in policy.values()):
            raise ValueError(f"{label}: cat vocalizations conflict with closed mouths")
        states = shot.get("states")
        if not isinstance(states, dict) or not {"start", "end"} <= set(states) or any(not _nonempty_text(value) for value in states.values()):
            raise ValueError(f"{label}.states requires observable start/end states")
        segments = shot.get("action_segments")
        if not isinstance(segments, list) or not segments:
            raise ValueError(f"{label}.action_segments must be a nonempty list")
        previous_time, previous_state = 0.0, "start"
        for segment in segments:
            _keys(segment, {"start_seconds", "end_seconds", "from_state", "to_state", "action_en", "action_zh"}, f"{label}.action_segments")
            start, end = segment.get("start_seconds"), segment.get("end_seconds")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (start, end)):
                raise ValueError(f"{label}: segment times must be finite numbers")
            if abs(start - previous_time) > 0.001 or end <= start or end > duration["seconds"] + 0.001:
                raise ValueError(f"{label}: action segment overlap, gap or overflow beyond {duration['seconds']:.6f}s")
            if segment.get("from_state") != previous_state or segment.get("to_state") not in states:
                raise ValueError(f"{label}: action state chain does not begin from the first frame or previous state")
            if not all(_nonempty_text(segment.get(key)) for key in ("action_en", "action_zh")):
                raise ValueError(f"{label}: each action needs complete English and Chinese descriptions")
            previous_time, previous_state = end, segment["to_state"]
        if abs(previous_time - duration["seconds"]) > 0.001 or previous_state != "end":
            raise ValueError(f"{label}: action timeline must finish in state end at {duration['seconds']:.6f}s")
        references = shot.get("reference_assets")
        if not isinstance(references, list):
            raise ValueError(f"{label}.reference_assets must be a list")
        for item in references:
            _keys(item, {"asset_id", "purpose", "character_id"}, f"{label}.reference_assets")
            if not _nonempty_text(item.get("asset_id")) or item.get("purpose") not in ("identity", "wardrobe", "scene"):
                raise ValueError(f"{label}: reference asset requires an ID and supported purpose")
            if item.get("purpose") == "scene":
                if item.get("character_id") is not None:
                    raise ValueError(f"{label}: scene reference has no character owner")
            elif item.get("character_id") not in visible:
                raise ValueError(f"{label}: reference belongs to a cat absent from this shot")
        requests = reference_requests(story, shot["id"])
        if len(requests) > 6 or len({item["asset_id"] for item in requests}) != len(requests):
            raise ValueError(f"{label}: select at most six unique reference assets")
        if re.search(r"<Video\s*\d+>|<Audio\s*\d+>|<(?:Picture|Image)\s*[2-9]\d*>|(?:provided|attached|uploaded) (?:dance |motion )?video", shot["motion_prompt_en"], re.I):
            raise ValueError(f"{label}: H3 receives only the first frame; video/audio reference is not connected")
        if shot["camera_mode"] == "static" and re.search(r"(?:camera (?:follows|tracks|orbits)|dolly (?:in|out|back|forward))", shot["motion_prompt_en"], re.I):
            raise ValueError(f"{label}: static camera conflicts with camera movement")
        prompt_length_report(story, shot["id"])
    return story


def _shot(story, index):
    if not 1 <= index <= 10:
        raise ValueError("Shot index must be 1–10")
    return story["shots"][index - 1]


def reference_requests(story, index):
    requests = []
    shot = _shot(story, index)
    for cast in shot["cast"]:
        character = story["characters"][cast["character_id"]]
        for view in cast["views"]:
            requests.append({"asset_id": f"{character['reference_set']}_{view}", "purpose": "identity",
                             "character_id": cast["character_id"], "view": view})
    for cast in shot["cast"]:
        wardrobe = story["characters"][cast["character_id"]].get("wardrobe")
        if wardrobe and wardrobe.get("reference_asset_id"):
            requests.append({"asset_id": wardrobe["reference_asset_id"], "purpose": "wardrobe", "character_id": cast["character_id"]})
    requests.extend(dict(item) for item in shot.get("reference_assets", []))
    return requests


def load_reference_catalog(asset_root):
    root = Path(asset_root).resolve()
    definitions = json.loads((root / "asset_catalog.json").read_text(encoding="utf-8"))
    catalog = {}
    for aid, item in definitions.items():
        _keys(item, {"path", "purpose", "owner", "view"}, f"asset {aid}")
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,95}", aid) or item.get("purpose") not in ("identity", "wardrobe", "scene"):
            raise ValueError(f"Invalid asset ID/purpose: {aid}")
        if not isinstance(item.get("path"), str):
            raise ValueError(f"Missing asset path: {aid}")
        path = (root / item["path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError(f"Invalid or missing asset file: {aid}/{item['path']}")
        if (item["purpose"] == "scene" and item.get("owner") is not None) or (item["purpose"] != "scene" and not _nonempty_text(item.get("owner"))):
            raise ValueError(f"Invalid asset owner: {aid}")
        with Image.open(path) as image:
            image.verify()
        catalog[aid] = {**item, "path": str(path)}
    return catalog


def resolve_reference_assets(story, index, catalog):
    requests = reference_requests(story, index)
    if len(requests) > 6 or len({item["asset_id"] for item in requests}) != len(requests):
        raise ValueError(f"shot {index}: at most six unique reference assets")
    resolved = []
    for request in requests:
        aid = request["asset_id"]
        if aid not in catalog:
            raise ValueError(f"shot {index}: unregistered reference asset {aid}")
        asset = catalog[aid]
        expected_owner = None if request["character_id"] is None else story["characters"][request["character_id"]]["reference_set"]
        if asset["purpose"] != request["purpose"] or asset.get("owner") != expected_owner:
            raise ValueError(f"shot {index}: asset purpose/owner mismatch for {aid}")
        if request.get('view') and asset.get('view') and request['view'] != asset['view']:
            raise ValueError(f'shot {index}: asset view mismatch for {aid}')
        resolved.append({**asset, **request})
    return resolved


def wardrobe_prompt(character):
    wardrobe = character.get("wardrobe")
    if wardrobe is None:
        return ""
    authority = "The wardrobe reference controls clothing" if wardrobe["reference_asset_id"] else "The episode clothing description controls clothing"
    return (f"EPISODE WARDROBE: {wardrobe['prompt_en']} Keep {'; '.join(wardrobe['must_preserve_en'])}. "
            f"Identity photos control the face, coat and body only. {authority}; "
            "do not remove the confirmed outfit because an identity photo is unclothed.")


def compose_start_prompt(story, index):
    shot = _shot(story, index)
    style = story["episode"].get("visual_style_prompt_en", "Photorealistic feline fur, real photography, horizontal 16:9.")
    pieces = [f"STYLE: {style}", "Create one static first frame. Each input photo has only its assigned role; source labels are not scene content."]
    for slot, item in enumerate(reference_requests(story, index), 1):
        if item["purpose"] == "identity":
            role = f"approved {item.get('view', 'appearance')} view of character {item['character_id']} for identity reference; face, coat and body only"
        elif item["purpose"] == "wardrobe":
            role = f"wardrobe reference for {item['character_id']}; preserve its outfit, not the source person's or cat's identity"
        else:
            role = "scene reference for room layout, materials and lighting; do not import its foreground subjects"
        pieces.append(f"INPUT IMAGE {slot} [{item['asset_id']}]: {role}.")
    for cast in shot["cast"]:
        cid = cast["character_id"]
        character = story["characters"][cid]
        pieces += [f"CHARACTER {cid}: {character['identity_prompt_en']}", f"IDENTITY TO PRESERVE: {'; '.join(character['must_not_change_en'])}."]
        if wardrobe_prompt(character):
            pieces.append(wardrobe_prompt(character))
    pieces += [f"CAMERA MODE: {shot['camera_mode']}.", f"START FRAME: {shot['start_image_prompt_en']}",
               f"OPENING STATE: {shot['states']['start']}", f"BACKGROUND: {shot['background_prompt_en']}",
               f"MUST PRESERVE: {'; '.join(shot['must_preserve_en'])}.",
               "The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise."]
    return "\n".join(pieces)


def compose_start_negative_prompt(story, index):
    shot = _shot(story, index)
    rules = []
    for text in shot['must_avoid_en']:
        scoped = re.sub(r"human hands", "human hands replacing the cats' paws", text, flags=re.I)
        if re.search(r'human hands|fingers|human torsos|stretched legs|extra (?:limbs|legs)|additional tails', text, re.I):
            scoped = 'On the named cats only: ' + scoped
        rules.append(scoped)
    return "; ".join([*rules, "wrong cat coat markings", "human hands replacing feline paws", "extra limbs on the cats",
                      "blurry fur", "text", "captions", "logos", "visible camera"])


def image_spec(story, index):
    """Everything affecting the first image; deliberately excludes voices and video actions."""
    return {"prompt": compose_start_prompt(story, index), "negative_prompt": compose_start_negative_prompt(story, index),
            "references": reference_requests(story, index), "size": [1344, 768]}


def _speaker_ids(story):
    speakers = {}
    for shot in story["shots"]:
        for utterance in shot["audio"]["utterances"]:
            if utterance["speaker_id"] not in speakers:
                speakers[utterance["speaker_id"]] = f"S{len(speakers) + 1}"
    return speakers


def compose_video_prompt(story, index):
    shot = _shot(story, index)
    visible = [item["character_id"] for item in shot["cast"]]
    subjects = " ".join(f"Visible character {cid}: {story['characters'][cid]['identity_prompt_en']}" for cid in visible)
    camera = "static camera locked throughout the take" if shot["camera_mode"] == "static" else f"{shot['camera_mode']} camera perspective"
    style = story["episode"].get("visual_style_prompt_en", "Live-action-style photorealistic cat vlog")
    body = [f"[Shot 1] {style}, {camera}. Fully preserve the characters, clothes and opening composition in <Picture 1>.",
            subjects, f"FIRST-FRAME STATE: {shot['states']['start']}", f"BACKGROUND: {shot['background_prompt_en']}",
            shot["motion_prompt_en"], f"Maintain {'; '.join(shot['must_preserve_en'])}.",
            "Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs.",
            "The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take."]
    for cid in visible:
        wardrobe = story["characters"][cid].get("wardrobe")
        if wardrobe:
            body.append(f"CLOTHING {cid}: {wardrobe['prompt_en']} Throughout motion keep {'; '.join(wardrobe['must_preserve_en'])}.")
    for segment in shot["action_segments"]:
        body.append(f"{segment['start_seconds']:.3f}–{segment['end_seconds']:.3f}s: {segment['action_en']} "
                    f"End state: {shot['states'][segment['to_state']]}")
    for cid, policy in shot["mouth_policy"].items():
        if policy == "closed":
            body.append(f"Character {cid} acts silently: its lips remain closed, no panting, teeth or tongue.")
        elif policy == "speech":
            body.append(f"Character {cid} opens its mouth only for its own written speech or singing; other times it rests naturally.")
        else:
            body.append(f"Character {cid} uses only the described natural mouth expression or vocalization.")
    speakers = _speaker_ids(story)
    for utterance in shot["audio"]["utterances"]:
        cid = utterance["speaker_id"]
        character = story["characters"][cid]
        identification = f"Character {cid}, {character['identity_prompt_en']} Voice: {character['voice_prompt_en']} ({speakers[cid]})"
        if utterance["mode"] == "voiceover":
            verb = "says in an off-screen voiceover"
        elif utterance["mode"] == "singing":
            verb = "sings" if cid in visible else "sings offscreen"
        else:
            verb = "says"
        line = f"{utterance['cue_en']} {identification}, with {utterance['delivery_en']}, {verb}: <d>[{utterance['language']}] {utterance['text']}</d>"
        if utterance["mode"] == "voiceover" or cid not in visible:
            line += " The speaker remains offscreen; the visible cats do not lip-sync this voiceover."
        elif len(visible) > 1:
            line += " The other visible cat does not lip-sync this speaker's line."
        body.append(line)
    vocalizations = shot["audio"]["cat_vocalizations_prompt_en"].strip()
    body.append("Cat vocalizations: " + vocalizations if vocalizations else "No meows or other unrequested cat vocalizations.")
    if shot["audio"]["diegetic_music_prompt_en"].strip():
        body.append("Music audible within the scene: " + shot["audio"]["diegetic_music_prompt_en"].strip())
    else:
        body.append("Within the scene, only the described voices, physical sounds and ambience are audible.")
    music = shot["audio"]["background_music_prompt_en"].strip() or "N/A"
    return ("For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\n"
            + "integrated_multimodal_description: " + " ".join(body)
            + "\noverall_soundscape: " + shot["ambience_prompt_en"]
            + "\nnon_diegetic_music: " + music)


def prompt_length_report(story, index):
    prompts = {"image_positive": compose_start_prompt(story, index), "image_negative": compose_start_negative_prompt(story, index),
               "video": compose_video_prompt(story, index)}
    for name, text in prompts.items():
        if len(text) > MAX_PROMPT_CHARS:
            raise ValueError(f"shot {index} {name}: {len(text)} characters exceeds project budget {MAX_PROMPT_CHARS}; no text was truncated")
    return {name: {"characters": len(text), "words": len(text.split()), "composer_truncated": False} for name, text in prompts.items()}


def story_review_markdown(story):
    lines = [f"# {story['episode']['title_zh']} · v4 分镜审稿", '', story['episode']['theme_zh'], '', story['episode']['arc_zh'], '',
             '本文件供逐镜审稿。代码与素材检查通过不代表 JoyAI/H3 的样片效果通过；当前模型画质需人工验收。', '']
    cumulative = 0
    for shot in story['shots']:
        timing = resolve_duration(shot['duration_seconds'])
        end = cumulative + timing['frames']
        lines += [f"## 镜头 {shot['id']:02d} · {cumulative / 24:.3f}–{end / 24:.3f}秒", '',
                  f"请求 {shot['duration_seconds']:.3f}秒；实际 {timing['frames']}帧／{timing['seconds']:.3f}秒。剧情：{shot['beat_zh']}", '',
                  '### 首帧图提示词（中文）', '', shot['first_frame_zh'], '',
                  '### 视频生成提示词（中文审稿）', '',
                  shot.get('video_overview_zh', '视频起点为上方已审首帧，服装、身份与空间按首帧保持。机位详情需对照下方英文稿审查。'), '']
        for segment in shot['action_segments']:
            lines.append(f"- {segment['start_seconds']:.3f}–{segment['end_seconds']:.3f}秒：{segment['action_zh']}")
        lines += ['', '嘴部规则：' + '；'.join(f"{story['characters'][cid]['name_zh']}：" + {'closed': '全程自然闭嘴，无喘气、牙齿或舌头',
                    'speech': '只在自己对白或演唱时开口', 'expressive': '仅做本镜明确要求的口部动作或猫叫'}[policy] for cid, policy in shot['mouth_policy'].items()), '',
                  '音效与音乐：' + shot.get('sound_notes_zh', '中文音效说明待审稿；原音效与音乐英文描述保留在下方执行提示词。'), '']
        for line in shot['audio']['utterances']:
            lines.append(f"- {story['characters'][line['speaker_id']]['name_zh']}／{line['mode']}：{line['text']}")
        lines += ['', '### 实际首帧正向／负向及 H3 提示词', '', '```text', compose_start_prompt(story, shot['id']), '',
                  'NEGATIVE:', compose_start_negative_prompt(story, shot['id']), '', compose_video_prompt(story, shot['id']), '```', '']
        cumulative = end
    lines += [f"总长：{cumulative}帧／{cumulative / 24:.3f}秒。前十五秒钩子须按上方真实累计时间审查。", '']
    return '\n'.join(lines)


def migrate_v3_story(source):
    if source.get('schema_version') != 3:
        raise ValueError('This explicit migration accepts schema_version 3 only')
    story = copy.deepcopy(source)
    story['schema_version'] = 4
    for character in story['characters'].values():
        character['wardrobe'] = None
    report = {'source_story': copy.deepcopy(source), 'editorial_review_required': True, 'untimed_shots_requiring_review': [],
              'timing_notes': [], 'quality_status': 'pending'}
    pattern = re.compile(r'(?:ACTION\s+)?(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*s\s*:', re.I)
    for shot in story['shots']:
        duration = 175 / 24
        timeline_zh = shot.pop('action_timeline_zh')
        original_motion = shot['motion_prompt_en']
        matches = list(pattern.finditer(original_motion))
        end_split = re.search(r'END STATE:\s*(.*)', original_motion, re.I)
        end_state = end_split.group(1).strip() if end_split else 'Finish the described action and settle in its resulting position.'
        shot.update({'duration_seconds': duration, 'reference_assets': [], 'background_prompt_en': '',
                     'first_frame_zh': f"{shot['time_of_day_zh']}，{shot['location_zh']}。本镜意图：{shot['beat_zh']}。原首帧指令：{shot['start_image_prompt_en']}",
                     'states': {'start': shot['start_image_prompt_en'], 'end': end_state}, 'action_segments': []})
        if matches:
            shot['motion_prompt_en'] = original_motion[:matches[0].start()].strip() + ' ' + (end_split.group(0) if end_split else '')
            for position, match in enumerate(matches):
                stop = matches[position + 1].start() if position + 1 < len(matches) else (end_split.start() if end_split else len(original_motion))
                action = original_motion[match.end():stop].strip()
                start, end = float(match.group(1)), float(match.group(2))
                final = position == len(matches) - 1
                if final and abs(end - duration) <= 0.01:
                    if end != duration:
                        report['timing_notes'].append(f"shot {shot['id']}: source {end}s is its rounded 175-frame ending; represented exactly as {duration:.6f}s")
                    end = duration
                previous = 'start' if position == 0 else f'after_{position}'
                next_state = 'end' if final else f'after_{position + 1}'
                if not final:
                    shot['states'][next_state] = 'The preceding described action has completed: ' + action
                shot['action_segments'].append({'start_seconds': start, 'end_seconds': end, 'from_state': previous, 'to_state': next_state,
                                               'action_en': action, 'action_zh': timeline_zh[position] if position < len(timeline_zh) else '请对照原动作补全中文审稿。'})
        else:
            report['untimed_shots_requiring_review'].append(shot['id'])
            shot['motion_prompt_en'] = 'Begin at the approved first frame and keep one continuous shot. Perform the full action below.'
            shot['action_segments'] = [{'start_seconds': 0, 'end_seconds': duration, 'from_state': 'start', 'to_state': 'end',
                                       'action_en': original_motion, 'action_zh': '；'.join(timeline_zh)}]
        if re.search(r'CAMERA:\s*(?:fixed|locked|static)', original_motion, re.I):
            shot['camera_mode'] = 'static'
        voice_source = original_motion + ' ' + shot['ambience_prompt_en']
        voice = re.search(r'(?<!no )\b(?:meow|meowing|purr|purring)\b', voice_source, re.I)
        mouth_action = re.search(r'\bin (?:its|the cat.s) mouth\b', original_motion + ' ' + shot['start_image_prompt_en'], re.I)
        shot['audio']['cat_vocalizations_prompt_en'] = ('Only the cat vocalizations explicitly described in the action and ambience: ' + voice_source) if voice else ''
        shot['mouth_policy'] = {}
        for cast in shot['cast']:
            cid = cast['character_id']
            speaking = any(line['speaker_id'] == cid and line['mode'] != 'voiceover' for line in shot['audio']['utterances'])
            shot['mouth_policy'][cid] = 'speech' if speaking else ('expressive' if voice or mouth_action else 'closed')
    validate_story(json.dumps(story, ensure_ascii=False))
    return story, report


def _numpy(value):
    if hasattr(value, "detach"):
        return value.detach().cpu().numpy()
    return np.asarray(value)


def _rgb_frame(frame) -> np.ndarray:
    array = _numpy(frame)
    if array.ndim != 3 or array.shape[-1] not in (3, 4):
        raise ValueError("Video frames must have H×W×3 or H×W×4 shape")
    if array.dtype != np.uint8:
        array = np.rint(np.clip(array, 0, 1) * 255).astype(np.uint8)
    return np.ascontiguousarray(array[..., :3])


def encode_av_clip(frames, audio: dict, path: Path, fps: int = 24) -> Path:
    """Stream RGB video into ffmpeg and mux a trimmed stereo ambient soundtrack."""
    if fps <= 0 or len(frames) < 1:
        raise ValueError("A clip needs frames and a positive frame rate")
    first = _rgb_frame(frames[0])
    height, width = first.shape[:2]
    if width % 2 or height % 2:
        raise ValueError("H.264 input dimensions must be even")
    sample_rate = int(audio["sample_rate"])
    waveform = _numpy(audio["waveform"])
    if waveform.ndim == 3 and waveform.shape[0] == 1:
        waveform = waveform[0]
    if waveform.ndim != 2 or waveform.shape[0] not in (1, 2) or sample_rate <= 0:
        raise ValueError("Audio must be mono or stereo in a [1, channels, samples] batch")
    if waveform.shape[0] == 1:
        waveform = np.repeat(waveform, 2, axis=0)
    duration = len(frames) / fps
    sample_count = round(duration * sample_rate)
    adjusted = np.zeros((2, sample_count), dtype=np.float32)
    take = min(sample_count, waveform.shape[1])
    adjusted[:, :take] = np.clip(waveform[:, :take], -1, 1)
    pcm = np.rint(adjusted.T * 32767).astype("<i2")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", dir=path.parent, delete=False) as handle:
        wav_path = Path(handle.name)
    try:
        with wave.open(str(wav_path), "wb") as writer:
            writer.setnchannels(2)
            writer.setsampwidth(2)
            writer.setframerate(sample_rate)
            writer.writeframes(pcm.tobytes())
        fade = min(0.08, duration / 4)
        command = [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}",
            "-r", str(fps), "-i", "pipe:0", "-i", str(wav_path),
            "-map", "0:v:0", "-map", "1:a:0", "-frames:v", str(len(frames)),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-af", f"afade=t=in:st=0:d={fade:.4f},afade=t=out:st={duration-fade:.4f}:d={fade:.4f}",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(path),
        ]
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for frame in frames:
                process.stdin.write(_rgb_frame(frame).tobytes())
            process.stdin.close()
            error = process.stderr.read().decode("utf-8", errors="replace")
            if process.wait() != 0:
                raise RuntimeError(f"ffmpeg clip encoding failed: {error}")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stderr.close()
        return path
    finally:
        wav_path.unlink(missing_ok=True)


def join_av_clips(
    clips: list[Path], output: Path, fps: int = 24,
    frames_per_clip: int = 175, output_size: tuple[int, int] = (1280, 720),
    frame_counts: list[int] | None = None,
) -> Path:
    """Join independent clips in list order with exact per-shot video/audio durations."""
    if not clips or fps <= 0 or frames_per_clip <= 0:
        raise ValueError("Provide clips, a positive frame rate and frames_per_clip")
    width, height = output_size
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError("Final MP4 dimensions must be positive and even")
    paths = [Path(clip).resolve() for clip in clips]
    counts = list(frame_counts) if frame_counts is not None else [frames_per_clip] * len(paths)
    if len(counts) != len(paths) or any(isinstance(count, bool) or not isinstance(count, int) or count < 1 for count in counts):
        raise ValueError('frame_counts must contain one positive integer for every clip')
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(path)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    filters = []
    for index in range(len(paths)):
        duration = counts[index] / fps
        filters.append(
            f"[{index}:v]fps={fps},trim=end_frame={counts[index]},setpts=PTS-STARTPTS,"
            f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[v{index}]"
        )
        filters.append(
            f"[{index}:a]aresample=48000,apad,atrim=0:{duration:.8f},"
            f"asetpts=PTS-STARTPTS[a{index}]"
        )
    pairs = "".join(f"[v{index}][a{index}]" for index in range(len(paths)))
    filters.append(f"{pairs}concat=n={len(paths)}:v=1:a=1[v][a]")
    command = ["ffmpeg", "-y", "-loglevel", "error"]
    for path in paths:
        command.extend(("-i", str(path)))
    command.extend((
        "-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
        "-frames:v", str(sum(counts)),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", str(output),
    ))
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"ffmpeg join failed: {result.stderr}")
    return output
