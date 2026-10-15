"""Measure a bounded download sample before starting large model or PyTorch transfers."""

from __future__ import annotations

import argparse
import time
from urllib.request import Request, urlopen


SOURCES = {
    "pytorch": (
        "https://download-r2.pytorch.org/whl/cu130/torch-2.10.0%2Bcu130-cp312-cp312-manylinux_2_28_x86_64.whl",
        642_000_000,
    ),
    "modelscope": (
        "https://modelscope.cn/api/v1/models/Comfy-Org/MiniMax-H3/repo?Revision=master&FilePath=diffusion_models%2Fminimax_h3_fl2va_pruned_fp8_scaled.safetensors",
        65_000_000_000,
    ),
    "huggingface": (
        "https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors",
        65_000_000_000,
    ),
    "github": (
        "https://github.com/nunchaku-ai/nunchaku/releases/download/v1.2.1/nunchaku-1.2.1+cu12.8torch2.8-cp312-cp312-linux_x86_64.whl",
        140_000_000,
    ),
}


def projected_hours(total_bytes: int, bytes_per_second: float) -> float:
    return float("inf") if bytes_per_second <= 0 else total_bytes / bytes_per_second / 3600


def probe_url(url: str, max_bytes: int = 8 * 1024 * 1024, max_seconds: float = 20) -> tuple[int, float]:
    if max_bytes < 1 or max_seconds <= 0:
        raise ValueError("Probe size and duration must be positive")
    request = Request(url, headers={
        "Range": f"bytes=0-{max_bytes - 1}",
        "User-Agent": "masterpiece-flight2-network-preflight/1",
    })
    started = time.monotonic()
    received = 0
    with urlopen(request, timeout=min(max_seconds, 10)) as response:
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" in content_type or "application/json" in content_type:
            raise RuntimeError(f"Source returned {content_type} instead of model bytes")
        while received < max_bytes and time.monotonic() - started < max_seconds:
            chunk = response.read(min(64 * 1024, max_bytes - received))
            if not chunk:
                break
            received += len(chunk)
    if received == 0:
        raise RuntimeError("Source sent no bytes")
    return received, max(time.monotonic() - started, 1e-6)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=tuple(SOURCES), required=True)
    parser.add_argument("--min-mbps", type=float, default=5.0,
                        help="Abort the planned large download below this measured MB/s")
    parser.add_argument("--seconds", type=float, default=20)
    args = parser.parse_args()
    url, total = SOURCES[args.source]
    try:
        received, elapsed = probe_url(url, max_seconds=args.seconds)
    except Exception as exc:
        print(f"PROBE FAILED: {exc}")
        return 2
    speed = received / elapsed
    print(f"PROBE {args.source}: {received / 1e6:.1f} MB in {elapsed:.1f}s = {speed / 1e6:.2f} MB/s")
    print(f"At that speed, {total / 1e9:.1f} GB would take about {projected_hours(total, speed):.1f} hours")
    if speed < args.min_mbps * 1_000_000:
        print("TOO SLOW: do not start the large download from this source on a paid GPU")
        return 1
    print("SPEED OK: source is fast enough to try; keep watching the first large file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
