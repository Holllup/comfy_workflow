"""Two-stage ComfyUI cat vlog: review ten persisted first frames, then render."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageOps

from . import core

RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
ASSET_ROOT = Path(__file__).resolve().parent / "assets"
REVIEW = "1_生成首帧并审查"
RENDER = "2_已审查_生成视频"
PHASES = (REVIEW, RENDER)
IMAGE_BACKEND = "joyai-image-edit-plus-bf16-40step-v4-role-references"
VIDEO_BACKEND = "h3-fl2va-fp8-20step-v4"


def _output_root():
    return Path(os.environ.get("CAT_VLOG_H3_OUTPUT_ROOT", "/root/autodl-tmp/cat_vlog_h3/output"))


def _run_path(run_id):
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("run_id must contain letters, digits, _ or - and be at most 64 characters")
    return _output_root() / run_id


def _array(image):
    return image.detach().cpu().numpy() if hasattr(image, "detach") else np.asarray(image)


def _image_tensor(array):
    data = np.asarray(array, dtype=np.float32)
    try:
        import torch
    except ModuleNotFoundError:
        return data
    return torch.from_numpy(data.copy())


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _digest(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _previews(paths, subfolder):
    """Use ComfyUI's native image-preview UI, with safe copies under its temp root."""
    try:
        import folder_paths
    except ModuleNotFoundError:
        return []
    target = Path(folder_paths.get_temp_directory()) / "cat_vlog_h3" / subfolder
    target.mkdir(parents=True, exist_ok=True)
    images = []
    for path in paths:
        path = Path(path)
        filename = f"{path.stem}_{_sha(path)[:12]}.png"
        shutil.copyfile(path, target / filename)
        images.append({"filename": filename, "subfolder": f"cat_vlog_h3/{subfolder}", "type": "temp"})
    return images


def _load_frame(path):
    with Image.open(path) as image:
        if image.size != (1344, 768):
            raise ValueError("Reviewed first frame must be 1344×768")
        return _image_tensor(np.asarray(image.convert("RGB"), dtype=np.float32)[None] / 255.0)


def _reference_bank():
    return core.load_reference_catalog(ASSET_ROOT)


def _image_context(story, seed_base, bank):
    frames = {}
    for index in range(1, 11):
        images = [{key: value for key, value in item.items() if key != 'path'} | {"sha256": _sha(item['path'])}
                  for item in core.resolve_reference_assets(story, index, bank)]
        frames[str(index)] = _digest({"image_backend": IMAGE_BACKEND, "image_spec": core.image_spec(story, index), "seed_base": seed_base, "assets": images})
    return json.dumps({"frames": frames}, sort_keys=True)


def _frame_context(context, index):
    try:
        return json.loads(context)["frames"][str(index)]
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError("旧版审查记录需要重新生成并审查 / review required") from error


def _frame_record(run_id, index, context, frame_key=None):
    folder = _run_path(run_id) / "frames"
    path = folder / f"shot_{index:02d}_start.png"
    stamp = path.with_suffix(".json")
    if not path.is_file() or not stamp.is_file():
        raise ValueError(f"镜头 {index} 未生成首帧，请先运行阶段1审查 / review")
    data = _read_json(stamp)
    if data.get("context") != _frame_context(context, index) or (frame_key is not None and data.get("frame_key") != frame_key):
        raise ValueError(f"镜头 {index} 的剧本、参考或种子已变化，请重新生成并审查 / review")
    if data.get("sha256") != _sha(path):
        raise ValueError(f"镜头 {index} 文件与审查记录不一致，请重新生成并审查 / review")
    return path, {"id": index, "sha256": data["sha256"], "frame_key": data["frame_key"]}


def _approved(ready):
    if not isinstance(ready, str) or not ready.startswith("approved:"):
        raise ValueError("请先在阶段1审查选中的首帧，再切换阶段2 / review required")
    try:
        data = json.loads(ready.removeprefix('approved:'))
        if not data['selected'] or not data['frames']:
            raise ValueError()
        return data
    except (ValueError, TypeError, KeyError) as error:
        raise ValueError("无效或旧版审查凭证 / review required") from error


def _clip_record(run_id, index, ready, video_key, frame_count):
    approved = _approved(ready)
    path = _run_path(run_id) / 'clips' / f'shot_{index:02d}.mp4'
    stamp = path.with_suffix('.json')
    if not path.is_file() or not stamp.is_file():
        raise ValueError(f'clip {index} not generated')
    record = _read_json(stamp)
    if record.get('video_key') != video_key or record.get('frame_count') != frame_count or record.get('frame_sha256') != approved['frames'][str(index)]['sha256']:
        raise ValueError(f'clip {index} conditions changed')
    if record.get('sha256') != _sha(path):
        raise ValueError(f'clip {index} file changed')
    return path


class CatH3References:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("CAT_REFERENCES",)
    RETURN_NAMES = ("references",)
    FUNCTION = "load"
    CATEGORY = "cat_vlog_h3"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls):
        bank = _reference_bank()
        return _digest({"catalog": bank, "content": {aid: _sha(item['path']) for aid, item in bank.items()}})

    def load(self):
        bank = _reference_bank()
        previews = []
        labels = []
        for aid, item in bank.items():
            previews.extend(_previews([item['path']], f"reference_{aid}"))
            labels.append(f"{aid}: {item['purpose']} / {item.get('owner') or 'scene'}")
        return {"ui": {"images": previews, "text": labels}, "result": (bank,)}


class CatH3Story:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "story_json": ("STRING", {"default": "", "multiline": True}),
            "run_id": ("STRING", {"default": "cat_vlog_01"}),
            "seed_base": ("INT", {"default": 482701, "min": 0, "max": 2147483000}),
            "phase": (list(PHASES), {"default": REVIEW}),
            "selected_shots": ("STRING", {"default": "all", "tooltip": "all，或1,5,7；同一图用于少量验收和十镜正式运行"}),
            "model_quality": (["pending", "accepted", "rejected"], {"default": "pending", "tooltip": "用户看片后选择；pending仅允许最多三镜视频验收"}),
            "references": ("CAT_REFERENCES",),
        }}

    RETURN_TYPES = ("STRING", "STRING", "INT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("story_json", "run_id", "seed_base", "phase", "context", "selected_shots")
    FUNCTION = "prepare"
    CATEGORY = "cat_vlog_h3"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return CatH3References.IS_CHANGED()

    def prepare(self, story_json, run_id, seed_base, phase=REVIEW, references=None, selected_shots="all", model_quality="pending"):
        if phase not in PHASES:
            raise ValueError("Unknown review phase")
        story = core.validate_story(story_json)
        selected = core.parse_shot_selection(selected_shots)
        selection = ','.join(map(str, selected))
        if model_quality not in ('pending', 'accepted', 'rejected'):
            raise ValueError('Invalid model_quality status')
        if phase == RENDER and (model_quality == 'rejected' or (model_quality != 'accepted' and len(selected) > 3)):
            raise ValueError('模型画质尚未验收 / model quality pending: first render at most three selected shots, review them, then select accepted')
        folder = _run_path(run_id)
        normalized = json.dumps(story, ensure_ascii=False, indent=2) + "\n"
        bank = references if references is not None else _reference_bank()
        character_sha = {aid: _sha(item['path']) for aid, item in bank.items()}
        context = _image_context(story, seed_base, bank)
        manifest_path = folder / "manifest.json"
        if phase == RENDER:
            review_path = folder / 'review.json'
            if not review_path.is_file() or _read_json(review_path).get('schema_version') != 4:
                raise ValueError("尚无当前首帧审查记录，请先运行阶段1 / review required")
            review = _read_json(review_path)
            for index in selected:
                if review.get('frames', {}).get(str(index), {}).get('context') != _frame_context(context, index):
                    raise ValueError(f'镜头{index}尚未生成或条件已变，请先运行阶段1 / review required')
            manifest = _read_json(manifest_path) if manifest_path.exists() else {}
            manifest.update({"story_sha256": _digest(story), "character_sha256": character_sha, "seed_base": seed_base})
            _write_json(manifest_path, manifest)
            (folder / "story.json").write_text(normalized, encoding="utf-8")
        else:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "frames").mkdir(exist_ok=True)
            (folder / "clips").mkdir(exist_ok=True)
            (folder / "story.json").write_text(normalized, encoding="utf-8")
            _write_json(manifest_path, {
                "run_id": run_id, "context": context, "story_sha256": _digest(story), "seed_base": seed_base,
                "character_sha256": character_sha, "status": "frames_pending",
                "render": {"width": 1344, "height": 768, "fps": 24, "steps": 20, "shots": 10},
            })
        manifest = _read_json(manifest_path)
        manifest.update({'schema_version': 4, 'selected_shots': list(selected), 'model_quality': model_quality,
                         'image_backend': IMAGE_BACKEND, 'video_backend': VIDEO_BACKEND, 'sample_quality': 'not_automatically_verified'})
        _write_json(manifest_path, manifest)
        timings, cumulative = [], 0
        for shot in story['shots']:
            timing = core.resolve_duration(shot['duration_seconds'])
            timings.append({'id': shot['id'], **timing, 'start_seconds': cumulative / 24, 'end_seconds': (cumulative + timing['frames']) / 24})
            cumulative += timing['frames']
        _write_json(folder / 'timing_report.json', {'shots': timings, 'total_frames': cumulative, 'total_seconds': cumulative / 24})
        reference_manifest = {}
        for index in range(1, 11):
            for item in core.resolve_reference_assets(story, index, bank):
                aid = item['asset_id']
                target = folder / 'references' / (aid + Path(item['path']).suffix)
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(item['path'], target)
                reference_manifest[aid] = {key: value for key, value in item.items() if key != 'path'} | {'sha256': _sha(target), 'run_file': str(target)}
        _write_json(folder / 'references.json', reference_manifest)
        prompt_folder = folder / "prompts"
        prompt_folder.mkdir(parents=True, exist_ok=True)
        for index in range(1, 11):
            (prompt_folder / f"shot_{index:02d}_image.txt").write_text(core.compose_start_prompt(story, index), encoding="utf-8")
            (prompt_folder / f"shot_{index:02d}_image_negative.txt").write_text(core.compose_start_negative_prompt(story, index), encoding="utf-8")
            (prompt_folder / f"shot_{index:02d}_video.txt").write_text(core.compose_video_prompt(story, index), encoding="utf-8")
        (folder / 'story_review.md').write_text(core.story_review_markdown(story), encoding='utf-8')
        return normalized, run_id, seed_base, phase, context, selection

class CatH3SelectReferences:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"story_json": ("STRING", {"forceInput": True}),
                             "index": ("INT", {"default": 1, "min": 1, "max": 10}),
                             "references": ("CAT_REFERENCES",)}}

    RETURN_TYPES = ("CAT_SHOT_REFERENCES",)
    RETURN_NAMES = ("selected_photos",)
    FUNCTION = "select"
    CATEGORY = "cat_vlog_h3"

    def select(self, story_json, index, references):
        story = core.validate_story(story_json)
        packed = []
        for item in core.resolve_reference_assets(story, index, references):
            with Image.open(item['path']) as image:
                packed.append({**item, "image": _image_tensor(np.asarray(image.convert('RGB'), dtype=np.float32)[None] / 255)})
        return (packed,)


def _text_token_budget(clip, prompt):
    if len(prompt) > core.MAX_PROMPT_CHARS:
        raise ValueError("Prompt exceeds character budget; text was not truncated")
    tokenized = clip.tokenize(prompt)
    counts = [sum(len(block) for block in blocks) for blocks in tokenized.values() if isinstance(blocks, (list, tuple))]
    if not counts:
        raise RuntimeError("Cannot inspect text tokenizer output; update the adapter before generation")
    count = max(counts)
    if count > 4096:
        raise ValueError(f"Prompt has {count} text tokens, over the project's 4096-token budget; not truncated")
    return {"text_tokens": count, "project_text_budget": 4096, "composer_truncated": False}


class CatH3JoyEncode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"clip": ("CLIP",), "vae": ("VAE",), "prompt": ("STRING", {"forceInput": True}),
                             "references": ("CAT_SHOT_REFERENCES",)}}

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"
    CATEGORY = "cat_vlog_h3"

    def encode(self, clip, vae, prompt, references):
        if not 1 <= len(references) <= 6 or any(item.get('image') is None for item in references):
            raise ValueError("JoyAI requires one to six actual photos, without placeholders")
        _text_token_budget(clip, prompt)
        try:
            from comfy_extras.nodes_joyimage import _encode
        except ImportError as error:
            raise RuntimeError("Current ComfyUI lacks the supported native JoyAI encoding path; run preflight first") from error
        return (_encode(clip, prompt, vae, [item['image'] for item in references]),)


class CatH3ShotFields:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "story_json": ("STRING", {"forceInput": True}), "seed_base": ("INT", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 10}),
            "variation": ("INT", {"default": 0, "min": 0, "max": 100000}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "STRING", "STRING", "INT", "STRING")
    RETURN_NAMES = ("start_prompt", "video_prompt", "start_seed", "video_seed", "frame_key", "negative_prompt", "frame_count", "video_key")
    FUNCTION = "split"
    CATEGORY = "cat_vlog_h3"

    def split(self, story_json, seed_base, index, variation=0):
        story = core.validate_story(story_json)
        start = core.compose_start_prompt(story, index)
        start_seed = seed_base + index * 1000 + 1 + variation * 100000
        video_seed = seed_base + index * 1000 + 3
        negative = core.compose_start_negative_prompt(story, index)
        video = core.compose_video_prompt(story, index)
        length = core.resolve_duration(story['shots'][index - 1]['duration_seconds'])['frames']
        key = _digest({'prompt': video, 'seed': video_seed, 'frames': length, 'backend': VIDEO_BACKEND})
        return start, video, start_seed, video_seed, _digest({"prompt": start, "negative": negative, "seed": start_seed}), negative, length, key


class CatH3SaveFrame:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "run_id": ("STRING", {"forceInput": True}), "phase": ("STRING", {"forceInput": True}),
            "context": ("STRING", {"forceInput": True}), "frame_key": ("STRING", {"forceInput": True}),
            "selected_shots": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 10}),
            "image": ("IMAGE", {"lazy": True}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "path")
    FUNCTION = "save"
    CATEGORY = "cat_vlog_h3"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Re-check disk on every queue; upstream JoyAI computations remain cacheable.
        # Linked input values may not be available during ComfyUI's change scan.
        return float("nan")

    def check_lazy_status(self, phase, image=None, run_id=None, context=None, index=None, frame_key=None, selected_shots='all', **kwargs):
        if index is not None and index not in core.parse_shot_selection(selected_shots):
            return []
        if phase != REVIEW or image is not None:
            return []
        if run_id is not None and context is not None and index is not None and frame_key is not None:
            try:
                _frame_record(run_id, index, context, frame_key)
                return []
            except (ValueError, OSError):
                pass
        return ["image"]

    def save(self, run_id, phase, context, index, frame_key, image=None, selected_shots='all'):
        if index not in core.parse_shot_selection(selected_shots):
            return {'ui': {'text': [f'镜头 {index:02d} 未选中']}, 'result': (_image_tensor(np.zeros((1, 1, 1, 3))), '')}
        path = _run_path(run_id) / "frames" / f"shot_{index:02d}_start.png"
        if phase == REVIEW and image is not None:
            data = _array(image)
            if data.shape != (1, 768, 1344, 3):
                raise ValueError("Cat H3 first frames must be 1344×768 RGB images")
            path.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(np.rint(np.clip(data[0], 0, 1) * 255).astype(np.uint8)).save(path)
            _write_json(path.with_suffix(".json"), {"context": _frame_context(context, index), "frame_key": frame_key, "sha256": _sha(path)})
        elif phase in PHASES:
            _frame_record(run_id, index, context, frame_key)
        else:
            raise ValueError("Unknown review phase")
        return {"ui": {"images": _previews([path], run_id)}, "result": (_load_frame(path), str(path))}


class CatH3Stage:
    @classmethod
    def INPUT_TYPES(cls):
        required = {"run_id": ("STRING", {"forceInput": True}), "phase": ("STRING", {"forceInput": True}),
                    "context": ("STRING", {"forceInput": True}), "selected_shots": ("STRING", {"forceInput": True})}
        required.update({f"frame_{i:02d}": ("STRING", {"forceInput": True}) for i in range(1, 11)})
        return {"required": required}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("ready",)
    FUNCTION = "run"
    CATEGORY = "cat_vlog_h3"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def run(self, run_id, phase, context, selected_shots='all', **frames):
        folder = _run_path(run_id)
        selected = core.parse_shot_selection(selected_shots)
        paths, records = [], {}
        for index in selected:
            path, record = _frame_record(run_id, index, context)
            if frames.get(f"frame_{index:02d}") != str(path):
                raise ValueError("All selected first frames must enter the review node")
            paths.append(path)
            records[str(index)] = {**record, 'context': _frame_context(context, index)}
        review_path = folder / "review.json"
        review = _read_json(review_path) if review_path.is_file() else {'schema_version': 4, 'frames': {}, 'human_approved': {}}
        if review.get('schema_version') != 4:
            review = {'schema_version': 4, 'frames': {}, 'human_approved': {}}
        if phase == REVIEW:
            review['frames'].update(records)
            for index in selected:
                review['human_approved'].pop(str(index), None)
            _write_json(review_path, review)
            # A numbered overview helps map thumbnails to storyboard shot numbers.
            sheet = Image.new("RGB", (1344, 800), (25, 25, 25))
            draw = ImageDraw.Draw(sheet)
            for position, (index, path) in enumerate(zip(selected, paths)):
                with Image.open(path) as image:
                    thumb = ImageOps.contain(image.convert("RGB"), (260, 350))
                x, y = (position % 5) * 268, (position // 5) * 400
                sheet.paste(thumb, (x, y + 30))
                draw.text((x + 8, y + 8), f"SHOT {index:02d}", fill="white")
            sheet.save(folder / "first_frames_review.png")
            token, status = f"review_pending:{run_id}", "awaiting_review"
            message = f"所选首帧 {selected_shots} 已生成；审查下方大图。通过后保持镜号选择，切阶段2再点Run。初次模型验收先选最多三镜，看片通过后选择 model_quality=accepted。"
        elif phase == RENDER:
            if any(review['frames'].get(index) != record for index, record in records.items()):
                raise ValueError("首帧已变化，请回到阶段1重新审查 / review required")
            review['human_approved'].update(records)
            _write_json(review_path, review)
            token, status = 'approved:' + json.dumps({'run_id': run_id, 'selected': list(selected), 'frames': records}, sort_keys=True), 'rendering'
            message = "正在使用已审查并保存的十张首帧；不会重新运行 JoyAI。"
        else:
            raise ValueError("Unknown review phase")
        manifest_path = folder / "manifest.json"
        manifest = _read_json(manifest_path) if manifest_path.exists() else {}
        manifest.update({"status": status, "review_digest": _digest(review)})
        _write_json(manifest_path, manifest)
        try:
            import comfy.model_management as management
        except ModuleNotFoundError:
            pass
        else:
            management.unload_all_models()
            management.soft_empty_cache()
        preview_paths = [folder / "first_frames_review.png", *paths]
        return {"ui": {"images": _previews(preview_paths, run_id), "text": [message]}, "result": (token,)}


class CatH3VideoGate:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "start": ("IMAGE",), "ready": ("STRING", {"forceInput": True}),
            "prior_done": ("STRING", {"forceInput": True}), "index": ("INT", {"default": 1, "min": 1, "max": 10}),
            "clip": ("CLIP",), "prompt": ("STRING", {"forceInput": True}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("start", "checked_prompt")
    FUNCTION = "allow"
    CATEGORY = "cat_vlog_h3"

    def allow(self, start, ready, prior_done, index, clip, prompt):
        if index not in _approved(ready)['selected']:
            raise ValueError('This video shot is not selected')
        if not prior_done:
            raise ValueError(f"Shot {index} cannot start before prior completion")
        _text_token_budget(clip, prompt)
        return (start, prompt)


class CatH3SaveAV:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "phase": ("STRING", {"forceInput": True}), "run_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 10}),
            "ready": ("STRING", {"forceInput": True, "lazy": True}),
            "selected_shots": ("STRING", {"forceInput": True}), "video_key": ("STRING", {"forceInput": True}),
            "frame_count": ("INT", {"forceInput": True}),
            "images": ("IMAGE", {"lazy": True}), "audio": ("AUDIO", {"lazy": True}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("done",)
    FUNCTION = "save"
    CATEGORY = "cat_vlog_h3"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float('nan')

    def check_lazy_status(self, phase, ready=None, images=None, audio=None, selected_shots='all', index=None,
                          run_id=None, video_key=None, frame_count=None, **kwargs):
        if phase == REVIEW or (index is not None and index not in core.parse_shot_selection(selected_shots)):
            return []
        if ready is None:
            return ["ready"]
        _approved(ready)
        if run_id is not None and index is not None and video_key is not None and frame_count is not None:
            try:
                _clip_record(run_id, index, ready, video_key, frame_count)
                return []
            except (ValueError, OSError, KeyError):
                pass
        return [name for name, value in (("images", images), ("audio", audio)) if value is None]

    def save(self, phase, run_id, index, ready=None, images=None, audio=None, selected_shots='all', video_key='', frame_count=175):
        if phase == REVIEW or index not in core.parse_shot_selection(selected_shots):
            return (f"skipped:{run_id}:{index}",)
        _approved(ready)
        if images is None:
            return (str(_clip_record(run_id, index, ready, video_key, frame_count)),)
        if tuple(images.shape) != (frame_count, 768, 1344, 3):
            raise ValueError(f"Each cat H3 video must contain {frame_count} frames of 1344×768 RGB")
        path = _run_path(run_id) / "clips" / f"shot_{index:02d}.mp4"
        core.encode_av_clip(images, audio, path, fps=24)
        _write_json(path.with_suffix('.json'), {'video_key': video_key, 'frame_count': frame_count,
                    'frame_sha256': _approved(ready)['frames'][str(index)]['sha256'], 'sha256': _sha(path)})
        return (str(path),)


class CatH3Finish:
    @classmethod
    def INPUT_TYPES(cls):
        required = {"phase": ("STRING", {"forceInput": True}), "run_id": ("STRING", {"forceInput": True}),
                    "story_json": ("STRING", {"forceInput": True}), "context": ("STRING", {"forceInput": True}),
                    "selected_shots": ("STRING", {"forceInput": True}), "ready": ("STRING", {"forceInput": True, "lazy": True})}
        required.update({f"clip_{i:02d}": ("STRING", {"forceInput": True, "lazy": True}) for i in range(1, 11)})
        required.update({f"{kind}_{i:02d}": ("STRING", {"forceInput": True}) for i in range(1, 11) for kind in ('frame_key', 'video_key')})
        return {"required": required}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("final_path",)
    FUNCTION = "finish"
    CATEGORY = "cat_vlog_h3"
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float('nan')

    def check_lazy_status(self, phase, ready=None, selected_shots='all', **kwargs):
        if phase == REVIEW:
            return []
        if ready is None:
            return ["ready"]
        _approved(ready)
        return [f"clip_{i:02d}" for i in core.parse_shot_selection(selected_shots) if kwargs.get(f"clip_{i:02d}") is None]

    def finish(self, phase, run_id, story_json, ready=None, context=None, selected_shots='all', **kwargs):
        if phase == REVIEW:
            return {"ui": {"text": ["阶段1只生成所选首帧。看图通过后切阶段2；初次模型质量验收先选最多三镜视频。"]}, "result": ("",)}
        _approved(ready)
        story = core.validate_story(story_json)
        folder = _run_path(run_id)
        manifest = _read_json(folder / 'manifest.json')
        if manifest.get('model_quality') != 'accepted':
            return {'ui': {'text': ['所选验收片段已完成；模型画质尚未人工验收，不合成十镜正式成片。看片通过后在01节点选择 model_quality=accepted。']}, 'result': ('',)}
        clips, counts, missing = [], [], []
        for index in range(1, 11):
            count = core.resolve_duration(story['shots'][index - 1]['duration_seconds'])['frames']
            counts.append(count)
            try:
                _, frame = _frame_record(run_id, index, context, kwargs[f'frame_key_{index:02d}'])
                full_ready = 'approved:' + json.dumps({'selected': [index], 'frames': {str(index): frame}})
                clips.append(_clip_record(run_id, index, full_ready, kwargs[f'video_key_{index:02d}'], count))
            except (ValueError, OSError, KeyError):
                missing.append(index)
        if missing:
            manifest = _read_json(folder / 'manifest.json')
            manifest.update({'status': 'clips_pending', 'missing_or_stale_shots': missing})
            _write_json(folder / 'manifest.json', manifest)
            return {'ui': {'text': [f'本次所选片段已完成；尚缺或已过期的镜头：{missing}。未合成十镜成片。']}, 'result': ('',)}
        final = folder / "cat_vlog_h3.mp4"
        core.join_av_clips(clips, final, fps=24, frame_counts=counts, output_size=(1280, 720))
        manifest = _read_json(folder / "manifest.json")
        manifest.update({"run_id": run_id, "status": "complete", "clips": [str(p.resolve()) for p in clips],
                         "final": str(final.resolve()), "video": {"width": 1280, "height": 720, "native_width": 1344,
                         "native_height": 768, "fps": 24, "frames_per_shot": counts, "shots": 10, "total_frames": sum(counts), 'total_seconds': sum(counts) / 24},
                         "audio": {"enabled": True, "codec": "AAC", "sample_rate": 48000},
                         "models": {"image": "JoyAI-Image-Edit-Plus BF16 40 steps", "video": "MiniMax H3 FL2VA pruned FP8", "video_steps": 20}})
        _write_json(folder / "manifest.json", manifest)
        return {"ui": {"text": [str(final)]}, "result": (str(final),)}
