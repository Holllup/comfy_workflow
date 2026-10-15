"""Generate current workflow JSON files and a model-free AutoDL bundle."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

if __package__:
    from .workflow_builder import write_workflows
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from masterpiece_flight2.workflow_builder import write_workflows


ROOT = Path(__file__).resolve().parent


def build_bundle(destination: Path) -> Path:
    from masterpiece_flight2.realism_workflows import write_stages
    story = (ROOT / "examples" / "starry_night_story.json").read_text(encoding="utf-8")
    write_workflows(ROOT / "workflows", story)
    write_stages(ROOT / "workflows" / "flux_h3_v3")
    paths = [ROOT / name for name in (
        "__init__.py", "core.py", "nodes.py", "workflow_builder.py", "build_package.py",
        "requirements.txt", "README.md", "README_安装.md", "README_H3_新实例.md", "PROMPT_ChatGPT编剧.md", "PROMPT_ChatGPT编剧_空间版.md",
        "realism.py", "realism_nodes.py", "realism_workflows.py", "README_FLUX_H3.md",
    )]
    paths += sorted((ROOT / "scripts").glob("*.py"))
    paths += sorted((ROOT / "examples").glob("*.json"))
    paths += sorted((ROOT / "references").glob("*.json"))
    paths += sorted((ROOT / "workflows").rglob("*.json"))
    paths += sorted((ROOT / "skills").rglob("*.md"))
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in paths:
            archive.write(path, arcname=str(Path("masterpiece_flight2") / path.relative_to(ROOT)))
    return destination


if __name__ == "__main__":
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "masterpiece_flight2_bundle.zip"
    print(build_bundle(output))
