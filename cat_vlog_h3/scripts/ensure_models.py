"""Check existing weights; probe file URLs and resume the audio VAE with curl, without a hub SDK."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import sys
import tempfile
import time

EXISTING_MODELS = {
    "diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors": 18_000_000_000,
    "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors": 13_000_000_000,
    "vae/minimax_h3_video_vae_fp16.safetensors": 4_000_000_000,
}
AUDIO_RELATIVE = "vae/minimax_h3_audio_vae_fp32.safetensors"
AUDIO_SIZE = 605_254_808
AUDIO_SHA256 = "8e505d95dd1561d47abd43d4238fd40d9bb1ae9e147ed0a4cba778d76ae4db48"
MODELSCOPE_URL = (
    "https://modelscope.cn/api/v1/models/Comfy-Org/MiniMax-H3/repo?"
    "Revision=master&FilePath=vae%2Fminimax_h3_audio_vae_fp32.safetensors"
)


SOURCES = {
    "modelscope": MODELSCOPE_URL,
    "hf-mirror": "https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/" + AUDIO_RELATIVE,
    "huggingface": "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/" + AUDIO_RELATIVE,
}


def verify_audio_file(path: Path, expected_bytes: int = AUDIO_SIZE, expected_sha256: str = AUDIO_SHA256) -> bool:
    path = Path(path)
    if not path.is_file() or path.stat().st_size != expected_bytes:
        return False
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest() == expected_sha256


def _curl():
    executable = shutil.which("curl")
    if not executable:
        raise RuntimeError("curl is missing; install curl before downloading (no Python hub SDK is needed)")
    return executable


def _stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def probe_source(url: str, max_bytes: int = 4 * 1024 * 1024, max_seconds: float = 20) -> tuple[int, float]:
    """Stop after exactly the requested bytes or a wall-clock deadline, including DNS."""
    if max_bytes < 1 or max_seconds <= 0:
        raise ValueError("Probe size and time must be positive")
    start = time.monotonic()
    received = 0
    with tempfile.TemporaryDirectory(prefix="cat_h3_probe_") as directory:
        headers = Path(directory) / "headers"
        command = [_curl(), "--fail", "--location", "--silent", "--show-error",
                   "--connect-timeout", str(min(8, max_seconds)), "--max-time", str(max_seconds),
                   "--range", f"0-{max_bytes-1}", "--dump-header", str(headers), url]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        selector = selectors.DefaultSelector()
        selector.register(process.stdout, selectors.EVENT_READ)
        try:
            while received < max_bytes:
                remaining = max_seconds - (time.monotonic() - start)
                if remaining <= 0:
                    break
                if not selector.select(timeout=min(0.1, remaining)):
                    continue
                chunk = os.read(process.stdout.fileno(), min(64 * 1024, max_bytes-received))
                if not chunk:
                    break
                received += len(chunk)
        finally:
            selector.close()
            _stop(process)
            error = process.stderr.read().decode("utf-8", errors="replace").strip()
            process.stdout.close()
            process.stderr.close()
        elapsed = max(time.monotonic() - start, 1e-6)
        header_text = headers.read_text(errors="replace") if headers.exists() else ""
        responses = re.split(r"(?m)^HTTP/", header_text)
        final = responses[-1] if len(responses) > 1 else ""
        status = re.match(r"\S+\s+(\d+)", final)
        if re.search(r"(?im)^content-type:.*(?:text/html|application/json)", final):
            raise RuntimeError("Source returned HTML/JSON, not model data")
        content_range = re.search(r"(?im)^content-range:\s*bytes\s+0-(\d+)/(\d+)", final)
        if not status or status.group(1) != "206" or not content_range:
            raise RuntimeError("Source did not confirm HTTP 206 byte range" + (f": {error[:160]}" if error else ""))
        if received != max_bytes or int(content_range.group(1)) != max_bytes-1:
            raise RuntimeError(f"Incomplete bounded probe: {received}/{max_bytes} bytes in {elapsed:.1f}s")
        return received, elapsed


def probe_sources(source="auto", min_mbps=2.0):
    selected = SOURCES if source == "auto" else {source: SOURCES[source]}
    eligible = []
    with ThreadPoolExecutor(max_workers=len(selected)) as pool:
        jobs = {pool.submit(probe_source, url): (name, url) for name, url in selected.items()}
        for job in as_completed(jobs):
            name, url = jobs[job]
            try:
                size, seconds = job.result()
                speed = size / seconds
                print(f"PROBE {name}: {speed/1e6:.2f} MB/s; audio VAE estimate {AUDIO_SIZE/speed/60:.1f} min", flush=True)
                if speed >= min_mbps * 1e6:
                    eligible.append((speed, name, url))
            except (RuntimeError, OSError) as error:
                print(f"UNAVAILABLE {name}: {error}", flush=True)
    return sorted(eligible, reverse=True)


def fetch_verified(url, partial, destination, expected_bytes=AUDIO_SIZE, expected_sha256=AUDIO_SHA256,
                   min_bytes_per_second=1_000_000, max_seconds=900, show_progress=False):
    """Resume the same probed URL to a .part file, then atomically install only after SHA verification."""
    partial, destination = Path(partial), Path(destination)
    partial.parent.mkdir(parents=True, exist_ok=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if verify_audio_file(partial, expected_bytes, expected_sha256):
        os.replace(partial, destination)
        return destination
    if partial.exists() and partial.stat().st_size >= expected_bytes:
        raise RuntimeError(f"Existing partial file failed size/SHA256; keep it for inspection: {partial}")
    command = [_curl(), "--fail", "--location", "--show-error", "--connect-timeout", "10",
               "--max-time", str(max_seconds), "--speed-time", "25", "--speed-limit", str(max(1,int(min_bytes_per_second))),
               "--continue-at", "-", "--output", str(partial)]
    if not show_progress:
        command.append("--silent")
    command.append(url)
    process = subprocess.Popen(command)
    try:
        code = process.wait(timeout=max_seconds + 2)
    finally:
        _stop(process)
    if not verify_audio_file(partial, expected_bytes, expected_sha256):
        if partial.exists() and partial.stat().st_size == expected_bytes:
            raise RuntimeError(f"Downloaded file failed official SHA256: {partial}; not installed")
        raise RuntimeError(f"Download paused (curl exit {code}); partial bytes retained at {partial}")
    os.replace(partial, destination)
    return destination


def _model_root(comfy_root: Path) -> Path:
    models = comfy_root / "models"
    if not models.is_symlink():
        raise RuntimeError(f"Expected ComfyUI/models to be a data-disk symlink: {models}")
    target = models.resolve(strict=False)
    if not target.is_relative_to(Path("/root/autodl-tmp")):
        raise RuntimeError(f"Model symlink points outside the AutoDL data disk: {target}")
    target.mkdir(parents=True, exist_ok=True)
    return models


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-root", type=Path, default=Path("/root/ComfyUI"))
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--download-audio", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--source", choices=["auto", *SOURCES], default="auto")
    parser.add_argument("--min-mbps", type=float, default=2.0)
    args = parser.parse_args(argv)
    if args.min_mbps <= 0:
        parser.error("--min-mbps must be positive")
    if args.probe_only:
        return 0 if probe_sources(args.source, args.min_mbps) else 3
    if not args.comfy_root.is_dir():
        parser.error(f"ComfyUI directory does not exist: {args.comfy_root}")
    models = _model_root(args.comfy_root)
    missing = []
    for relative, minimum in EXISTING_MODELS.items():
        path = models / relative
        ok = path.is_file() and path.stat().st_size >= minimum
        print(f"{'OK' if ok else 'MISSING/INCOMPLETE'}  {path}", flush=True)
        if not ok:
            missing.append(relative)
    if missing:
        print("Existing H3 models are incomplete; this script will not re-download them", flush=True)
        return 2
    audio = models / AUDIO_RELATIVE
    if verify_audio_file(audio):
        print(f"OK  {audio}  SHA256 verified", flush=True)
        return 0
    print(f"MISSING/INCOMPLETE  {audio}", flush=True)
    if args.check_only or not args.download_audio:
        return 1
    staging = models / ".cat_vlog_h3_downloads"
    partial = staging / (Path(AUDIO_RELATIVE).name + ".part")
    # Recover a completed old SDK transfer without making another network request.
    for path in (partial, staging / AUDIO_RELATIVE):
        if verify_audio_file(path):
            audio.parent.mkdir(parents=True, exist_ok=True)
            os.replace(path, audio)
            print(f"READY  {audio}  SHA256 verified", flush=True)
            return 0
    if shutil.disk_usage(models).free < AUDIO_SIZE + 200_000_000:
        raise RuntimeError("Not enough data-disk space for the audio VAE")
    routes = probe_sources(args.source, args.min_mbps)
    if not routes:
        print(f"STOP: no route reached {args.min_mbps:g} MB/s. No full download started; keep GPU off.", flush=True)
        return 3
    for speed, name, url in routes:
        print(f"DOWNLOAD {name}: continuing {partial}; final file must match the official SHA256", flush=True)
        try:
            fetch_verified(url, partial, audio, min_bytes_per_second=args.min_mbps * 500_000, show_progress=True)
            print(f"READY  {audio}  SHA256 verified", flush=True)
            return 0
        except RuntimeError as error:
            print(str(error), flush=True)
            if partial.exists() and partial.stat().st_size >= AUDIO_SIZE:
                return 2
    print("PAUSED: all qualified routes failed; re-run this command to resume the .part file", flush=True)
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nPAUSED: partial download retained; re-run the same command to resume", file=sys.stderr)
        raise SystemExit(130)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f"STOP: {error}", file=sys.stderr)
        raise SystemExit(2)
