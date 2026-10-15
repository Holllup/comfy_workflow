"""Resolve requested shot durations before writing action segments; no files or models are changed."""
import argparse
import json
from pathlib import Path

from validate_story import find_project, load_core


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('seconds', nargs='+', type=float)
    parser.add_argument('--project-root', type=Path)
    args = parser.parse_args()
    core = load_core(find_project(args.project_root))
    result = [core.resolve_duration(value) for value in args.seconds]
    print(json.dumps({'shots': result, 'total_seconds': sum(item['frames'] for item in result) / 24}, indent=2))


if __name__ == '__main__':
    main()
