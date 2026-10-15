#!/usr/bin/env python3
"""Read-only validation using the actual cat_vlog_h3 core and prompt composers."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path
import sys


def find_project(explicit: Path | None) -> Path:
    if explicit is not None:
        candidates = [explicit, explicit / "cat_vlog_h3"]
    else:
        candidates = []
        for origin in (Path.cwd(), Path(__file__).resolve().parent):
            for parent in (origin, *origin.parents):
                candidates.extend((parent, parent / "cat_vlog_h3"))
        candidates.append(Path("/Users/zhwh/Desktop/sd_workflow/cat_vlog_h3"))
    for candidate in candidates:
        if (candidate / "core.py").is_file() and (candidate / "workflows/01_one_pass_10x7s_h3_cu128.json").is_file():
            return candidate.resolve()
    raise FileNotFoundError("cat_vlog_h3 project not found; supply --project-root with its directory")


def load_core(project: Path):
    spec = importlib.util.spec_from_file_location("cat_vlog_storyboard_core", project / "core.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_and_compose(raw: str, project: Path) -> dict:
    core = load_core(project)
    story = core.validate_story(raw)
    asset_root = (project / "assets").resolve()
    catalog = core.load_reference_catalog(asset_root)
    prompts = []
    cumulative = 0
    for shot in story["shots"]:
        index = shot["id"]
        references = core.resolve_reference_assets(story, index, catalog)
        start = core.compose_start_prompt(story, index)
        start_negative = core.compose_start_negative_prompt(story, index)
        video = core.compose_video_prompt(story, index)
        expected = [
            (start, [shot["start_image_prompt_en"], *shot["must_preserve_en"],
                     shot['states']['start'], shot['background_prompt_en'],
                     *[story["characters"][item["character_id"]]["identity_prompt_en"] for item in shot["cast"]]]),
            (start_negative, [re.sub('human hands', "human hands replacing the cats' paws", fragment, flags=re.I) for fragment in shot["must_avoid_en"]]),
            (video, [shot["camera_mode"], shot["motion_prompt_en"], shot["ambience_prompt_en"],
                     *shot["must_preserve_en"], *[line["text"] for line in shot["audio"]["utterances"]],
                     *[segment['action_en'] for segment in shot['action_segments']],
                     shot["audio"]["diegetic_music_prompt_en"], shot["audio"]["background_music_prompt_en"]]),
        ]
        for rendered, fragments in expected:
            if any(fragment not in rendered for fragment in fragments):
                raise ValueError(f"shot {index}: project prompt composer dropped a storyboard field; inspect the current core")
        prompts.append({"id": index, "cast": shot["cast"],
                        'reference_inputs': references, 'timing': core.resolve_duration(shot['duration_seconds']),
                        'starts_at_seconds': cumulative / 24, 'first_frame_zh': shot['first_frame_zh'],
                        'length_checks': core.prompt_length_report(story, index),
                        "start_prompt": start, "start_negative_prompt": start_negative, "video_prompt": video})
        cumulative += prompts[-1]['timing']['frames']
    return {"status": "valid", "project": str(project), "schema_version": 4, 'model_quality_verified': False,
            'total_frames': cumulative, 'total_seconds': cumulative / 24,
            "shots": prompts, "editorial_review": "required: detailed Chinese/English agreement, hook within actual first 15s, states, clothing and sample quality"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("story", type=Path, help="Reviewed UTF-8 story JSON; read without modifying it")
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--prompts", action="store_true", help="Print the actual positive, negative and video prompts for ten shots")
    parser.add_argument('--review-markdown', type=Path, help='Export a full Chinese storyboard review in execution mode')
    args = parser.parse_args(argv)
    try:
        report = validate_and_compose(args.story.read_text(encoding="utf-8-sig"), find_project(args.project_root))
    except (OSError, ValueError, TypeError, KeyError, ImportError) as error:
        print(f"INVALID: {error}", file=sys.stderr)
        return 1
    if args.prompts:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"VALID: 10 shots; real project validator and prompt composition passed ({report['project']})")
        print("Editorial review remains necessary; this does not run ComfyUI or predict video quality.")
    if args.review_markdown:
        core = load_core(find_project(args.project_root))
        args.review_markdown.parent.mkdir(parents=True, exist_ok=True)
        args.review_markdown.write_text(core.story_review_markdown(core.validate_story(args.story.read_text(encoding='utf-8-sig'))), encoding='utf-8')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
