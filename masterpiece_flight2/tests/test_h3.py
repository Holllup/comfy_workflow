import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from test_core import story


class H3CoreTests(unittest.TestCase):
    def test_spatial_style_seed_preserves_palette_without_source_layout(self):
        from masterpiece_flight2 import core

        producer = getattr(core, "spatial_style_seed", None)
        self.assertIsNotNone(producer)
        painting = np.zeros((80, 80, 3), np.uint8)
        painting[:, :40] = (240, 20, 20)
        painting[:, 40:] = (20, 20, 240)
        seed = producer(painting, 1344, 768)
        self.assertEqual(seed.shape, (768, 1344, 3))
        left_red = float(seed[:, :672, 0].mean())
        right_red = float(seed[:, 672:, 0].mean())
        self.assertLess(abs(left_red - right_red), 70)
        self.assertGreater(float(seed[..., 0].mean()), 70)
        self.assertGreater(float(seed[..., 2].mean()), 70)

    def test_v2_prompts_explain_two_inputs_and_timed_camera_target(self):
        from masterpiece_flight2 import core

        frame = {"image_prompt_en": "Painted village street.", "camera_position": "above the lane", "camera_direction": "toward church", "camera_path_from_next_frame": "move backward from steeple", "shared_landmarks": ["church", "hill"], "transition_object": "blue hill", "transition_object_screen_position": "right 45%", "entry_state": "low street", "exit_state": "hill close", "end_frame_constraints": ["hill fills frame"], "must_preserve": ["blue palette"], "must_not_generate": ["modern cars"]}
        image_text = core.compose_image_prompt(frame, 2)
        self.assertIn("INPUT IMAGE 1", image_text)
        self.assertIn("INPUT IMAGE 2", image_text)
        self.assertIn("right 45%", image_text)
        self.assertIn("modern cars", image_text)
        shot = {"motion_prompt_en": "A painted drone flight.", "start_state": "street", "camera_path": "rise to roofs", "speed_profile": "fast then slow", "parallax": "near walls move faster", "environment_motion": "warm lights flicker", "transition_approach": "hill covers view", "final_quarter_target_state": "blue hill close"}
        motion_text = core.compose_motion_prompt(shot)
        self.assertIn("START STATE", motion_text)
        self.assertIn("FINAL 25% TARGET STATE", motion_text)
        self.assertIn("hill covers view", motion_text)

    def test_spatial_prompt_names_style_seed_and_unconnected_second_image(self):
        import inspect
        from masterpiece_flight2 import core

        frame = {
            "image_prompt_en": "Build a traversable painted village, not a flat picture.",
            "camera_position": "beside the hill",
            "camera_direction": "toward the church",
            "camera_path_from_next_frame": "pull back from the near view",
            "shared_landmarks": ["church", "cypress"],
            "transition_object": "hill shoulder",
            "transition_object_screen_position": "right half",
            "entry_state": "near the hill",
            "exit_state": "above the village",
            "end_frame_constraints": ["continuous landscape"],
            "must_preserve": ["cobalt palette"],
            "must_not_generate": ["flat backdrop"],
        }
        self.assertIn("spatial_mode", inspect.signature(core.compose_image_prompt).parameters)
        prompt = core.compose_image_prompt(frame, 4, spatial_mode=True)
        self.assertIn("INPUT IMAGE 1: abstract", prompt)
        self.assertIn("INPUT IMAGE 2: not connected", prompt)
        self.assertNotIn("INPUT IMAGE 1: the canonical original painting", prompt)
        self.assertIn("parallax", prompt.lower())

    def test_h3_project_preserves_one_native_canvas_through_saved_keyframes(self):
        from masterpiece_flight2 import core

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = core.init_project(root, "h3", json.dumps(story()), np.zeros((4, 3, 3), np.uint8), canvas_size=(1344, 768))
            self.assertEqual(project["ending"].shape, (768, 1344, 3))
            frame = np.full((768, 1344, 3), 70, np.uint8)
            for index in range(1, 5):
                core.save_keyframe(root, "h3", index, frame)
            self.assertEqual(core.load_project(root, "h3")["frames"][0].shape, (768, 1344, 3))

    def test_story_v2_requires_camera_and_transition_contracts(self):
        from masterpiece_flight2 import core

        plan = story()
        plan["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "camera_position"):
            core.validate_story(json.dumps(plan))

    def test_generic_transition_names_are_accepted_for_other_paintings(self):
        from masterpiece_flight2 import core

        source = Path(__file__).resolve().parents[1] / "examples" / "starry_night_story.json"
        plan = json.loads(source.read_text(encoding="utf-8"))
        plan["shots"][0]["transition_type"] = "generic_occlusion"
        plan["shots"][1]["transition_type"] = "landmark_match"
        plan["shots"][2]["transition_type"] = "radial_light"
        self.assertEqual(core.validate_story(json.dumps(plan))["shots"][0]["transition_type"], "generic_occlusion")

    def test_h3_bridge_keeps_native_shape_and_exact_endpoints(self):
        from masterpiece_flight2 import core

        generated = np.full((8, 4, 8, 3), 0.25, np.float32)
        start = np.full((4, 8, 3), 30, np.uint8)
        end = np.full((4, 8, 3), 210, np.uint8)
        result = core.bridge_h3_frames(generated, start, end, blend_frames=4)
        self.assertEqual(result.shape, (8, 4, 8, 3))
        np.testing.assert_array_equal(result[0], start)
        np.testing.assert_array_equal(result[-1], end)
        self.assertTrue(np.all(result[-2] > result[-3]))

    def test_delivery_canvas_pads_from_each_moving_frame_instead_of_original(self):
        from masterpiece_flight2 import core

        frames = np.full((2, 768, 1344, 3), 90, np.uint8)
        frames[1] = 120
        original = np.full((768, 1344, 3), 20, np.uint8)
        result = core.delivery_canvas(frames, original)
        self.assertEqual(result.shape, (2, 720, 1280, 3))
        self.assertEqual(int(result[0, 100, 0, 0]), 90)
        self.assertEqual(int(result[1, 100, 0, 0]), 120)
        self.assertEqual(int(result[0, 100, 10, 0]), 90)


class H3WorkflowTests(unittest.TestCase):
    def test_spatial_variant_keeps_original_out_of_early_qwen_image_inputs(self):
        from masterpiece_flight2.workflow_builder import build_one_pass_h3

        try:
            graph = build_one_pass_h3(runtime="cu128", spatial_mode=True)
        except TypeError as exc:
            self.fail(f"Spatial workflow variant is unavailable: {exc}")
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}
        edits = [node for node in nodes.values() if node["type"] == "TextEncodeQwenImageEditPlus"]
        self.assertEqual(len(edits), 8)
        for edit in edits:
            image2 = next(item for item in edit["inputs"] if item["name"] == "image2")
            self.assertIsNone(image2["link"], edit["title"])
        negatives = [node for node in edits if "反向提示词" in node["title"]]
        self.assertEqual(len(negatives), 4)
        self.assertTrue(all("flat painting" in node["widgets_values"][0].lower() and "canvas border" in node["widgets_values"][0].lower() for node in negatives))
        first_edit = next(node for node in edits if "关键帧 04 正向" in node["title"])
        image1 = next(item for item in first_edit["inputs"] if item["name"] == "image1")
        self.assertEqual(nodes[links[image1["link"]][1]]["type"], "ArtSpatialStyleSeed")
        frame_texts = [node for node in nodes.values() if node["type"] == "ArtFrameText"]
        self.assertEqual(len(frame_texts), 4)
        self.assertTrue(all(len(node["widgets_values"]) >= 3 for node in frame_texts))
        self.assertTrue(all(node["widgets_values"][2] is True for node in frame_texts))
        h3 = sorted((node for node in nodes.values() if node["type"] == "MiniMaxH3ImageToVideo"), key=lambda node: node["pos"][1])
        self.assertEqual(len(h3), 4)
        final_end = next(item for item in h3[3]["inputs"] if item["name"] == "last_frame")
        self.assertEqual(nodes[links[final_end["link"]][1]]["type"], "ArtH3Stage")
        self.assertEqual(links[final_end["link"]][2], 4)
        bridges = [node for node in nodes.values() if node["type"] == "ArtH3Bridge"]
        self.assertEqual([node["widgets_values"][1] for node in bridges], [2, 2, 2, 2])
        self.assertEqual(sum(node["type"] == "SaveVideo" for node in nodes.values()), 5)

    def test_cu128_variant_uses_fp8_video_model_without_torch_upgrade(self):
        from masterpiece_flight2.workflow_builder import build_one_pass_h3

        graph = build_one_pass_h3(runtime="cu128")
        model = next(node for node in graph["nodes"] if node["type"] == "UNETLoader")
        vaes = [node for node in graph["nodes"] if node["type"] == "VAELoader"]
        self.assertEqual(model["widgets_values"][0], "minimax_h3_fl2va_pruned_fp8_scaled.safetensors")
        self.assertTrue(any(node["widgets_values"][0] == "minimax_h3_video_vae_fp16.safetensors" for node in vaes))
        self.assertEqual(sum(node["type"] == "MiniMaxH3ImageToVideo" for node in graph["nodes"]), 4)
        self.assertEqual(sum(node["type"] == "ArtSpatialStyleSeed" for node in graph["nodes"]), 1)
        edits = [node for node in graph["nodes"] if node["type"] == "TextEncodeQwenImageEditPlus"]
        self.assertTrue(all(next(i for i in node["inputs"] if i["name"] == "image2")["link"] is None for node in edits))

    def test_spatial_frame_text_rejects_legacy_story_before_generating(self):
        import inspect
        from masterpiece_flight2.nodes import ArtFrameText

        self.assertIn("spatial_mode", inspect.signature(ArtFrameText.run).parameters)
        with self.assertRaisesRegex(ValueError, "conditioning_mode"):
            ArtFrameText().run(json.dumps(story()), 4, 487201, True)

    def test_h3_pilot_runs_one_shot_after_keyframes(self):
        from masterpiece_flight2.workflow_builder import build_one_pass_h3

        graph = build_one_pass_h3(pilot=True)
        self.assertEqual(sum(node["type"] == "MiniMaxH3ImageToVideo" for node in graph["nodes"]), 1)
        self.assertEqual(sum(node["type"] == "SaveVideo" for node in graph["nodes"]), 1)
        self.assertEqual(sum(node["type"] == "ArtSaveKeyframe" for node in graph["nodes"]), 4)

    def test_one_pass_h3_has_native_first_last_frame_chain_and_five_videos(self):
        from masterpiece_flight2.workflow_builder import build_one_pass_h3

        graph = build_one_pass_h3()
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}

        def parent(node, slot):
            return nodes[links[node["inputs"][slot]["link"]][1]]

        h3 = sorted((node for node in nodes.values() if node["type"] == "MiniMaxH3ImageToVideo"), key=lambda n: n["pos"][1])
        self.assertEqual(len(h3), 4)
        self.assertEqual(sum(n["type"] == "UNETLoader" for n in nodes.values()), 1)
        qwen = next(n for n in nodes.values() if n["type"] == "NunchakuQwenImageDiTLoader")
        self.assertEqual(qwen["widgets_values"][0], "svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors")
        self.assertEqual(sum(n["type"] == "SamplerCustomAdvanced" for n in nodes.values()), 4)
        self.assertEqual(sum(n["type"] == "SaveVideo" for n in nodes.values()), 5)
        self.assertTrue(all(n["widgets_values"] == [24, 8] for n in nodes.values() if n["type"] == "CreateVideo"))
        self.assertTrue(all(n["widgets_values"][-3:] == [1344, 768, 124] for n in h3))
        self.assertEqual(parent(h3[0], 2)["type"], "ArtH3Stage")
        self.assertEqual(parent(h3[0], 3)["type"], "ArtH3Stage")
        for index in range(1, 4):
            self.assertEqual(parent(h3[index], 2)["type"], "ArtLastFrame")
        self.assertEqual(parent(h3[3], 3)["type"], "ArtH3Stage")
        self.assertEqual(sum(n["type"] == "ArtH3Audit" for n in nodes.values()), 4)
        self.assertEqual(sum(n["type"] == "ArtH3Bridge" for n in nodes.values()), 4)
        self.assertEqual(parent(next(n for n in nodes.values() if n["type"] == "ArtDeliveryCanvas"), 0)["type"], "ArtJoinFrames")


class H3NodeTests(unittest.TestCase):
    def test_h3_prepare_uses_native_canvas_and_audit_saves_raw_tail_before_bridge(self):
        import os
        from masterpiece_flight2 import nodes

        with tempfile.TemporaryDirectory() as temp:
            previous = os.environ.get("ART_PROJECT_ROOT")
            os.environ["ART_PROJECT_ROOT"] = temp
            try:
                painting = np.zeros((1, 3, 4, 3), np.float32)
                canvas, _, project_id = nodes.ArtPrepare().run(painting, "starry", json.dumps(story()), "h3_1344x768")
                self.assertEqual(tuple(canvas.shape), (1, 768, 1344, 3))
                raw = np.full((1, 4, 8, 3), 0.2, np.float32)
                target = np.full((1, 4, 8, 3), 0.8, np.float32)
                audited = nodes.ArtH3Audit().run(raw, target, project_id, 1)[0]
                self.assertEqual(tuple(audited.shape), (1, 4, 8, 3))
                directory = Path(temp) / project_id / "diagnostics"
                self.assertTrue((directory / "shot_01_raw_last.png").exists())
                score = json.loads((directory / "shot_01_gap.json").read_text())
                self.assertGreater(score["mean_absolute_difference"], 0.5)
            finally:
                if previous is None:
                    os.environ.pop("ART_PROJECT_ROOT", None)
                else:
                    os.environ["ART_PROJECT_ROOT"] = previous


if __name__ == "__main__":
    unittest.main()
