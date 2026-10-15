"""Read-only v4 preflight. Never loads weights, starts ComfyUI or requests GPU generation."""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import shutil
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cat_vlog_h3 import core
from cat_vlog_h3.workflow_builder import JOYAI_MODEL, JOYAI_CLIP, JOYAI_VAE, H3_MODEL, H3_CLIP, H3_VIDEO_VAE, H3_AUDIO_VAE
from cat_vlog_h3.scripts.check_runtime import graph_errors
from cat_vlog_h3.scripts.ensure_joyai_models import MODEL_SPECS
from cat_vlog_h3.scripts.ensure_models import EXISTING_MODELS, AUDIO_RELATIVE, AUDIO_SIZE


def graph_configuration_errors(graph):
    errors = []
    expected = {'UNETLoader': {JOYAI_MODEL, H3_MODEL}, 'CLIPLoader': {JOYAI_CLIP, H3_CLIP},
                'VAELoader': {JOYAI_VAE, H3_VIDEO_VAE, H3_AUDIO_VAE}}
    for kind, names in expected.items():
        actual = [node['widgets_values'][0] for node in graph['nodes'] if node['type'] == kind]
        if len(actual) != len(names) or set(actual) != names:
            errors.append(f'{kind}: model files differ from the reviewed v4 profile')
    for node in graph['nodes']:
        names = [item['name'] for item in node.get('inputs', [])]
        if len(names) != len(set(names)):
            errors.append(f"duplicate inputs: {node.get('title', node['type'])}")
        if node['type'] == 'KSampler' and node['widgets_values'][2:7] != [40, 4.0, 'euler', 'normal', 1]:
            errors.append('JoyAI first-frame sampling parameters differ from BF16/40 steps/CFG4/euler/normal')
        if node['type'] == 'BasicScheduler' and node['widgets_values'] != ['simple', 20, 1]:
            errors.append('H3 scheduler differs from the 20-step base profile')
        if node['type'] == 'KSamplerSelect' and node['widgets_values'] != ['res_multistep']:
            errors.append('H3 sampler differs from res_multistep')
        if node['type'] == 'MiniMaxH3ImageToVideo':
            if node['widgets_values'][1:3] != [1344, 768]:
                errors.append('H3 resolution differs from 1344x768')
            if not any(item['name'] == 'length' and item.get('link') for item in node['inputs']):
                errors.append('H3 length is not connected to per-shot duration')
            if any(item['name'] == 'last_frame' and item.get('link') for item in node['inputs']):
                errors.append('Unexpected last-frame input')
    return sorted(set(errors))


def inspect_artifacts(project, story_path=None):
    project = Path(project)
    workflow = project / 'workflows/01_one_pass_10x7s_h3_cu128.json'
    graph = json.loads(workflow.read_text(encoding='utf-8'))
    story_path = Path(story_path) if story_path else project / 'storyboards/dance_club_audition_story.json'
    story = core.validate_story(story_path.read_text(encoding='utf-8-sig'))
    catalog = core.load_reference_catalog(project / 'assets')
    shots = []
    for shot in story['shots']:
        index = shot['id']
        shots.append({'id': index, 'references': core.resolve_reference_assets(story, index, catalog),
                      'timing': core.resolve_duration(shot['duration_seconds']), 'prompt_lengths': core.prompt_length_report(story, index)})
    return {'schema_version': 4, 'errors': graph_configuration_errors(graph), 'workflow': str(workflow),
            'model_quality_verified': False, 'quality_status': 'pending_user_sample_review',
            'total_frames': sum(shot['timing']['frames'] for shot in shots), 'shots': shots,
            'runtime_text_budget': '4096 plain-text tokens; checked using the installed CLIP tokenizer before encoding; images excluded from this project text budget'}


def inspect_model_files(comfy_root):
    models = Path(comfy_root) / 'models'
    errors, files = [], {}
    resolved = models.resolve()
    if not models.is_symlink() or not resolved.is_relative_to(Path('/root/autodl-tmp')):
        errors.append('ComfyUI/models must be a symlink into /root/autodl-tmp on this AutoDL instance')
    requirements = {**{name: size for name, (size, _) in MODEL_SPECS.items()}, **EXISTING_MODELS, AUDIO_RELATIVE: AUDIO_SIZE}
    for name, size in requirements.items():
        path = models / name
        ok = path.is_file() and (path.stat().st_size == size if name in MODEL_SPECS or name == AUDIO_RELATIVE else path.stat().st_size >= size)
        files[name] = {'present_size_ok': ok, 'sha256_verified_by_this_check': False}
        if not ok:
            errors.append(f'missing/incomplete model: {name}; use the verified installer in no-GPU mode')
    for binary in ('ffmpeg', 'ffprobe'):
        if not shutil.which(binary):
            errors.append(f'missing executable: {binary}')
    return errors, files


def native_adapter_errors(comfy_root):
    source = Path(comfy_root) / 'comfy_extras/nodes_joyimage.py'
    if not source.is_file():
        return ['missing native JoyAI source; update ComfyUI before downloading new weights']
    tree = ast.parse(source.read_text(encoding='utf-8'))
    function = next((item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == '_encode'), None)
    if function is None or [item.arg for item in function.args.args] != ['clip', 'prompt', 'vae', 'images']:
        return ['native JoyAI encoding API changed; review the wrapper before generation']
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--story', type=Path)
    parser.add_argument('--url', help='Running ComfyUI URL, for example http://127.0.0.1:6006')
    parser.add_argument('--comfy-root', type=Path)
    parser.add_argument('--check-models', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = inspect_artifacts(args.project_root, args.story)
        if args.url:
            with urlopen(args.url.rstrip('/') + '/object_info', timeout=15) as response:
                definitions = json.load(response)
            graph = json.loads(Path(report['workflow']).read_text())
            report['errors'].extend(graph_errors(graph, definitions))
            try:
                with urlopen(args.url.rstrip('/') + '/system_stats', timeout=5) as response:
                    report['runtime_system'] = json.load(response).get('system', {})
            except OSError:
                report['runtime_system'] = {'version': 'unavailable; node signatures were inspected'}
        else:
            report['runtime_node_check'] = 'not_run_offline'
        if args.comfy_root:
            report['errors'].extend(native_adapter_errors(args.comfy_root))
        if args.check_models:
            if not args.comfy_root:
                parser.error('--check-models requires --comfy-root')
            errors, files = inspect_model_files(args.comfy_root)
            report['errors'].extend(errors)
            report['models'] = files
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report['errors'] else 0
    except (OSError, ValueError, KeyError) as error:
        print(f'PREFLIGHT FAILED: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
