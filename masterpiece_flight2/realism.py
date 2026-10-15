"""Version 3 photoreal-to-artwork projects, approvals and lossless clip caches."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
import subprocess
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from . import core

CANVAS = (1344, 768)
FRAMES = 124
FPS = 24
PIPELINE = 'flux2dev_h3_realism_v3'
H3_PROFILE = 'fl2va_fp8_video_fp16_20step_res_multistep_simple_v1'


def validate_story_v3(raw: str) -> dict:
    text = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.IGNORECASE)
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f'Invalid storyboard JSON: {exc}') from exc
    if not isinstance(plan, dict) or plan.get('schema_version') != 3:
        raise ValueError('This workflow requires schema_version 3')
    if plan.get('conditioning_mode') != 'photoreal_to_artwork':
        raise ValueError('conditioning_mode must be photoreal_to_artwork')
    frames = plan.get('keyframes')
    if not isinstance(frames, list) or [f.get('id') if isinstance(f, dict) else None for f in frames] != [1, 2, 3, 4, 5]:
        raise ValueError('keyframes must contain five ordered frames, ids 1–5')
    # Reuse the established camera/transition contract, including frame 5.
    legacy = copy.deepcopy(plan)
    legacy['schema_version'] = 2
    legacy['keyframes'] = legacy['keyframes'][:4]
    core.validate_story(json.dumps(legacy))
    legacy['keyframes'][3] = dict(frames[4], id=4)
    core.validate_story(json.dumps(legacy))
    for block, fields in (('artwork_extension', ('prompt_en',)),
                          ('morph', ('motion_prompt_en', 'material_progression_en'))):
        value = plan.get(block)
        if not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k].strip() for k in fields):
            raise ValueError(f'{block} requires nonempty {fields}')
    if plan['morph'].get('camera_locked') is not True:
        raise ValueError('morph.camera_locked must be true')
    return plan


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_hash(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            value.update(chunk)
    return value.hexdigest()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    os.replace(temporary, path)


def _json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


class ProjectStore:
    """One project per queue; signatures reject stale generations and approvals."""

    def __init__(self, root: Path, project_id: str):
        self.path = core._project_path(root, project_id)

    def state(self) -> dict:
        path = self.path / 'manifest_v3.json'
        if not path.exists():
            raise ValueError('Create the v3 project in stage 1 first')
        state = json.loads(path.read_text(encoding='utf-8'))
        for filename, key in (('source.png', 'source_sha256'), ('story_v3.json', 'story_sha256')):
            file = self.path / filename
            if not file.is_file() or file_hash(file) != state.get(key):
                raise ValueError(f'{filename} changed; initialize the project in stage 1 again')
        return state

    def _persist(self, state):
        _write(self.path / 'manifest_v3.json', _json_bytes(state))

    def initialize(self, raw_story, painting, canvas_size=CANVAS):
        plan = validate_story_v3(raw_story)
        if (self.path / 'manifest.json').exists():
            raise ValueError('This project_id belongs to v2; choose a new v3 project_id')
        source = core._png_bytes(painting)
        signature = digest(source + _json_bytes(plan) + _json_bytes([PIPELINE, canvas_size]))
        if (self.path / 'manifest_v3.json').exists():
            old = json.loads((self.path / 'manifest_v3.json').read_text(encoding='utf-8'))
            if old['signature'] == signature:
                try:
                    self.state()
                    self.source_canvas()
                    return signature
                except ValueError:
                    pass
            revision = old['revision'] + 1
        else:
            revision = 1
        width, height = canvas_size
        original = core._rgb_uint8(painting)
        scale = min(width / original.shape[1], height / original.shape[0])
        w, h = round(original.shape[1] * scale), round(original.shape[0] * scale)
        x, y = (width - w) // 2, (height - h) // 2
        fitted = core.fit_canvas(original, width, height)
        _write(self.path / 'source.png', source)
        _write(self.path / 'source_canvas.png', core._png_bytes(fitted))
        _write(self.path / 'story_v3.json', _json_bytes(plan))
        self._persist({'pipeline': PIPELINE, 'signature': signature, 'revision': revision,
                       'canvas': [width, height], 'original_box': [x, y, w, h],
                       'source_sha256': digest(source), 'story_sha256': digest(_json_bytes(plan)),
                       'source_canvas_sha256': file_hash(self.path / 'source_canvas.png'),
                       'assets': {}, 'approved': {}, 'clips': {}, 'approved_morph': None})
        return signature

    def story(self):
        return validate_story_v3((self.path / 'story_v3.json').read_text(encoding='utf-8'))

    def source_canvas(self):
        state = self.state()
        path = self.path / 'source_canvas.png'
        if file_hash(path) != state['source_canvas_sha256']:
            raise ValueError('source_canvas changed; initialize the project again')
        return core.read_png(path)

    def restore_original(self, generated):
        result = core._rgb_uint8(generated).copy()
        state = self.state()
        if result.shape[:2] != tuple(reversed(state['canvas'])):
            raise ValueError('Generated image must match the native canvas')
        x, y, w, h = state['original_box']
        original = self.source_canvas()
        result[y:y + h, x:x + w] = original[y:y + h, x:x + w]
        return result

    def _asset(self, state, key):
        scope, name = key.split(':', 1)
        if scope == 'a':
            approval = state['approved'].get(name)
            if not approval:
                raise ValueError(f'{name} is not approved')
            slot = approval['slot']
            record = self._asset(state, 'd:' + slot)
            if record['sha256'] != approval['sha256']:
                raise ValueError(f'{name} approval is stale')
            return record
        record = state['assets'].get(name)
        if not record or record['signature'] != state['signature']:
            raise ValueError(f'{name} is missing or stale')
        for dependency, expected in record['deps'].items():
            if self._asset(state, dependency)['sha256'] != expected:
                raise ValueError(f'{name} is stale after {dependency} changed')
        path = self.path / record['path']
        if not path.is_file() or file_hash(path) != record['sha256']:
            raise ValueError(f'{name} file changed; generate and approve it again')
        return record

    def _image(self, key):
        state = self.state()
        return core.read_png(self.path / self._asset(state, key)['path'])

    def load_approved(self, role):
        return self._image('a:' + role)

    def load_draft(self, role):
        return self._image('d:' + role)

    def save_draft(self, slot, image, token):
        state = self.state()
        if token != state['signature']:
            raise ValueError('Generation token is stale; reload the project')
        if slot == 'art':
            dependencies = []
            image = self.restore_original(image)
        elif slot in ('r5_candidate_1', 'r5_candidate_2', 'r5_candidate_3'):
            dependencies = ['d:art']
        elif slot in ('r1', 'r2', 'r3', 'r4'):
            dependencies = ['a:r5' if slot == 'r4' else f'd:r{int(slot[1]) + 1}']
        else:
            raise ValueError(f'Unknown draft slot: {slot}')
        pixels = core._rgb_uint8(image)
        if pixels.shape[:2] != tuple(reversed(state['canvas'])):
            raise ValueError('Image must match the native canvas')
        content = core._png_bytes(pixels)
        sha = digest(content)
        relative = f'draft/{slot}_{sha[:16]}.png'
        record = {'path': relative, 'sha256': sha, 'signature': token,
                  'deps': {k: self._asset(state, k)['sha256'] for k in dependencies}}
        _write(self.path / relative, content)
        state['assets'][slot] = record
        self._persist(state)
        return record

    def approve_endpoints(self, candidate):
        if candidate not in (1, 2, 3):
            raise ValueError('Choose endpoint candidate 1, 2 or 3')
        state = self.state()
        selected = {}
        for role, slot in (('art', 'art'), ('r5', f'r5_candidate_{candidate}')):
            asset = self._asset(state, 'd:' + slot)
            selected[role] = {'slot': slot, 'sha256': asset['sha256']}
        if any(state['approved'].get(k) != v for k, v in selected.items()):
            state['approved'] = selected
            state['clips'] = {}
            state['approved_morph'] = None
        self._persist(state)

    def approve_frames(self):
        state = self.state()
        self._asset(state, 'a:r5')
        for i in range(1, 5):
            asset = self._asset(state, f'd:r{i}')
            state['approved'][f'r{i}'] = {'slot': f'r{i}', 'sha256': asset['sha256']}
        self._persist(state)

    def _clip_dependencies(self, name):
        if name == 'morph':
            return ('a:r5', 'a:art')
        if name not in ('flight1', 'flight2', 'flight3', 'flight4'):
            raise ValueError('Unknown clip name')
        i = int(name[-1])
        return (f'a:r{i}', f'a:r{i + 1}')

    def save_clip(self, name, frames, token, settings):
        state = self.state()
        if token != state['signature']:
            raise ValueError('Generation token is stale; reload the project')
        keys = self._clip_dependencies(name)
        deps = {key: self._asset(state, key)['sha256'] for key in keys}
        start, end = [self._image(key) for key in keys]
        if np.asarray(frames).shape != (FRAMES, *start.shape):
            raise ValueError('H3 must return 124 frames on the native canvas')
        corrected = core.bridge_h3_frames(frames, start, end, blend_frames=2)
        profile = dict(settings, profile=H3_PROFILE, fps=FPS, frames=FRAMES)
        cache_id = digest(_json_bytes([token, deps, profile]))[:20]
        relative = f'cache/{name}_{cache_id}.npy'
        destination = self.path / relative
        destination.parent.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
            temporary = Path(stream.name)
            np.save(stream, corrected, allow_pickle=False)
        os.replace(temporary, destination)
        for index in (0, 31, 62, 93, 123):
            _write(self.path / f'diagnostics/{name}_raw_{index:03d}.png', core._png_bytes(frames[index]))
        _write(self.path / f'diagnostics/{name}_target.png', core._png_bytes(end))
        state['clips'][name] = {'path': relative, 'sha256': file_hash(destination), 'signature': token,
                                'deps': deps, 'settings': profile}
        if name == 'morph':
            state['approved_morph'] = None
        self._persist(state)
        return corrected

    def _clip(self, state, name):
        record = state['clips'].get(name)
        if not record or record['signature'] != state['signature'] or record['settings']['profile'] != H3_PROFILE:
            raise ValueError(f'{name} cache is missing or stale')
        for dependency, expected in record['deps'].items():
            if self._asset(state, dependency)['sha256'] != expected:
                raise ValueError(f'{name} cache is stale')
        path = self.path / record['path']
        if not path.is_file() or file_hash(path) != record['sha256']:
            raise ValueError(f'{name} cache changed or is stale')
        return record

    def load_clip(self, name):
        state = self.state()
        record = self._clip(state, name)
        return np.load(self.path / record['path'], mmap_mode='r', allow_pickle=False)

    def approve_morph(self):
        state = self.state()
        state['approved_morph'] = self._clip(state, 'morph')['sha256']
        self._persist(state)

    def review_code(self, kind, candidate=1):
        state = self.state()
        if kind == 'endpoints':
            keys = ['d:art', f'd:r5_candidate_{candidate}']
            values = [self._asset(state, key)['sha256'] for key in keys]
        elif kind == 'frames':
            keys = [f'd:r{i}' for i in range(1, 5)] + ['a:r5']
            values = [self._asset(state, key)['sha256'] for key in keys]
        elif kind == 'morph':
            values = [self._clip(state, 'morph')['sha256']]
        else:
            raise ValueError('Unknown review stage')
        return digest(_json_bytes([state['signature'], kind, values]))[:16]

    def load_morph(self):
        state = self.state()
        if not state['approved_morph']:
            raise ValueError('Morph clip is not approved')
        record = self._clip(state, 'morph')
        if record['sha256'] != state['approved_morph']:
            raise ValueError('Morph approval is stale')
        return self.load_clip('morph')


def iter_joined_frames(clips, ending):
    if len(clips) != 5:
        raise ValueError('Four flight clips and one morph clip are required')
    shape = np.asarray(ending).shape
    if any(np.asarray(clip).shape != (FRAMES, *shape) for clip in clips):
        raise ValueError('All five clips must have 124 frames and the same canvas')
    for index, clip in enumerate(clips):
        yield from clip[0 if index == 0 else 1:]
    for _ in range(FPS):
        yield ending


def encode_frames(frames, output: Path, size=(1280, 720)):
    """Stream frames to ffmpeg; never allocate the full 640-frame float batch."""
    if not shutil.which('ffmpeg'):
        raise RuntimeError('ffmpeg is missing; run the v3 preflight before rendering')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    width, height = size
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError('Video dimensions must be positive even integers')
    fd, name = tempfile.mkstemp(suffix='.mp4', dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    command = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
               '-s', f'{width}x{height}', '-r', str(FPS), '-i', 'pipe:0', '-an',
               '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p',
               '-movflags', '+faststart', str(temporary)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    count = 0
    try:
        for frame in frames:
            rgb = core._rgb_uint8(frame)
            ratio = min(width / rgb.shape[1], height / rgb.shape[0])
            w, h = max(1, round(rgb.shape[1] * ratio)), max(1, round(rgb.shape[0] * ratio))
            scaled = np.asarray(Image.fromarray(rgb).resize((w, h), Image.Resampling.LANCZOS))
            x, y = (width - w) // 2, (height - h) // 2
            canvas = np.pad(scaled, ((y, height - h - y), (x, width - w - x), (0, 0)), mode='edge')
            process.stdin.write(canvas.tobytes())
            count += 1
        process.stdin.close()
        error = process.stderr.read().decode(errors='replace')
        if process.wait() != 0 or count == 0:
            raise RuntimeError(f'Video encoding failed: {error}')
        os.replace(temporary, output)
    except BrokenPipeError as exc:
        raise RuntimeError('ffmpeg stopped before video encoding completed') from exc
    finally:
        if process.poll() is None:
            process.kill(); process.wait()
        if not process.stdin.closed: process.stdin.close()
        process.stderr.close()
        temporary.unlink(missing_ok=True)
    return count
