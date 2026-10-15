"""Build a model-free AutoDL bundle with current cat H3 UI workflows."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

if __package__:
    from .workflow_builder import write_workflows
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from cat_vlog_h3.workflow_builder import write_workflows


ROOT = Path(__file__).resolve().parent


def build_bundle(destination: Path) -> Path:
    story = (ROOT / "storyboards" / "dance_club_audition_story.json").read_text(encoding="utf-8")
    write_workflows(ROOT / "workflows", story)
    paths = [ROOT / name for name in (
        "__init__.py", "core.py", "nodes.py", "workflow_builder.py", "build_package.py",
        "requirements.txt", "README.md", "AGENTS.md", "PROMPT_ChatGPT_十镜编剧.md",
    )]
    for pattern in ("scripts/*.py", "examples/*.json", "references/*.json", "references/*.md", "workflows/*.json", "storyboards/*.json", "storyboards/*.md",
                    "migration_reports/*.json", "acceptance/*.md", "acceptance/*.json", "assets/**/*.png", "assets/*.json"):
        paths.extend(sorted(ROOT.glob(pattern)))
    for pattern in ("skills/**/*.md", "skills/**/*.py", "skills/**/*.yaml"):
        paths.extend(sorted(ROOT.glob(pattern)))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            if not path.is_file():
                raise FileNotFoundError(path)
            archive.write(path, arcname=str(Path("cat_vlog_h3") / path.relative_to(ROOT)))
    return destination


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "cat_vlog_h3_bundle.zip"
    print(build_bundle(output))
