"""Download only the weights used by the local one-pass MiniMax H3 graph."""

from __future__ import annotations

import argparse
import os
import shutil
import struct
from dataclasses import dataclass
from pathlib import Path

if __package__:
    from .network_preflight import SOURCES, probe_url, projected_hours
else:
    from network_preflight import SOURCES, probe_url, projected_hours


@dataclass(frozen=True)
class Weight:
    group: str
    target: str
    repo_hf: str
    repo_ms: str
    remote: str
    minimum_bytes: int


WEIGHTS = (
    Weight("h3", "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", "Comfy-Org/MiniMax-H3", "Comfy-Org/MiniMax-H3", "diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", 18_000_000_000),
    Weight("h3", "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "Comfy-Org/MiniMax-H3", "Comfy-Org/MiniMax-H3", "text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", 13_000_000_000),
    Weight("h3", "vae/minimax_h3_video_vae_int8_convrot.safetensors", "Comfy-Org/MiniMax-H3", "Comfy-Org/MiniMax-H3", "vae/minimax_h3_video_vae_int8_convrot.safetensors", 2_000_000_000),
    Weight("qwen", "diffusion_models/svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors", "nunchaku-ai/nunchaku-qwen-image-edit-2509", "nunchaku-tech/nunchaku-qwen-image-edit-2509", "lightning-251115/svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors", 12_000_000_000),
    Weight("qwen", "clip/qwen_2.5_vl_7b_fp8_scaled.safetensors", "Comfy-Org/Qwen-Image_ComfyUI", "Comfy-Org/Qwen-Image_ComfyUI", "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors", 8_000_000_000),
    Weight("qwen", "vae/qwen_image_vae.safetensors", "Comfy-Org/Qwen-Image_ComfyUI", "Comfy-Org/Qwen-Image_ComfyUI", "split_files/vae/qwen_image_vae.safetensors", 200_000_000),
)

CU128_H3_WEIGHTS = (
    Weight("h3", "diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors", "Comfy-Org/MiniMax-H3", "Comfy-Org/MiniMax-H3", "diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors", 18_000_000_000),
    WEIGHTS[1],
    Weight("h3", "vae/minimax_h3_video_vae_fp16.safetensors", "Comfy-Org/MiniMax-H3", "Comfy-Org/MiniMax-H3", "vae/minimax_h3_video_vae_fp16.safetensors", 4_000_000_000),
)


def healthy(path: Path, minimum_bytes: int) -> bool:
    if not path.is_file() or path.stat().st_size < minimum_bytes:
        return False
    with path.open("rb") as handle:
        header_length = struct.unpack("<Q", handle.read(8))[0]
        return 2 < header_length < 100_000_000 and handle.read(1) == b"{"


def download(weight: Weight, staging: Path, source: str) -> Path:
    if source == "modelscope":
        from modelscope.hub.file_download import model_file_download
        return Path(model_file_download(model_id=weight.repo_ms, file_path=weight.remote, local_dir=str(staging)))
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo_id=weight.repo_hf, filename=weight.remote, local_dir=str(staging)))


def link_to_comfy(data_file: Path, comfy_root: Path, model_root: Path) -> Path:
    """Expose one data-disk weight to a system-disk ComfyUI without copying it."""
    relative = data_file.relative_to(model_root)
    link = comfy_root / "models" / relative
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() and link.resolve() == data_file.resolve():
        return link
    if link.exists() or link.is_symlink():
        raise FileExistsError(f"ComfyUI model path already has a different file: {link}")
    link.symlink_to(data_file.resolve())
    return link


def ensure_source_speed(source: str, minimum_mbps: float = 5.0) -> float:
    """Fail before any weight download when a bounded sample is too slow."""
    url, total = SOURCES[source]
    received, elapsed = probe_url(url)
    speed = received / elapsed
    print(f"NETWORK {source}: {speed / 1e6:.2f} MB/s; {total / 1e9:.0f} GB would take about {projected_hours(total, speed):.1f} hours", flush=True)
    if speed < minimum_mbps * 1_000_000:
        raise RuntimeError(f"{source} is too slow for large model downloads; choose another source or a lower explicit --min-mbps")
    return speed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comfy-root", type=Path, default=Path("/root/autodl-tmp/ComfyUI"))
    parser.add_argument("--model-root", type=Path, help="Model directory on the data disk; default is ComfyUI/models")
    parser.add_argument("--link-into-comfy", action="store_true", help="Symlink data-disk models into ComfyUI/models")
    parser.add_argument("--set", choices=("all", "h3", "qwen"), default="all")
    parser.add_argument("--runtime", choices=("cu130", "cu128"), default="cu130",
                        help="Match the downloaded H3 weights to the workflow JSON and installed PyTorch CUDA build")
    parser.add_argument("--source", choices=("modelscope", "huggingface"), default="modelscope")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--min-mbps", type=float, default=5.0,
                        help="Minimum measured MB/s before starting missing weight downloads")
    parser.add_argument("--skip-network-preflight", action="store_true",
                        help="Use only after independently verifying the source is fast enough")
    args = parser.parse_args()
    models = args.model_root or args.comfy_root / "models"
    available = (CU128_H3_WEIGHTS if args.runtime == "cu128" else WEIGHTS[:3]) + WEIGHTS[3:]
    selected = [weight for weight in available if args.set in ("all", weight.group)]
    missing = []
    for weight in selected:
        path = models / weight.target
        ok = healthy(path, weight.minimum_bytes)
        print(f"{'OK' if ok else 'MISSING/INCOMPLETE'}  {path}", flush=True)
        if not ok:
            missing.append(weight)
    if args.check_only:
        return 1 if missing else 0
    if not args.comfy_root.is_dir():
        parser.error(f"ComfyUI directory does not exist: {args.comfy_root}")
    if models.is_symlink() and not models.exists():
        target = models.resolve(strict=False)
        target.mkdir(parents=True, exist_ok=True)
        print(f"INITIALIZED MODEL DIRECTORY  {target}", flush=True)
    if missing and not args.skip_network_preflight:
        ensure_source_speed(args.source, args.min_mbps)
    staging = models / ".masterpiece_downloads"
    staging.mkdir(parents=True, exist_ok=True)
    for weight in missing:
        destination = models / weight.target
        if shutil.disk_usage(models).free < weight.minimum_bytes + 5_000_000_000:
            raise RuntimeError(f"Not enough free data-disk space for {destination.name}")
        print(f"Downloading {weight.remote} from {args.source} to data disk...", flush=True)
        downloaded = download(weight, staging, args.source)
        if not healthy(downloaded, weight.minimum_bytes):
            raise RuntimeError(f"Download is incomplete or invalid: {downloaded}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(downloaded, destination)
        print(f"READY  {destination} ({destination.stat().st_size:,} bytes)", flush=True)
    if args.link_into_comfy:
        for weight in selected:
            destination = models / weight.target
            if not healthy(destination, weight.minimum_bytes):
                raise RuntimeError(f"Cannot link incomplete model: {destination}")
            link = link_to_comfy(destination, args.comfy_root, models)
            print(f"LINKED  {link} -> {destination}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
