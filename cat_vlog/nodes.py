"""ComfyUI nodes for the six-shot cat vlog workflow."""

import os
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from .core import concat_clips, encode_clip, freeze_reference, generate_story, parse_story


def _output_root() -> Path:
    return Path(os.environ.get("CAT_VLOG_ROOT", Path(__file__).resolve().parents[2] / "output" / "cat_vlog"))


def _numpy_image(value):
    if hasattr(value, "detach"):
        value = value.detach().cpu().numpy()
    return np.asarray(value)


_STORY_MODEL = None


def _load_story_model():
    global _STORY_MODEL
    if _STORY_MODEL is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_path = Path(os.environ.get(
            "CAT_VLOG_STORY_MODEL",
            "/root/autodl-tmp/cat_vlog/models/Qwen3-4B-Instruct-2507",
        ))
        if not model_path.is_dir():
            raise FileNotFoundError(f"Local story model is missing: {model_path}")
        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        model = AutoModelForCausalLM.from_pretrained(
            model_path, dtype=torch.float32, local_files_only=True,
        )
        model.eval()
        _STORY_MODEL = (tokenizer, model)
    return _STORY_MODEL


def _complete_story(prompt, seed):
    import torch

    tokenizer, model = _load_story_model()
    messages = [
        {"role": "system", "content": "You write coherent short video storyboards. Output strict JSON only."},
        {"role": "user", "content": prompt},
    ]
    input_ids = tokenizer.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True, return_tensors="pt",
    )
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        with torch.inference_mode():
            output = model.generate(
                input_ids, max_new_tokens=1600, do_sample=True, temperature=0.8, top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
            )
    return tokenizer.decode(output[0][input_ids.shape[-1]:], skip_special_tokens=True)


class CatStoryPlanner:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "theme": ("STRING", {"default": "小猫的一天", "multiline": True}),
            "auto_random": ("BOOLEAN", {"default": True}),
            "seed": ("INT", {"default": 0, "min": 0, "max": 2**53 - 1}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("story_json", "run_id", "run_seed")
    FUNCTION = "plan"
    CATEGORY = "Cat Vlog"

    @classmethod
    def IS_CHANGED(cls, theme, auto_random, seed):
        return float("nan") if auto_random else (theme, seed)

    def plan(self, theme, auto_random, seed):
        run_seed = secrets.randbits(48) if auto_random else seed
        attempt = 0

        def complete(prompt):
            nonlocal attempt
            attempt += 1
            return _complete_story(prompt, run_seed + attempt - 1)

        story = generate_story(theme, run_seed, complete)
        story["run_seed"] = run_seed
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + f"_{run_seed:012x}"
        folder = _output_root() / run_id
        folder.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(story, ensure_ascii=False, indent=2)
        (folder / "story.json").write_text(raw, encoding="utf-8")
        return raw, run_id, run_seed


class CatShotFields:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "story_json": ("STRING", {"forceInput": True}),
            "run_seed": ("INT", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 6}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("image_prompt", "motion_prompt", "image_seed", "video_seed")
    FUNCTION = "split"
    CATEGORY = "Cat Vlog"

    def split(self, story_json, run_seed, index):
        shot = parse_story(story_json)["shots"][index - 1]
        return (
            shot["image_prompt"], shot["motion_prompt"],
            (run_seed + index * 997) % (2**53),
            (run_seed + index * 1999) % (2**53),
        )


class CatReference:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"generated": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "lock"
    CATEGORY = "Cat Vlog"

    def lock(self, generated):
        frozen = freeze_reference(_numpy_image(generated)[0], _output_root() / "reference.png")
        if hasattr(generated, "detach"):
            import torch
            return (torch.from_numpy(frozen.copy()).unsqueeze(0),)
        return (frozen[np.newaxis],)


class _CatGate:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "prompt": ("STRING", {"forceInput": True}),
            "seed": ("INT", {"forceInput": True}),
            "prior": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 6}),
        }}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("prompt", "seed")
    FUNCTION = "allow"
    CATEGORY = "Cat Vlog"

    def allow(self, prompt, seed, prior, index):
        if not prior:
            raise ValueError(f"Shot {index} cannot start before the previous step completed")
        return prompt, seed


class CatImageGate(_CatGate):
    pass


class CatVideoGate(_CatGate):
    pass


class CatSaveFrame:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "image": ("IMAGE",),
            "run_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 6}),
        }}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "done")
    FUNCTION = "save"
    CATEGORY = "Cat Vlog"

    def save(self, image, run_id, index):
        path = _output_root() / run_id / f"shot_{index:02}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        pixels = _numpy_image(image)[0]
        Image.fromarray((np.clip(pixels, 0, 1) * 255).round().astype(np.uint8)).save(path)
        return image, str(path)


class CatSaveClip:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "images": ("IMAGE",),
            "run_id": ("STRING", {"forceInput": True}),
            "index": ("INT", {"default": 1, "min": 1, "max": 6}),
        }}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("done",)
    FUNCTION = "save"
    CATEGORY = "Cat Vlog"

    def save(self, images, run_id, index):
        path = _output_root() / run_id / f"shot_{index:02}.mp4"
        encode_clip(_numpy_image(images), path)
        return (str(path),)


class CatFinish:
    @classmethod
    def INPUT_TYPES(cls):
        required = {f"clip_{index}": ("STRING", {"forceInput": True}) for index in range(1, 7)}
        required["story_json"] = ("STRING", {"forceInput": True})
        required["run_id"] = ("STRING", {"forceInput": True})
        return {"required": required}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("final_path",)
    FUNCTION = "finish"
    CATEGORY = "Cat Vlog"
    OUTPUT_NODE = True

    def finish(self, clip_1, clip_2, clip_3, clip_4, clip_5, clip_6, story_json, run_id):
        folder = _output_root() / run_id
        folder.mkdir(parents=True, exist_ok=True)
        clips = [Path(path) for path in (clip_1, clip_2, clip_3, clip_4, clip_5, clip_6)]
        final = folder / "cat_vlog_30s.mp4"
        concat_clips(clips, final)
        story = parse_story(story_json)
        (folder / "story.json").write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        manifest = {
            "run_id": run_id,
            "reference": str(_output_root() / "reference.png"),
            "clips": [str(path) for path in clips],
            "final": str(final),
            "video": {"width": 704, "height": 1280, "fps": 24, "frames_per_shot": 120, "shots": 6},
            "models": {"image": "nunchaku-qwen-image-edit-2509-lightning", "video": "wan2.2-ti2v-5B"},
        }
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ui": {"text": [str(final)]}, "result": (str(final),)}
