"""Install the three pinned JoyAI Plus BF16 files only after bounded route probes and SHA256 checks.

Run on the AutoDL data disk in no-GPU mode. No Torch or ComfyUI packages are changed.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
from pathlib import Path
import shutil

if __package__:
    from .ensure_models import _model_root, fetch_verified, probe_source, verify_audio_file
else:
    from ensure_models import _model_root, fetch_verified, probe_source, verify_audio_file


REPOSITORY = "jdopensource/JoyAI-Image-Edit-Plus-ComfyUI"
REVISION = "a90b1a3ba2829a476dbcaeb9c4819601a8b1e561"
MODEL_SPECS = {
    "diffusion_models/joyai_image_edit_plus_bf16.safetensors": (
        32_527_457_192, "80372f34c379b96a1d8cecc57a3816c5ae2c4d3844483016930a7806875c8103"),
    "text_encoders/qwen3vl_8b_joyimage_edit_plus_bf16.safetensors": (
        17_534_340_584, "a1eee8233f3063466dd3b06e857b0a2cf13a77c543908374771d51a546beb2e0"),
    "vae/wan_2.1_vae.safetensors": (
        253_815_318, "2fc39d31359a4b0a64f55876d8ff7fa8d780956ae2cb13463b0223e15148976b"),
}
SOURCES = {
    "hf-mirror": "https://hf-mirror.com",
    "huggingface": "https://huggingface.co",
}


def verify_spec(path: Path, spec: tuple[int, str]) -> bool:
    return verify_audio_file(path, *spec)


def qualified_routes(relative: str, size: int, min_mbps: float = 5.0, source: str = "auto"):
    selected = SOURCES if source == "auto" else {source: SOURCES[source]}
    urls = {name: f"{base}/{REPOSITORY}/resolve/{REVISION}/{relative}" for name, base in selected.items()}
    qualified = []
    with ThreadPoolExecutor(max_workers=len(urls)) as pool:
        jobs = {pool.submit(probe_source, url): (name, url) for name, url in urls.items()}
        for job in as_completed(jobs):
            name, url = jobs[job]
            try:
                bytes_read, elapsed = job.result()
                speed = bytes_read / elapsed
                print(f"PROBE {name} {relative}: {speed / 1e6:.2f} MB/s, "
                      f"estimate {size / speed / 60:.1f} min", flush=True)
                if speed >= min_mbps * 1e6:
                    qualified.append((speed, name, url))
            except (RuntimeError, OSError) as error:
                print(f"UNAVAILABLE {name} {relative}: {error}", flush=True)
    return sorted(qualified, reverse=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-root", type=Path, default=Path("/root/ComfyUI"))
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--source", choices=["auto", *SOURCES], default="auto")
    parser.add_argument("--min-mbps", type=float, default=5.0)
    args = parser.parse_args(argv)
    if args.min_mbps <= 0:
        parser.error("--min-mbps must be positive")
    models = _model_root(args.comfy_root)
    missing = []
    for relative, spec in MODEL_SPECS.items():
        path = models / relative
        if verify_spec(path, spec):
            print(f"OK {path} SHA256 verified", flush=True)
        else:
            print(f"MISSING/INCOMPLETE {path}", flush=True)
            missing.append((relative, spec))
    if not missing:
        return 0
    if args.check_only or not (args.probe_only or args.download):
        return 1
    staging = models / ".cat_vlog_h3_downloads" / "joyai"
    remaining = sum(size for _, (size, _) in missing)
    already = sum(min((staging / (Path(relative).name + ".part")).stat().st_size, spec[0])
                  for relative, spec in missing if (staging / (Path(relative).name + ".part")).exists())
    if args.download and shutil.disk_usage(models).free < remaining - already + 2_000_000_000:
        raise RuntimeError("Not enough free space on the AutoDL data disk for JoyAI Plus BF16")
    for relative, spec in missing:
        size, digest = spec
        routes = qualified_routes(relative, size, args.min_mbps, args.source)
        if not routes:
            print(f"STOP: no route met {args.min_mbps:g} MB/s for {relative}; no large download started", flush=True)
            return 3
        if args.probe_only:
            continue
        path = models / relative
        partial = staging / (path.name + ".part")
        for speed, name, url in routes:
            print(f"DOWNLOAD {name}: {relative}, resuming {partial}; final SHA256 must match", flush=True)
            try:
                fetch_verified(url, partial, path, expected_bytes=size, expected_sha256=digest,
                               min_bytes_per_second=int(args.min_mbps * 500_000),
                               max_seconds=max(3600, math.ceil(size / (args.min_mbps * 1e6) * 3)),
                               show_progress=True)
                print(f"READY {path} SHA256 verified", flush=True)
                break
            except RuntimeError as error:
                print(str(error), flush=True)
                if partial.exists() and partial.stat().st_size >= size:
                    return 2
        else:
            print(f"PAUSED {relative}: verified routes failed; re-run to resume .part", flush=True)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
