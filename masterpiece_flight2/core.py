"""Storyboard validation and local project files, independent of ComfyUI."""

from __future__ import annotations

import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


PROJECT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")


def validate_story(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.IGNORECASE).strip()
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid storyboard JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise ValueError("Storyboard must be a JSON object")
    if plan.get("schema_version") == 3:
        from .realism import validate_story_v3
        return validate_story_v3(text)
    artwork = plan.get("artwork")
    if not isinstance(artwork, dict) or not all(str(artwork.get(k, "")).strip() for k in ("title", "artist", "year", "place")):
        raise ValueError("artwork requires title, artist, year and place")
    links = plan.get("source_links")
    if not isinstance(links, list) or not links or not all(
        isinstance(item, dict) and str(item.get("label", "")).strip() and str(item.get("url", "")).startswith("https://")
        for item in links
    ):
        raise ValueError("source_links must contain cited HTTPS sources")
    for field in ("verified_context", "imagined_context", "visual_anchors"):
        values = plan.get(field)
        if not isinstance(values, list) or not values or not all(isinstance(x, str) and x.strip() for x in values):
            raise ValueError(f"{field} must contain nonempty strings")
    for field, required in (
        ("keyframes", ("beat_zh", "image_prompt_en")),
        ("shots", ("beat_zh", "motion_prompt_en", "transition_zh")),
    ):
        values = plan.get(field)
        if not isinstance(values, list) or len(values) != 4 or [item.get("id") if isinstance(item, dict) else None for item in values] != [1, 2, 3, 4]:
            raise ValueError(f"{field} must contain four ordered items with ids 1–4")
        for item in values:
            for key in required:
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ValueError(f"{field}[{item['id']}].{key} must be nonempty")
    if plan.get("schema_version", 1) >= 2:
        frame_strings = (
            "camera_position", "camera_direction", "camera_path_from_next_frame",
            "transition_object", "transition_object_screen_position", "entry_state", "exit_state",
        )
        frame_lists = ("shared_landmarks", "end_frame_constraints", "must_preserve", "must_not_generate")
        shot_strings = (
            "start_state", "camera_path", "speed_profile", "parallax", "environment_motion",
            "transition_approach", "final_quarter_target_state", "transition_type",
        )
        for frame in plan["keyframes"]:
            for key in frame_strings:
                if not isinstance(frame.get(key), str) or not frame[key].strip():
                    raise ValueError(f"keyframes[{frame['id']}].{key} must be nonempty")
            for key in frame_lists:
                if not isinstance(frame.get(key), list) or not frame[key] or not all(isinstance(value, str) and value.strip() for value in frame[key]):
                    raise ValueError(f"keyframes[{frame['id']}].{key} must be nonempty strings")
        allowed = (
            "hill_occlusion", "steeple_match", "radial_star_halo", "final_artwork_alignment",
            "generic_occlusion", "landmark_match", "radial_light",
        )
        for shot in plan["shots"]:
            for key in shot_strings:
                if not isinstance(shot.get(key), str) or not shot[key].strip():
                    raise ValueError(f"shots[{shot['id']}].{key} must be nonempty")
            if shot["transition_type"] not in allowed:
                raise ValueError(f"shots[{shot['id']}].transition_type is unknown")
    return plan


def compose_image_prompt(frame: dict, index: int, spatial_mode: bool = False) -> str:
    if "camera_position" not in frame:
        return frame["image_prompt_en"]
    if spatial_mode:
        image_1 = (
            "abstract shuffled palette seed with no recognizable original layout"
            if index == 4 else f"newly generated spatial keyframe {index + 1}, nearer the final view"
        )
        image_2 = "not connected; reconstruct volume and landmarks from the visual brief"
    else:
        image_1 = "the canonical original painting" if index == 4 else f"newly generated keyframe {index + 1}, nearer the original painting"
        image_2 = "not connected; use input image 1 as the painting reference" if index == 4 else "the canonical original painting, for style and landmarks"
    spatial_rule = [(
        "SPATIAL RULE",
        "A full-bleed traversable oil-painted environment. Near, middle and far objects have "
        "solid volume, changing occlusion and camera-dependent parallax; no flat painting, "
        "pasted backdrop, canvas edge or static sky plate.",
    )] if spatial_mode else []
    sections = [
        ("INPUT IMAGE 1", image_1), ("INPUT IMAGE 2", image_2), *spatial_rule,
        ("CAMERA POSITION", frame["camera_position"]),
        ("CAMERA DIRECTION", frame["camera_direction"]),
        ("REVERSE CAMERA MOVE FROM INPUT IMAGE 1", frame["camera_path_from_next_frame"]),
        ("SHARED LANDMARKS", "; ".join(frame["shared_landmarks"])),
        ("TRANSITION OBJECT", frame["transition_object"]),
        ("OBJECT SCREEN POSITION AND COVERAGE", frame["transition_object_screen_position"]),
        ("ENTRY STATE", frame["entry_state"]), ("EXIT STATE", frame["exit_state"]),
        ("END FRAME CONSTRAINTS", "; ".join(frame["end_frame_constraints"])),
        ("MUST PRESERVE", "; ".join(frame["must_preserve"])),
        ("MUST NOT GENERATE", "; ".join(frame["must_not_generate"])),
        ("VISUAL BRIEF", frame["image_prompt_en"]),
    ]
    return "\n".join(f"{heading}: {value}" for heading, value in sections)


def compose_motion_prompt(shot: dict) -> str:
    if "start_state" not in shot:
        return shot["motion_prompt_en"]
    sections = [
        ("START STATE", shot["start_state"]),
        ("CAMERA PATH", shot["camera_path"]),
        ("SPEED PROFILE", shot["speed_profile"]),
        ("PARALLAX", shot["parallax"]),
        ("ENVIRONMENT MOTION", shot["environment_motion"]),
        ("TRANSITION APPROACH", shot["transition_approach"]),
        ("FINAL 25% TARGET STATE", shot["final_quarter_target_state"]),
        ("DIRECTOR'S BRIEF", shot["motion_prompt_en"]),
    ]
    return "\n".join(f"{heading}: {value}" for heading, value in sections)


def fit_canvas(image: np.ndarray, width: int = 1280, height: int = 720) -> np.ndarray:
    source = _rgb_uint8(image)
    if width <= 0 or height <= 0:
        raise ValueError("Canvas dimensions must be positive")
    source_height, source_width = source.shape[:2]
    scale = min(width / source_width, height / source_height)
    resized_width = max(1, round(source_width * scale))
    resized_height = max(1, round(source_height * scale))
    resized = np.asarray(Image.fromarray(source).resize((resized_width, resized_height), Image.Resampling.LANCZOS))
    edges = np.concatenate((source[0], source[-1], source[:, 0], source[:, -1]), axis=0)
    border = np.median(edges, axis=0).astype(np.uint8)
    canvas = np.empty((height, width, 3), dtype=np.uint8)
    canvas[:] = border
    x = (width - resized_width) // 2
    y = (height - resized_height) // 2
    canvas[y:y + resized_height, x:x + resized_width] = resized
    return canvas


def spatial_style_seed(image: np.ndarray, width: int = 1344, height: int = 768) -> np.ndarray:
    """Keep the artwork's palette while removing its recognizable layout and border."""
    source = Image.fromarray(_rgb_uint8(image))
    palette = np.asarray(source.resize((24, 14), Image.Resampling.BOX)).copy()
    colors = palette.reshape(-1, 3)
    np.random.default_rng(487201).shuffle(colors)
    wash = Image.fromarray(colors.reshape(14, 24, 3)).resize((width, height), Image.Resampling.BICUBIC)
    return np.asarray(wash.filter(ImageFilter.GaussianBlur(radius=8))).copy()


def bridge_video_frames(
    generated: np.ndarray,
    start: np.ndarray,
    target: np.ndarray,
    blend_frames: int = 8,
) -> np.ndarray:
    """Normalize Wan frames and dissolve their ending into the approved target."""
    frames = np.asarray(generated)
    if frames.ndim != 4 or frames.shape[0] < 2:
        raise ValueError("Video must contain at least two frames")
    start = _rgb_uint8(start)
    target = _rgb_uint8(target)
    if start.shape != target.shape:
        raise ValueError("Start and target keyframes must have identical dimensions")
    height, width = target.shape[:2]
    result = np.empty((frames.shape[0], height, width, 3), dtype=np.uint8)
    for index, frame in enumerate(frames):
        rgb = _rgb_uint8(frame)
        if rgb.shape[:2] != (height, width):
            rgb = np.asarray(Image.fromarray(rgb).resize((width, height), Image.Resampling.BILINEAR))
        result[index] = rgb
    result[0] = start
    blend_count = min(max(1, int(blend_frames)), len(result) - 1)
    for offset in range(blend_count):
        index = len(result) - blend_count + offset
        opacity = (offset + 1) / blend_count
        result[index] = np.rint(
            result[index].astype(np.float32) * (1 - opacity) + target.astype(np.float32) * opacity
        ).astype(np.uint8)
    result[-1] = target
    return result


def bridge_h3_frames(generated: np.ndarray, start: np.ndarray, target: np.ndarray, blend_frames: int = 4) -> np.ndarray:
    """Small endpoint correction for first/last-frame conditioned H3 clips."""
    frames = np.asarray(generated)
    if frames.ndim != 4 or frames.shape[0] < 2:
        raise ValueError("Video must contain at least two frames")
    start, target = _rgb_uint8(start), _rgb_uint8(target)
    if start.shape != target.shape or frames.shape[1:] != start.shape:
        raise ValueError("H3 frames and both anchors must share one native canvas")
    result = np.stack([_rgb_uint8(frame) for frame in frames])
    gap = float(np.mean(np.abs(result[-1].astype(np.float32) - target.astype(np.float32)))) / 255.0
    count = min(len(result) - 1, 2 if gap < 0.04 else max(1, min(int(blend_frames), 12)))
    result[0] = start
    for offset in range(count):
        position = len(result) - count + offset
        alpha = (offset + 1) / count
        result[position] = np.rint(result[position].astype(np.float32) * (1 - alpha) + target.astype(np.float32) * alpha).astype(np.uint8)
    result[-1] = target
    return result


def delivery_canvas(frames: np.ndarray, original: np.ndarray) -> np.ndarray:
    """Fit native H3 frames without pinning the original painting to video edges."""
    video = np.asarray(frames)
    if video.ndim != 4 or video.shape[0] < 1 or video.shape[1:] != (768, 1344, 3):
        raise ValueError("Expected native 1344×768 H3 frames")
    reference = _rgb_uint8(original)
    if reference.shape != (768, 1344, 3):
        raise ValueError("Expected one native H3 original frame")
    result = np.empty((len(video), 720, 1280, 3), dtype=np.uint8)
    for index, frame in enumerate(video):
        resized = np.asarray(Image.fromarray(_rgb_uint8(frame)).resize((1260, 720), Image.Resampling.LANCZOS))
        result[index, :, 10:1270] = resized
        result[index, :, :10] = resized[:, :1]
        result[index, :, 1270:] = resized[:, -1:]
    return result


def _rgb_uint8(image: np.ndarray) -> np.ndarray:
    array = np.asarray(image)
    if array.ndim != 3 or array.shape[2] not in (3, 4) or array.shape[0] == 0 or array.shape[1] == 0:
        raise ValueError("Image must have shape H×W×3 or H×W×4")
    if array.dtype != np.uint8:
        array = np.clip(np.rint(array.astype(np.float32) * 255), 0, 255).astype(np.uint8)
    return np.ascontiguousarray(array[:, :, :3])


def _png_bytes(image: np.ndarray) -> bytes:
    output = io.BytesIO()
    Image.fromarray(_rgb_uint8(image)).save(output, format="PNG")
    return output.getvalue()


def read_png(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB")).copy()


def _project_path(root: Path, project_id: str) -> Path:
    if not PROJECT_RE.fullmatch(project_id):
        raise ValueError("project_id must use letters, digits, _ or - and be at most 64 characters")
    return Path(root) / project_id


def init_project(root: Path, project_id: str, raw_story: str, painting: np.ndarray, canvas_size: tuple[int, int] = (1280, 720)) -> dict:
    project = _project_path(root, project_id)
    story = validate_story(raw_story)
    source = _png_bytes(painting)
    normalized = json.dumps(story, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
    source_hash = hashlib.sha256(source).hexdigest()
    story_hash = hashlib.sha256(normalized).hexdigest()
    manifest_path = project / "manifest.json"
    if manifest_path.exists():
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("source_sha256") != source_hash or old.get("story_sha256") != story_hash or old.get("canvas") != {"width": canvas_size[0], "height": canvas_size[1]}:
            raise ValueError("project_id already belongs to a different image or storyboard; choose a new project_id")
    project.mkdir(parents=True, exist_ok=True)
    (project / "draft").mkdir(exist_ok=True)
    (project / "approved").mkdir(exist_ok=True)
    ending = fit_canvas(_rgb_uint8(painting), *canvas_size)
    (project / "source.png").write_bytes(source)
    (project / "ending.png").write_bytes(_png_bytes(ending))
    (project / "story.json").write_bytes(normalized)
    manifest = {
        "project_id": project_id,
        "artwork": story["artwork"],
        "source_links": story["source_links"],
        "source_sha256": source_hash,
        "story_sha256": story_hash,
        "canvas": {"width": canvas_size[0], "height": canvas_size[1]},
        "status": "keyframes_pending",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"story": story, "ending": ending, "manifest": manifest}


def save_keyframe(root: Path, project_id: str, index: int, image: np.ndarray) -> Path:
    project = _project_path(root, project_id)
    if not (project / "manifest.json").exists():
        raise FileNotFoundError(f"Project {project_id} has not been initialized")
    if index not in (1, 2, 3, 4):
        raise ValueError("Keyframe index must be 1–4")
    array = _rgb_uint8(image)
    manifest = json.loads((project / "manifest.json").read_text(encoding="utf-8"))
    canvas = manifest["canvas"]
    if array.shape[:2] != (canvas["height"], canvas["width"]):
        raise ValueError(f"Approved keyframes must be {canvas['width']}×{canvas['height']}")
    content = _png_bytes(array)
    draft = project / "draft" / f"frame_{index:02d}.png"
    approved = project / "approved" / f"frame_{index:02d}.png"
    draft.write_bytes(content)
    if not approved.exists():
        approved.write_bytes(content)
    return draft


def load_project(root: Path, project_id: str) -> dict:
    project = _project_path(root, project_id)
    story_path = project / "story.json"
    if not story_path.exists():
        raise FileNotFoundError(f"No storyboard for project {project_id}")
    story = validate_story(story_path.read_text(encoding="utf-8"))
    ending = read_png(project / "ending.png")
    frames = []
    for index in range(1, 5):
        path = project / "approved" / f"frame_{index:02d}.png"
        if not path.exists():
            raise FileNotFoundError(f"Missing approved {path.name}")
        frame = read_png(path)
        if frame.shape != ending.shape:
            raise ValueError(f"{path.name} must match the canonical painting canvas")
        frames.append(frame)
    return {"story": story, "ending": ending, "frames": frames, "path": project}
