"""Explicit v3 migration; keep the complete source in a separate review report."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from cat_vlog_h3.core import migrate_v3_story


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error('Choose a new output file; migration does not overwrite the original or an existing draft')
    story, report = migrate_v3_story(json.loads(args.source.read_text(encoding='utf-8-sig')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(story, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    report_path = args.output.with_suffix('.migration_review.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'DRAFT v4: {args.output}\nREVIEW REQUIRED: {report_path}')


if __name__ == '__main__':
    main()
