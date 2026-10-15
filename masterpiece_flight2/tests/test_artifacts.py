import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from masterpiece_flight2.core import validate_story
from masterpiece_flight2.workflow_builder import write_workflows


ROOT = Path(__file__).resolve().parents[1]


class ArtifactTests(unittest.TestCase):
    def test_starry_night_example_is_valid_and_preserves_historical_caveat(self):
        path = ROOT / "examples" / "starry_night_story.json"
        self.assertTrue(path.exists(), "The pilot storyboard is missing")
        plan = validate_story(path.read_text(encoding="utf-8"))
        self.assertEqual(plan["artwork"]["title"], "The Starry Night")
        self.assertTrue(any("village" in item.lower() and "window" in item.lower() for item in plan["verified_context"]))
        self.assertTrue(any("village" in item.lower() for item in plan["imagined_context"]))

    def test_generated_workflows_include_reviewed_pilot_story(self):
        source = ROOT / "examples" / "starry_night_story.json"
        self.assertTrue(source.exists(), "The pilot storyboard is missing")
        story = source.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as temp:
            write_workflows(Path(temp), story)
            files = sorted(path.name for path in Path(temp).glob("*.json"))
            self.assertEqual(files, ["00_one_pass_minimax_h3.json", "00_one_pass_minimax_h3_cu128.json", "00_one_pass_minimax_h3_spatial_cu128.json", "00_one_pass_wan5b.json", "00_pilot_minimax_h3.json", "00_pilot_minimax_h3_cu128.json", "00_pilot_minimax_h3_spatial_cu128.json", "01_keyframes.json", "01_keyframes_nunchaku.json", "02_pilot_5s.json", "02_pilot_wan5b.json", "03_full_20s.json", "03_full_wan5b.json"])
            first = json.loads((Path(temp) / "01_keyframes.json").read_text(encoding="utf-8"))
            prepare = next(node for node in first["nodes"] if node["type"] == "ArtPrepare")
            self.assertEqual(json.loads(prepare["widgets_values"][1])["artwork"]["title"], "The Starry Night")
            one_pass = json.loads((Path(temp) / "00_one_pass_wan5b.json").read_text(encoding="utf-8"))
            prepare = next(node for node in one_pass["nodes"] if node["type"] == "ArtPrepare")
            self.assertEqual(prepare["widgets_values"][1], "")

    def test_bundle_contains_runtime_and_docs_but_no_model_weights(self):
        try:
            from masterpiece_flight2.build_package import build_bundle
        except ImportError as exc:
            self.fail(f"bundle builder missing: {exc}")
        with tempfile.TemporaryDirectory() as temp:
            bundle = build_bundle(Path(temp) / "bundle.zip")
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
            self.assertIn("masterpiece_flight2/__init__.py", names)
            self.assertIn("masterpiece_flight2/nodes.py", names)
            self.assertIn("masterpiece_flight2/references/ltx25_flf2v_subgraph.json", names)
            self.assertIn("masterpiece_flight2/workflows/03_full_20s.json", names)
            self.assertIn("masterpiece_flight2/workflows/01_keyframes_nunchaku.json", names)
            self.assertIn("masterpiece_flight2/workflows/03_full_wan5b.json", names)
            self.assertIn("masterpiece_flight2/workflows/00_one_pass_wan5b.json", names)
            self.assertIn("masterpiece_flight2/workflows/00_one_pass_minimax_h3.json", names)
            self.assertIn("masterpiece_flight2/workflows/00_one_pass_minimax_h3_spatial_cu128.json", names)
            self.assertIn("masterpiece_flight2/examples/starry_night_story_spatial.json", names)
            self.assertIn("masterpiece_flight2/PROMPT_ChatGPT编剧_空间版.md", names)
            self.assertIn("masterpiece_flight2/README_H3_新实例.md", names)
            self.assertIn("masterpiece_flight2/scripts/download_h3_models.py", names)
            self.assertIn("masterpiece_flight2/README_安装.md", names)
            self.assertFalse(any(name.endswith(".safetensors") for name in names))

    def test_shipped_cu128_graph_does_not_feed_complete_painting_to_qwen(self):
        graph = json.loads((ROOT / "workflows" / "00_one_pass_minimax_h3_cu128.json").read_text(encoding="utf-8"))
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}
        seed = [node for node in nodes.values() if node["type"] == "ArtSpatialStyleSeed"]
        self.assertEqual(len(seed), 1)
        edits = [node for node in nodes.values() if node["type"] == "TextEncodeQwenImageEditPlus"]
        self.assertEqual(len(edits), 8)
        self.assertTrue(all(next(item for item in node["inputs"] if item["name"] == "image2")["link"] is None for node in edits))
        first = next(node for node in edits if "关键帧 04 正向" in node["title"])
        link_id = next(item for item in first["inputs"] if item["name"] == "image1")["link"]
        self.assertEqual(nodes[links[link_id][1]]["type"], "ArtSpatialStyleSeed")

    def test_h3_example_defines_four_specific_transition_interfaces(self):
        plan = validate_story((ROOT / "examples" / "starry_night_story.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["schema_version"], 2)
        self.assertEqual([shot["transition_type"] for shot in plan["shots"]], [
            "hill_occlusion", "steeple_match", "radial_star_halo", "final_artwork_alignment",
        ])
        self.assertIn("35%", plan["keyframes"][1]["transition_object_screen_position"])

    def test_spatial_starry_night_example_has_v2_camera_and_transition_contracts(self):
        path = ROOT / "examples" / "starry_night_story_spatial.json"
        plan = validate_story(path.read_text(encoding="utf-8"))
        self.assertEqual(plan.get("schema_version"), 2)
        self.assertEqual([shot.get("transition_type") for shot in plan["shots"]], [
            "hill_occlusion", "steeple_match", "radial_star_halo", "final_artwork_alignment",
        ])
        self.assertIn("35", plan["keyframes"][1]["transition_object_screen_position"])
        self.assertIn("25", plan["keyframes"][3]["transition_object_screen_position"])

    def test_spatial_starry_night_example_declares_palette_only_conditioning(self):
        path = ROOT / "examples" / "starry_night_story_spatial.json"
        plan = validate_story(path.read_text(encoding="utf-8"))
        self.assertEqual(plan.get("conditioning_mode"), "spatial_style_seed")
        self.assertIn("abstract", plan["keyframes"][3]["image_prompt_en"].lower())
        for frame in plan["keyframes"][:3]:
            self.assertIn("no second image", frame["image_prompt_en"].lower())
            forbidden = " ".join(frame["must_not_generate"]).lower()
            self.assertIn("flat", forbidden)
            self.assertIn("canvas", forbidden)

    def test_generated_workflows_have_no_unrelated_example_prompts(self):
        with tempfile.TemporaryDirectory() as temp:
            write_workflows(Path(temp))
            for path in Path(temp).glob("*.json"):
                text = path.read_text(encoding="utf-8").lower()
                for sample in ("man on the sofa", "puppy", "1970s-style subway"):
                    self.assertFalse(sample in text, f"{path.name} still contains {sample}")


if __name__ == "__main__":
    unittest.main()
