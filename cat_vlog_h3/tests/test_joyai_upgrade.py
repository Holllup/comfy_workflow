"""The exported first-frame graph must use the approved multi-reference editor."""

import json
from pathlib import Path
import unittest

from cat_vlog_h3 import nodes
from cat_vlog_h3.workflow_builder import build_workflow


class JoyAIUpgradeTests(unittest.TestCase):
    def test_export_uses_full_joyai_multi_reference_editing_for_all_ten_frames(self):
        graph = build_workflow()
        by_id = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}

        def source(node, port_name):
            port = next(port for port in node["inputs"] if port["name"] == port_name)
            return by_id[links[port["link"]][1]]

        types = [node["type"] for node in graph["nodes"]]
        for node in graph["nodes"]:
            names = [port["name"] for port in node.get("inputs", [])]
            self.assertEqual(len(names), len(set(names)), (node["title"], names))
        self.assertEqual(types.count("CatH3JoyEncode"), 20)
        self.assertEqual(types.count("EmptySD3LatentImage"), 10)
        self.assertNotIn("NunchakuQwenImageDiTLoader", types)
        image_model = next(node for node in graph["nodes"] if node["type"] == "UNETLoader" and "JoyAI" in node["title"])
        self.assertEqual(image_model["widgets_values"][0], "joyai_image_edit_plus_bf16.safetensors")
        for encoder in (node for node in graph["nodes"] if node["type"] == "CatH3JoyEncode"):
            self.assertEqual(source(encoder, "clip")["type"], "CLIPLoader")
            self.assertEqual(source(encoder, "vae")["type"], "VAELoader")
            self.assertEqual(source(encoder, "references")["type"], "CatH3SelectReferences")
        for sampler in (node for node in graph["nodes"] if node["type"] == "KSampler"):
            self.assertEqual(sampler["widgets_values"][2:7], [40, 4.0, "euler", "normal", 1])
            latent = source(sampler, "latent_image")
            self.assertEqual(latent["type"], "EmptySD3LatentImage")
            self.assertEqual(latent["widgets_values"], [1344, 768, 1])

    def test_reference_picker_passes_actual_photos_without_gray_canvas(self):
        self.assertEqual(nodes.CatH3SelectReferences.RETURN_NAMES[0], "selected_photos")
        story = Path(__file__).resolve().parents[1] / "storyboards/dance_club_audition_story.json"
        bank = nodes._reference_bank()
        selected = nodes.CatH3SelectReferences().select(story.read_text(), 1, bank)
        first = selected[0][0]["image"]
        requests = __import__("cat_vlog_h3.core", fromlist=["reference_requests"]).reference_requests(
            json.loads(story.read_text()), 1
        )
        photo = Path(bank[requests[0]["asset_id"]]["path"])
        from PIL import Image
        with Image.open(photo) as image:
            self.assertEqual(tuple(first.shape[1:3]), (image.height, image.width))

    def test_image_prompt_treats_photos_as_identity_references(self):
        from cat_vlog_h3 import core
        story = json.loads((Path(__file__).resolve().parents[1] / "storyboards/dance_club_audition_story.json").read_text())
        prompt = core.compose_start_prompt(story, 1)
        self.assertIn("identity reference", prompt)
        self.assertIn("START FRAME", prompt)
        self.assertNotIn("neutral landscape canvas", prompt)

    def test_shot_specific_avoid_rules_go_to_negative_conditioning(self):
        from cat_vlog_h3 import core
        story = json.loads((Path(__file__).resolve().parents[1] / "storyboards/dance_club_audition_story.json").read_text())
        story["shots"][0]["must_avoid_en"].append("glowing purple floor tiles")
        positive = core.compose_start_prompt(story, 1)
        negative = core.compose_start_negative_prompt(story, 1)
        self.assertNotIn("glowing purple floor tiles", positive)
        self.assertIn("glowing purple floor tiles", negative)
        graph = build_workflow()
        negative_encoder = next(node for node in graph["nodes"] if node["title"] == "镜头 01 首帧负向")
        prompt_link = next(port["link"] for port in negative_encoder["inputs"] if port["name"] == "prompt")
        source = next(link for link in graph["links"] if link[0] == prompt_link)
        self.assertEqual(source[2], 5)

    def test_one_cat_shot_has_two_actual_refs_without_inventing_a_second_cat(self):
        from cat_vlog_h3 import core
        story = json.loads((Path(__file__).resolve().parents[1] / "examples/rainy_day_cat_story.json").read_text())
        requests = core.reference_requests(story, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual({item["character_id"] for item in requests}, {"protagonist"})
        prompt = core.compose_start_prompt(story, 1)
        self.assertNotIn("INPUT IMAGE 3", prompt)


if __name__ == "__main__":
    unittest.main()
