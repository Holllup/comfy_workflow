"""Pure helpers shared by the ComfyUI nodes and local checks."""

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

TIMES = ("早晨", "上午", "中午", "下午", "傍晚", "夜晚")


def parse_story(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            raw = "\n".join(lines[1:-1])
    story = json.loads(raw)
    if not isinstance(story, dict) or not isinstance(story.get("shots"), list) or len(story["shots"]) != 6:
        raise ValueError("Story must contain exactly six shots")
    if tuple(shot.get("time") for shot in story["shots"]) != TIMES:
        raise ValueError("Shots must follow the chronological day")
    for shot in story["shots"]:
        for field in ("beat_zh", "image_prompt", "motion_prompt"):
            if not isinstance(shot.get(field), str) or not shot[field].strip():
                raise ValueError(f"Each shot needs a nonempty {field}")
    return story


def generate_story(theme: str, seed: int, complete) -> dict:
    prompt = (
        "Write a six-shot, chronological, silent vertical vlog about the same "
        "photorealistic orange-and-white kitten with green eyes and a small blue collar. "
        "The kitten acts as a selfie vlogger, looks into the lens, and may interact "
        "with simple props while retaining normal feline anatomy. Avoid extra paws, "
        "visible text, dialogue, and impossible hand actions. Vary the events and "
        "give the day a small surprise and resolution. "
        f"Theme: {theme}. Variation seed: {seed}. "
        "Return only JSON with title and shots. Each of the six shots must have "
        "time, beat_zh, image_prompt, and motion_prompt. Use time values in exactly "
        "this order: 早晨, 上午, 中午, 下午, 傍晚, 夜晚. "
        "Write beat_zh in Chinese and both prompts in English. Each motion prompt "
        "describes a single camera motion and simple five-second cat action."
    )
    last_error = None
    for _ in range(2):
        try:
            return parse_story(complete(prompt))
        except (ValueError, json.JSONDecodeError) as error:
            last_error = error
            prompt += " Your previous response was invalid. Return exactly the JSON schema requested."
    raise ValueError(f"Story generation failed after two attempts: {last_error}")


def freeze_reference(image: np.ndarray, path: Path) -> np.ndarray:
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        pixels = (np.clip(image, 0, 1) * 255).round().astype(np.uint8)
        Image.fromarray(pixels).save(path)
    return np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0


def encode_clip(frames: np.ndarray, path: Path) -> None:
    frames = np.asarray(frames)
    if frames.ndim != 4 or frames.shape[0] != 121 or frames.shape[-1] != 3:
        raise ValueError("Wan clip must contain 121 RGB frames")
    height, width = frames.shape[1:3]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{width}x{height}", "-r", "24", "-i", "pipe:0", "-an", "-frames:v", "120",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(path),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        for frame in frames[:120]:
            pixels = (np.clip(frame, 0, 1) * 255).round().astype(np.uint8)
            process.stdin.write(pixels.tobytes())
        process.stdin.close()
        error = process.stderr.read().decode("utf-8", errors="replace")
        if process.wait() != 0:
            raise RuntimeError(f"ffmpeg failed: {error}")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        process.stderr.close()


def concat_clips(paths: list[Path], output: Path) -> None:
    if len(paths) != 6:
        raise ValueError("Exactly six clips are required")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", dir=output.parent, delete=False) as manifest:
        manifest_path = Path(manifest.name)
        for path in paths:
            resolved = Path(path).resolve()
            if not resolved.is_file():
                raise FileNotFoundError(resolved)
            escaped = str(resolved).replace("'", "'\\''")
            manifest.write(f"file '{escaped}'\n")
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
             "-i", str(manifest_path), "-c", "copy", "-an", "-movflags", "+faststart", str(output)],
            capture_output=True, text=True,
        )
        if result.returncode:
            raise RuntimeError(f"ffmpeg concat failed: {result.stderr}")
    finally:
        manifest_path.unlink(missing_ok=True)
