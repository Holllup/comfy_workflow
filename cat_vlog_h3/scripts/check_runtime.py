"""Check a running ComfyUI's node definitions against the shipped UI graphs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]


def graph_errors(graph: dict, object_info: dict) -> list[str]:
    errors = []
    if any(node['type'] == 'CatH3JoyEncode' for node in graph['nodes']) and 'TextEncodeJoyImageEdit' not in object_info:
        errors.append('missing native JoyAI backend: TextEncodeJoyImageEdit; custom wrapper alone is insufficient')
    for node in graph["nodes"]:
        kind = node["type"]
        definition = object_info.get(kind)
        if definition is None:
            errors.append(f"missing node: {kind}")
            continue
        accepted = {}
        for group in ("required", "optional", "hidden"):
            accepted.update(definition.get("input", {}).get(group, {}))
        for port in node.get("inputs", []):
            name = port["name"]
            if name not in accepted:
                if not (kind == "TextEncodeJoyImageEdit" and "images" in accepted
                        and re.fullmatch(r"images\.image[0-5]", name) and port["type"] == "IMAGE"):
                    errors.append(f"{kind}: missing input {name}")
            else:
                declared = accepted[name]
                actual = declared[0] if isinstance(declared, (list, tuple)) and declared else declared
                if isinstance(actual, str) and actual != port["type"]:
                    errors.append(f"{kind}.{name}: input type {actual} != {port['type']}")
        output_types = definition.get("output", [])
        for slot, port in enumerate(node.get("outputs", [])):
            if slot >= len(output_types) or output_types[slot] != port["type"]:
                actual = output_types[slot] if slot < len(output_types) else "absent"
                errors.append(f"{kind}: output {slot} type {actual} != {port['type']}")
    return sorted(set(errors))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:6006")
    parser.add_argument("--workflow", type=Path, action="append")
    args = parser.parse_args(argv)
    files = args.workflow or [
        ROOT / "workflows/01_one_pass_10x7s_h3_cu128.json",
    ]
    with urlopen(args.url.rstrip("/") + "/object_info", timeout=15) as response:
        object_info = json.load(response)
    for path in files:
        graph = json.loads(path.read_text(encoding="utf-8"))
        errors = graph_errors(graph, object_info)
        if errors:
            print(f"INCOMPATIBLE  {path}")
            for error in errors[:30]:
                print(f"  {error}")
            return 1
        print(f"OK  {path}  {len(graph['nodes'])} nodes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
