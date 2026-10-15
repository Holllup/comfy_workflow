"""Read-only environment inspection, bounded probes and verified v3 model downloads."""

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Model:
    group: str
    target: str
    repo: str
    remote: str
    estimated_bytes: int
    sha256: str


# SHA256 values from the official Comfy-Org Hugging Face file pages, 2026-10-11.
MODELS = (
    Model('flux', 'diffusion_models/flux2_dev_fp8mixed.safetensors', 'Comfy-Org/flux2-dev',
          'split_files/diffusion_models/flux2_dev_fp8mixed.safetensors', 35_500_000_000,
          '863a82e4ff950a42a6b0e80bea824828f129eb1a8fbbdbd9e8cb29859127b486'),
    Model('flux', 'text_encoders/mistral_3_small_flux2_bf16.safetensors', 'Comfy-Org/flux2-dev',
          'split_files/text_encoders/mistral_3_small_flux2_bf16.safetensors', 35_600_000_000,
          '7d79902f60b1aeb3a6de2cfad02f4367b5e300a1387de3d03ac717cfa3df117c'),
    Model('flux', 'vae/flux2-vae.safetensors', 'Comfy-Org/flux2-dev',
          'split_files/vae/flux2-vae.safetensors', 336_000_000,
          'd64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5'),
    Model('h3', 'diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors', 'Comfy-Org/MiniMax-H3',
          'diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors', 21_000_000_000,
          '12944c1f7791637e7de12208aef04da82bd26b95271b1b47d817364315ade993'),
    Model('h3', 'text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 'Comfy-Org/MiniMax-H3',
          'text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 15_700_000_000,
          '35a88d51044231fe332301d7a62aa81e3f2cba62febeb446e2c1e3e0ef76f2c6'),
    Model('h3', 'vae/minimax_h3_video_vae_fp16.safetensors', 'Comfy-Org/MiniMax-H3',
          'vae/minimax_h3_video_vae_fp16.safetensors', 5_210_000_000,
          '7c1f131492e7eddacaac9069a61b81bdd39de5cc96561e677c5eab1cdce5e522'),
)
REQUIRED_NODES = {
    'UNETLoader', 'CLIPLoader', 'VAELoader', 'VAEEncode', 'VAEDecode', 'CLIPTextEncode',
    'FluxGuidance', 'ReferenceLatent', 'Flux2Scheduler', 'EmptyFlux2LatentImage',
    'BasicGuider', 'BasicScheduler', 'KSamplerSelect', 'RandomNoise', 'SamplerCustomAdvanced',
    'MiniMaxH3ImageToVideo', 'CreateVideo', 'SaveVideo', 'PreviewImage', 'PreviewAny',
    'ArtV3Prepare', 'ArtV3Prompt', 'ArtV3SaveImage', 'ArtV3LoadEndpoints',
    'ArtV3KeyframeStart', 'ArtV3LoadFrames', 'ArtV3SaveClip', 'ArtV3Finish', 'ArtOutputPrefix',
}


def verified(path, expected):
    if not Path(path).is_file(): return False
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''): value.update(chunk)
    return value.hexdigest() == expected


def model_url(model, source):
    if source == 'huggingface':
        return f'https://huggingface.co/{model.repo}/resolve/main/{model.remote}'
    return f'https://modelscope.cn/api/v1/models/{model.repo}/repo?Revision=master&FilePath={quote(model.remote, safe="")}'


def probe(url, max_bytes=4 * 1024 * 1024, opener=urlopen):
    request = Request(url, headers={'Range': f'bytes=0-{max_bytes - 1}', 'User-Agent': 'masterpiece-flight-v3/1'})
    started = time.monotonic()
    received = 0
    with opener(request, timeout=20) as response:
        if response.status != 206:
            raise RuntimeError('Probe requires HTTP 206; full response is not a valid speed sample')
        if not response.headers.get('Content-Range', '').startswith(f'bytes 0-{max_bytes - 1}/'):
            raise RuntimeError('Unexpected Content-Range for bounded sample')
        content = response.headers.get('Content-Type', '').lower()
        if 'html' in content or 'json' in content:
            raise RuntimeError('Model URL returned a web page instead of model bytes')
        while received < max_bytes:
            if time.monotonic() - started > 20: raise RuntimeError('Probe sample timed out')
            chunk = response.read(min(65536, max_bytes - received))
            if not chunk: break
            received += len(chunk)
    if received != max_bytes: raise RuntimeError('Incomplete speed sample')
    return received / max(time.monotonic() - started, 0.000001)


def fetch_model(model, staging, source):
    if source == 'modelscope':
        from modelscope.hub.file_download import model_file_download
        return Path(model_file_download(model_id=model.repo, file_path=model.remote, local_dir=str(staging)))
    from huggingface_hub import hf_hub_download
    return Path(hf_hub_download(repo_id=model.repo, filename=model.remote, local_dir=str(staging)))


def install(models, root, source, fetch=fetch_model, probe_fn=probe, minimum_mbps=5):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    missing = [model for model in models if not verified(root / model.target, model.sha256)]
    needed = sum(model.estimated_bytes for model in missing)
    if missing and shutil.disk_usage(root).free < needed + 5_000_000_000:
        raise RuntimeError(f'Insufficient data-disk space: need about {(needed + 5e9) / 1e9:.1f} GB free')
    staging = root / '.realism_downloads'
    for model in missing:
        speed = probe_fn(model_url(model, source))
        print(f'{model.target}: {speed / 1e6:.2f} MB/s; estimated {model.estimated_bytes / speed / 3600:.2f} hours', flush=True)
        if speed < minimum_mbps * 1e6:
            raise RuntimeError('Source too slow; compare the other source before downloading')
        staging.mkdir(exist_ok=True)
        downloaded = fetch(model, staging, source)
        if not verified(downloaded, model.sha256):
            raise RuntimeError(f'Official checksum mismatch: {downloaded}')
        destination = root / model.target
        destination.parent.mkdir(parents=True, exist_ok=True)
        os.replace(downloaded, destination)
        print(f'VERIFIED {destination}', flush=True)
    return len(missing)


def check_nodes(info):
    errors = [f'Missing node: {name}' for name in sorted(REQUIRED_NODES - set(info))]
    for kind, required in {'MiniMaxH3ImageToVideo': ('first_frame', 'last_frame'),
                           'Flux2Scheduler': ('steps', 'width', 'height')}.items():
        if kind in info:
            inputs = info[kind].get('input', {})
            names = set(inputs.get('required', {})) | set(inputs.get('optional', {}))
            errors += [f'{kind} missing input: {name}' for name in required if name not in names]
    return errors


def check_model_location(root, data_root=Path('/root/autodl-tmp')):
    if data_root.is_dir() and not Path(root).resolve().is_relative_to(data_root.resolve()):
        raise RuntimeError('Models must be on the AutoDL data disk; configure ComfyUI/models or --model-root under /root/autodl-tmp first')


def inspect_environment(comfy_root, model_root, url):
    report = {'python': platform.python_version(), 'platform': platform.platform(),
              'comfy_root': str(comfy_root), 'model_root_resolved': str(model_root.resolve()),
              'ffmpeg': shutil.which('ffmpeg'), 'models': [], 'problems': []}
    try:
        import torch
        report['torch'] = torch.__version__; report['torch_cuda'] = torch.version.cuda
        report['gpus'] = [{'name': torch.cuda.get_device_name(i),
                           'vram_gb': round(torch.cuda.get_device_properties(i).total_memory / 1e9, 1)}
                          for i in range(torch.cuda.device_count())]
    except ImportError:
        report['problems'].append('PyTorch is not installed in this Python environment')
    try: report['ram_gb'] = round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1e9, 1)
    except (ValueError, OSError): report['ram_gb'] = None
    path = model_root.resolve()
    while not path.exists() and path != path.parent: path = path.parent
    report['disk_free_gb'] = round(shutil.disk_usage(path).free / 1e9, 1)
    if not report['ffmpeg']: report['problems'].append('ffmpeg is required for streaming final assembly')
    for model in MODELS:
        target = model_root / model.target
        report['models'].append({'file': str(target), 'bytes': target.stat().st_size if target.is_file() else 0,
                                 'expected_sha256': model.sha256, 'status': 'present_unverified' if target.is_file() else 'missing'})
    try:
        with urlopen(url.rstrip('/') + '/object_info', timeout=10) as response: info = json.load(response)
        report['problems'] += check_nodes(info)
    except Exception as exc:
        report['problems'].append(f'Cannot inspect ComfyUI nodes at {url}: {exc}')
    report['note'] = 'No files or packages changed. File presence is not checksum verification. GPU generation remains a separate acceptance test.'
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'probe', 'verify', 'download'))
    parser.add_argument('--comfy-root', type=Path, default=Path('/root/ComfyUI'))
    parser.add_argument('--model-root', type=Path)
    parser.add_argument('--url', default='http://127.0.0.1:6006')
    parser.add_argument('--set', choices=('all', 'flux', 'h3'), default='all')
    parser.add_argument('--source', choices=('modelscope', 'huggingface'), default='modelscope')
    parser.add_argument('--min-mbps', type=float, default=5)
    args = parser.parse_args(argv)
    root = args.model_root or args.comfy_root / 'models'
    models = [model for model in MODELS if args.set in ('all', model.group)]
    if args.action == 'inspect':
        report = inspect_environment(args.comfy_root, root, args.url)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['problems'] else 0
    if args.action == 'probe':
        ok = True
        for model in models:
            try:
                speed = probe(model_url(model, args.source))
                print(f'{model.target}: {speed / 1e6:.2f} MB/s, about {model.estimated_bytes / speed / 3600:.2f} hours')
                ok = ok and speed >= args.min_mbps * 1e6
            except Exception as exc:
                print(f'PROBE FAILED {model.target}: {exc}'); ok = False
        return 0 if ok else 1
    if args.action == 'verify':
        ok = True
        for model in models:
            good = verified(root / model.target, model.sha256)
            print(f'{"VERIFIED" if good else "MISSING/CHECKSUM MISMATCH"} {root / model.target}')
            ok = ok and good
        return 0 if ok else 1
    if not args.comfy_root.is_dir(): parser.error('ComfyUI directory does not exist')
    check_model_location(root)
    print('Run in AutoDL no-GPU mode. Ctrl+C stops safely; rerun the same command to resume through the Hub client.', flush=True)
    install(models, root, args.source, minimum_mbps=args.min_mbps)
    return 0


if __name__ == '__main__':
    try: raise SystemExit(main())
    except (ValueError, RuntimeError) as exc:
        print(f'STOP: {exc}', file=sys.stderr); raise SystemExit(2)
