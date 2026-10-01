import unittest
import uuid

from cat_vlog.workflow_builder import build_workflow


class WorkflowGraphTests(unittest.TestCase):
    def test_has_a_standard_comfyui_workflow_id(self):
        uuid.UUID(build_workflow()["id"])

    def test_presents_six_labeled_storyboard_rows(self):
        groups = build_workflow()["groups"]
        self.assertEqual(len(groups), 6)
        self.assertEqual([group["title"] for group in groups], [f"分镜 {index:02}" for index in range(1, 7)])

    def test_previews_master_reference_and_each_saved_keyframe(self):
        graph = build_workflow()
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}
        previews = [node for node in nodes.values() if node["type"] == "PreviewImage"]
        self.assertEqual(len(previews), 7)
        source_types = [nodes[links[preview["inputs"][0]["link"]][1]]["type"] for preview in previews]
        self.assertEqual(source_types.count("CatReference"), 1)
        self.assertEqual(source_types.count("CatSaveFrame"), 6)

    def test_contains_six_portrait_keyframes_and_six_five_second_videos(self):
        graph = build_workflow()
        nodes = graph["nodes"]
        self.assertEqual(sum(node["type"] == "CatSaveFrame" for node in nodes), 6)
        self.assertEqual(sum(node["type"] == "CatSaveClip" for node in nodes), 6)
        latents = [node for node in nodes if node["type"] == "Wan22ImageToVideoLatent"]
        self.assertEqual(len(latents), 6)
        self.assertTrue(all(node["widgets_values"][:3] == [704, 1280, 121] for node in latents))

    def test_shares_heavy_image_and_video_model_loaders(self):
        types = [node["type"] for node in build_workflow()["nodes"]]
        self.assertEqual(types.count("NunchakuQwenImageDiTLoader"), 1)
        self.assertEqual(types.count("UNETLoader"), 2)  # Z-Image and Wan 5B

    def test_uses_the_quantized_qwen_model_preinstalled_on_autodl_v22(self):
        loader = next(node for node in build_workflow()["nodes"] if node["type"] == "NunchakuQwenImageDiTLoader")
        self.assertEqual(
            loader["widgets_values"][0],
            "svdq-int4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors",
        )

    def test_images_and_videos_have_explicit_serial_dependencies(self):
        graph = build_workflow()
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}
        image_gates = sorted(
            (node for node in nodes.values() if node["type"] == "CatImageGate"),
            key=lambda node: node["widgets_values"][0],
        )
        video_gates = sorted(
            (node for node in nodes.values() if node["type"] == "CatVideoGate"),
            key=lambda node: node["widgets_values"][0],
        )
        frames = sorted(
            (node for node in nodes.values() if node["type"] == "CatSaveFrame"),
            key=lambda node: node["widgets_values"][0],
        )
        clips = sorted(
            (node for node in nodes.values() if node["type"] == "CatSaveClip"),
            key=lambda node: node["widgets_values"][0],
        )
        self.assertEqual(len(image_gates), 6)
        self.assertEqual(len(video_gates), 6)
        for index in range(1, 6):
            prior_image = next(i for i in image_gates[index]["inputs"] if i["name"] == "prior")
            prior_video = next(i for i in video_gates[index]["inputs"] if i["name"] == "prior")
            self.assertEqual(links[prior_image["link"]][1], frames[index - 1]["id"])
            self.assertEqual(links[prior_video["link"]][1], clips[index - 1]["id"])
        first_video_prior = next(i for i in video_gates[0]["inputs"] if i["name"] == "prior")
        self.assertEqual(links[first_video_prior["link"]][1], frames[5]["id"])


if __name__ == "__main__":
    unittest.main()
