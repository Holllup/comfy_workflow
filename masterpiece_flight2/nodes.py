"""Small ComfyUI nodes for reviewed painting-flight projects."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np

from . import core


def _root() -> Path:
    override = os.environ.get("ART_PROJECT_ROOT")
    if override:
        return Path(override)
    import folder_paths
    return Path(folder_paths.get_output_directory()) / "masterpiece_flight2"


def _numpy_image(image) -> np.ndarray:
    if hasattr(image, "detach"):
        array = image.detach().cpu().numpy()
    else:
        array = np.asarray(image)
    if array.ndim == 4:
        if array.shape[0] != 1:
            raise ValueError("Expected exactly one image")
        array = array[0]
    return core._rgb_uint8(array)


def _tensor_image(image: np.ndarray):
    batch = np.asarray(image, dtype=np.float32)[None] / 255.0
    try:
        import torch
    except ModuleNotFoundError:
        return batch
    return torch.from_numpy(batch.copy())


class ArtPrepare:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "painting": ("IMAGE",),
            "project_id": ("STRING", {"default": "starry_night"}),
            "story_json": ("STRING", {"default": "", "multiline": True}),
            "canvas_mode": (["legacy_1280x720", "h3_1344x768"], {"default": "legacy_1280x720"}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("canvas", "story_json", "project_id")
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, painting, project_id, story_json, canvas_mode="legacy_1280x720"):
        if core.validate_story(story_json).get("schema_version") == 3:
            raise ValueError("Use ArtV3Prepare and the FLUX/H3 v3 workflows for schema_version 3")
        dimensions = (1344, 768) if canvas_mode == "h3_1344x768" else (1280, 720)
        project = core.init_project(_root(), project_id, story_json, _numpy_image(painting), canvas_size=dimensions)
        normalized = json.dumps(project["story"], ensure_ascii=False)
        return (_tensor_image(project["ending"]), normalized, project_id)


class ArtSpatialStyleSeed:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"painting": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("style_seed",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, painting):
        seed = core.spatial_style_seed(_numpy_image(painting))
        return (_tensor_image(seed),)


class ArtFrameText:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "story_json": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 4, "min": 1, "max": 4}),
            "seed_base": ("INT", {"default": 487201, "min": 0, "max": 2147483000}),
            "spatial_mode": ("BOOLEAN", {"default": False}),
        }}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("image_prompt", "seed")
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, story_json, index, seed_base, spatial_mode=False):
        plan = core.validate_story(story_json)
        if index not in (1, 2, 3, 4):
            raise ValueError("Frame index must be 1–4")
        if spatial_mode and plan.get("conditioning_mode") != "spatial_style_seed":
            raise ValueError("Spatial workflow requires conditioning_mode='spatial_style_seed' in story_json")
        return (core.compose_image_prompt(plan["keyframes"][index - 1], index, spatial_mode), seed_base + index)


class ArtSaveKeyframe:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "project_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 4, "min": 1, "max": 4}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "draft_path")
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"
    OUTPUT_NODE = True

    def run(self, image, project_id, index):
        path = core.save_keyframe(_root(), project_id, index, _numpy_image(image))
        return (image, str(path))


class ArtLoadApproved:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"project_id": ("STRING", {"default": "starry_night"})},
            "optional": {"render_model": ("STRING", {"default": "LTX-2.5 distilled Comfy int8"})},
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("frame_01", "frame_02", "frame_03", "frame_04", "ending", "story_json", "project_id")
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    @classmethod
    def IS_CHANGED(cls, project_id, render_model="LTX-2.5 distilled Comfy int8"):
        project = core._project_path(_root(), project_id)
        paths = [project / "story.json", project / "ending.png"] + [
            project / "approved" / f"frame_{i:02d}.png" for i in range(1, 5)
        ]
        digest = hashlib.sha256()
        digest.update(render_model.encode())
        for path in paths:
            digest.update(path.name.encode())
            digest.update(path.read_bytes() if path.exists() else b"missing")
        return digest.hexdigest()

    def run(self, project_id, render_model="LTX-2.5 distilled Comfy int8"):
        project = core.load_project(_root(), project_id)
        story_json = json.dumps(project["story"], ensure_ascii=False)
        settings = {
            "project_id": project_id,
            "frame_sha256": {
                f"frame_{i:02d}": hashlib.sha256((project["path"] / "approved" / f"frame_{i:02d}.png").read_bytes()).hexdigest()
                for i in range(1, 5)
            },
            "video_model": render_model,
            "duration_seconds_per_shot": 5,
            "width": 1280,
            "height": 720,
            "fps": 24,
            "video_seeds": [932100 + i * 101 for i in range(1, 5)],
            "audio": False,
        }
        if render_model == "Wan2.2 5B TI2V":
            settings["latent_height"] = 704
            settings["bridge_frames"] = 8
        (project["path"] / "render_settings.json").write_text(
            json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        manifest_path = project["path"] / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["status"] = "approved_loaded"
        manifest["approved_frame_sha256"] = settings["frame_sha256"]
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return tuple(_tensor_image(frame) for frame in project["frames"]) + (
            _tensor_image(project["ending"]), story_json, project_id
        )


class ArtMotionText:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "story_json": ("STRING", {"forceInput": True}),
                "index": ("INT", {"default": 1, "min": 1, "max": 4}),
            },
            "optional": {"prior_video": ("VIDEO",), "prior_images": ("IMAGE",)},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("motion_prompt",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, story_json, index, prior_video=None, prior_images=None):
        plan = core.validate_story(story_json)
        if index not in (1, 2, 3, 4):
            raise ValueError("Shot index must be 1–4")
        return (core.compose_motion_prompt(plan["shots"][index - 1]),)


class ArtH3Stage:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {**{f"frame_{index:02d}": ("IMAGE",) for index in range(1, 5)}, "ending": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",) * 5
    RETURN_NAMES = ("frame_01", "frame_02", "frame_03", "frame_04", "ending")
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, frame_01, frame_02, frame_03, frame_04, ending):
        try:
            import comfy.model_management as management
        except ModuleNotFoundError:
            pass
        else:
            management.unload_all_models()
            management.soft_empty_cache()
        return (frame_01, frame_02, frame_03, frame_04, ending)


class ArtH3Audit:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "raw_last": ("IMAGE",), "target": ("IMAGE",),
            "project_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 4}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("raw_last",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, raw_last, target, project_id, index):
        raw = _numpy_image(raw_last)
        goal = _numpy_image(target)
        if raw.shape != goal.shape:
            raise ValueError("H3 raw tail and target must have the same canvas")
        directory = core._project_path(_root(), project_id) / "diagnostics"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"shot_{index:02d}_raw_last.png").write_bytes(core._png_bytes(raw))
        (directory / f"shot_{index:02d}_target.png").write_bytes(core._png_bytes(goal))
        gap = float(np.mean(np.abs(raw.astype(np.float32) - goal.astype(np.float32))) / 255.0)
        (directory / f"shot_{index:02d}_gap.json").write_text(
            json.dumps({"shot": index, "mean_absolute_difference": round(gap, 6), "interpretation": "lower is closer; visual inspection is still required"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return (raw_last,)


class ArtH3Bridge:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "images": ("IMAGE",), "start": ("IMAGE",), "target": ("IMAGE",), "audit": ("IMAGE",),
            "story_json": ("STRING", {"forceInput": True}), "project_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 4}),
            "blend_frames": ("INT", {"default": 4, "min": 1, "max": 12}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, images, start, target, audit, story_json, project_id, index, blend_frames):
        plan = core.validate_story(story_json)
        transition = plan["shots"][index - 1].get("transition_type", "endpoint_correction")
        data = images.detach().cpu().numpy() if hasattr(images, "detach") else np.asarray(images)
        result = core.bridge_h3_frames(data, _numpy_image(start), _numpy_image(target), blend_frames)
        directory = core._project_path(_root(), project_id) / "diagnostics"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"shot_{index:02d}_bridged_last.png").write_bytes(core._png_bytes(result[-1]))
        (directory / f"shot_{index:02d}_transition.json").write_text(
            json.dumps({"shot": index, "transition_type": transition, "maximum_blend_frames": blend_frames}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        batch = result.astype(np.float32) / 255.0
        try:
            import torch
        except ModuleNotFoundError:
            return (batch,)
        return (torch.from_numpy(batch),)


class ArtDeliveryCanvas:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"images": ("IMAGE",), "original": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, images, original):
        data = images.detach().cpu().numpy() if hasattr(images, "detach") else np.asarray(images)
        output = core.delivery_canvas(data, _numpy_image(original)).astype(np.float32) / 255.0
        try:
            import torch
        except ModuleNotFoundError:
            return (output,)
        return (torch.from_numpy(output),)


class ArtHoldFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "count": ("INT", {"default": 24, "min": 1, "max": 240}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, image, count):
        if image.shape[0] != 1:
            raise ValueError("Hold expects one original image")
        if hasattr(image, "detach"):
            return (image.repeat((count, 1, 1, 1)),)
        return (np.repeat(np.asarray(image), count, axis=0),)


class ArtBridgeFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "images": ("IMAGE",),
            "start": ("IMAGE",),
            "target": ("IMAGE",),
            "blend_frames": ("INT", {"default": 8, "min": 1, "max": 24}),
        }}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, images, start, target, blend_frames):
        data = images.detach().cpu().numpy() if hasattr(images, "detach") else np.asarray(images)
        result = core.bridge_video_frames(data, _numpy_image(start), _numpy_image(target), blend_frames)
        batch = result.astype(np.float32) / 255.0
        try:
            import torch
        except ModuleNotFoundError:
            return (batch,)
        return (torch.from_numpy(batch),)


class ArtJoinFrames:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"clip1": ("IMAGE",), "still": ("IMAGE",)},
            "optional": {"clip2": ("IMAGE",), "clip3": ("IMAGE",), "clip4": ("IMAGE",)},
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, clip1, still, clip2=None, clip3=None, clip4=None):
        segments = [clip for clip in (clip1, clip2, clip3, clip4) if clip is not None] + [still]
        shape = tuple(clip1.shape[1:])
        if any(tuple(segment.shape[1:]) != shape for segment in segments):
            raise ValueError("All video segments must share one resolution")
        if hasattr(clip1, "detach"):
            import torch
            return (torch.cat(segments, dim=0),)
        return (np.concatenate(segments, axis=0),)


class ArtLastFrame:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"images": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, images):
        if images.shape[0] < 1:
            raise ValueError("Cannot take the last frame from an empty video")
        return (images[-1:],)


class ArtOutputPrefix:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "project_id": ("STRING", {"forceInput": True}),
            "label": ("STRING", {"default": "final"}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prefix",)
    FUNCTION = "run"
    CATEGORY = "masterpiece_flight2"

    def run(self, project_id, label):
        core._project_path(_root(), project_id)
        if label not in {
            "pilot", "final", "shot_01", "shot_02", "shot_03", "shot_04",
            "wan_pilot", "wan_final", "wan_shot_01", "wan_shot_02", "wan_shot_03", "wan_shot_04",
            "onepass_final", "onepass_shot_01", "onepass_shot_02", "onepass_shot_03", "onepass_shot_04",
            "h3_final", "h3_shot_01", "h3_shot_02", "h3_shot_03", "h3_shot_04",
        }:
            raise ValueError("Unknown output label")
        return (f"masterpiece_flight2/{project_id}/{label}",)


NODE_CLASS_MAPPINGS = {
    "ArtPrepare": ArtPrepare,
    "ArtSpatialStyleSeed": ArtSpatialStyleSeed,
    "ArtFrameText": ArtFrameText,
    "ArtSaveKeyframe": ArtSaveKeyframe,
    "ArtLoadApproved": ArtLoadApproved,
    "ArtMotionText": ArtMotionText,
    "ArtH3Stage": ArtH3Stage,
    "ArtH3Audit": ArtH3Audit,
    "ArtH3Bridge": ArtH3Bridge,
    "ArtDeliveryCanvas": ArtDeliveryCanvas,
    "ArtHoldFrames": ArtHoldFrames,
    "ArtBridgeFrames": ArtBridgeFrames,
    "ArtJoinFrames": ArtJoinFrames,
    "ArtLastFrame": ArtLastFrame,
    "ArtOutputPrefix": ArtOutputPrefix,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ArtPrepare": "名画飞行 · 创建项目",
    "ArtSpatialStyleSeed": "名画飞行 · 抽象画风种子（无原画构图）",
    "ArtFrameText": "名画飞行 · 关键帧提示词",
    "ArtSaveKeyframe": "名画飞行 · 保存关键帧",
    "ArtLoadApproved": "名画飞行 · 读取选定关键帧",
    "ArtMotionText": "名画飞行 · 飞行提示词",
    "ArtH3Stage": "名画飞行 · 图像完成后释放显存",
    "ArtH3Audit": "名画飞行 · 保存 H3 原始尾帧与偏差",
    "ArtH3Bridge": "名画飞行 · H3 接点安全校正",
    "ArtDeliveryCanvas": "名画飞行 · 成片留边转 16:9",
    "ArtHoldFrames": "名画飞行 · 原画定格",
    "ArtBridgeFrames": "名画飞行 · Wan 关键帧衔接",
    "ArtJoinFrames": "名画飞行 · 拼接帧序列",
    "ArtLastFrame": "名画飞行 · 提取实际尾帧",
    "ArtOutputPrefix": "名画飞行 · 输出路径",
}
