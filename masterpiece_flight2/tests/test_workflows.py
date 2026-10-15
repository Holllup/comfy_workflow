import unittest


QWEN = "eba40a3a-f6c5-48ac-b58e-55525d06b373"
LTX = "cf70afc4-5a03-47ce-8210-734b1de6c6bc"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        try:
            from masterpiece_flight2.workflow_builder import build_keyframes, build_keyframes_nunchaku, build_video, build_video_wan, build_one_pass_wan
        except ImportError as exc:
            self.fail(f"workflow builder is missing: {exc}")
        self.build_keyframes = build_keyframes
        self.build_keyframes_nunchaku = build_keyframes_nunchaku
        self.build_video = build_video
        self.build_video_wan = build_video_wan
        self.build_one_pass_wan = build_one_pass_wan

    def graph(self, data):
        nodes = {node["id"]: node for node in data["nodes"]}
        links = {link[0]: link for link in data["links"]}
        for link_id, source, source_slot, target, target_slot, kind in data["links"]:
            self.assertEqual(nodes[source]["outputs"][source_slot]["type"], kind)
            self.assertIn(kind, nodes[target]["inputs"][target_slot]["type"].split(","))
            self.assertEqual(nodes[target]["inputs"][target_slot]["link"], link_id)
        def parent(node, input_slot):
            return nodes[links[node["inputs"][input_slot]["link"]][1]]
        return nodes, parent

    def test_keyframes_generate_backward_from_original_then_save_forward_indices(self):
        data = self.build_keyframes()
        nodes, parent = self.graph(data)
        self.assertIn(QWEN, {item["id"] for item in data["definitions"]["subgraphs"]})
        edits = [n for n in nodes.values() if n["type"] == QWEN]
        self.assertEqual(len(edits), 4)
        by_index = {n["widgets_values"][0]: n for n in nodes.values() if n["type"] == "ArtSaveKeyframe"}
        self.assertEqual(sorted(by_index), [1, 2, 3, 4])
        self.assertEqual(parent(by_index[4], 0)["type"], QWEN)
        self.assertEqual(parent(parent(by_index[4], 0), 0)["type"], "ArtPrepare")
        for i in (1, 2, 3):
            edit = parent(by_index[i], 0)
            self.assertEqual(parent(edit, 0)["id"], by_index[i + 1]["id"])
            self.assertEqual(parent(edit, 1)["type"], "ArtPrepare")

    def test_full_video_uses_approved_frames_and_exact_original_at_end(self):
        data = self.build_video()
        nodes, parent = self.graph(data)
        self.assertIn(LTX, {item["id"] for item in data["definitions"]["subgraphs"]})
        clips = sorted((n for n in nodes.values() if n["type"] == LTX), key=lambda n: n["pos"][1])
        self.assertEqual(len(clips), 4)
        load = next(n for n in nodes.values() if n["type"] == "ArtLoadApproved")
        for i, clip in enumerate(clips):
            self.assertEqual(clip["widgets_values"][2:5], [5, 1280, 720])
            self.assertEqual(parent(clip, 0)["id"], load["id"])
            self.assertEqual(parent(clip, 1)["id"], load["id"])
            self.assertEqual(parent(clip, 2)["type"], "ArtMotionText")
            if i:
                self.assertEqual(parent(parent(clip, 2), 1)["type"], "SaveVideo")
        hold = next(n for n in nodes.values() if n["type"] == "ArtHoldFrames")
        self.assertEqual(parent(hold, 0)["id"], load["id"])
        join = next(n for n in nodes.values() if n["type"] == "ConcatenateVideo")
        self.assertEqual(len(join["inputs"]), 5)
        self.assertTrue(all(parent(join, i)["type"] == "SaveVideo" for i in range(4)))
        self.assertEqual(parent(join, 4)["type"], "CreateVideo")
        self.assertTrue(all(parent(n, 0)["type"] == "GetVideoComponents" for n in nodes.values() if n["type"] == "CreateVideo" and n["title"].startswith("无声镜头")))
        final = next(n for n in nodes.values() if n["type"] == "SaveVideo" and n["title"].startswith("最终"))
        self.assertEqual(parent(final, 0)["id"], join["id"])

    def test_nunchaku_keyframes_use_existing_quantized_model_without_fp8_download(self):
        data = self.build_keyframes_nunchaku(model_name="already-installed.safetensors")
        nodes, parent = self.graph(data)
        loaders = [n for n in nodes.values() if n["type"] == "NunchakuQwenImageDiTLoader"]
        self.assertEqual(len(loaders), 1)
        self.assertEqual(loaders[0]["widgets_values"][0], "already-installed.safetensors")
        self.assertFalse(any(n["type"] == "UNETLoader" for n in nodes.values()))
        self.assertEqual(sum(n["type"] == "KSampler" for n in nodes.values()), 4)
        by_index = {n["widgets_values"][0]: n for n in nodes.values() if n["type"] == "ArtSaveKeyframe"}
        self.assertEqual(sorted(by_index), [1, 2, 3, 4])
        for i in (1, 2, 3, 4):
            edit = parent(by_index[i], 0)
            self.assertEqual(edit["type"], "VAEDecode")
            sampler = parent(edit, 0)
            self.assertEqual(sampler["type"], "KSampler")
            source = parent(parent(sampler, 3), 0)
            self.assertEqual(source["id"], by_index[i + 1]["id"] if i < 4 else next(n["id"] for n in nodes.values() if n["type"] == "ArtPrepare"))

    def test_pilot_renders_only_final_approach_and_hold(self):
        data = self.build_video(pilot=True)
        nodes, parent = self.graph(data)
        clips = [n for n in nodes.values() if n["type"] == LTX]
        self.assertEqual(len(clips), 1)
        self.assertEqual(parent(clips[0], 1)["type"], "ArtLoadApproved")
        join = next(n for n in nodes.values() if n["type"] == "ConcatenateVideo")
        self.assertEqual(len(join["inputs"]), 2)

    def test_wan_uses_installed_5b_and_bridges_each_clip_to_approved_target(self):
        data = self.build_video_wan()
        nodes, parent = self.graph(data)
        self.assertFalse(any(n["type"] == LTX for n in nodes.values()))
        models = [n for n in nodes.values() if n["type"] == "UNETLoader"]
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["widgets_values"][0], "wan2.2_ti2v_5B_fp16.safetensors")
        latents = sorted((n for n in nodes.values() if n["type"] == "Wan22ImageToVideoLatent"), key=lambda n: n["pos"][1])
        self.assertEqual(len(latents), 4)
        self.assertTrue(all(n["widgets_values"][:3] == [1280, 704, 121] for n in latents))
        bridges = sorted((n for n in nodes.values() if n["type"] == "ArtBridgeFrames"), key=lambda n: n["pos"][1])
        self.assertEqual(len(bridges), 4)
        load = next(n for n in nodes.values() if n["type"] == "ArtLoadApproved")
        for i, bridge in enumerate(bridges):
            self.assertEqual(parent(bridge, 0)["type"], "VAEDecode")
            self.assertEqual(parent(bridge, 1)["id"], load["id"])
            self.assertEqual(parent(bridge, 2)["id"], load["id"])
        links = {link[0]: link for link in data["links"]}
        self.assertEqual([links[bridge["inputs"][2]["link"]][2] for bridge in bridges], [1, 2, 3, 4])
        self.assertFalse(any(n["type"] == "ConcatenateVideo" for n in nodes.values()))
        join = next(n for n in nodes.values() if n["type"] == "ArtJoinFrames")
        self.assertEqual(len(join["inputs"]), 5)
        self.assertEqual([parent(join, i)["type"] for i in (0, 2, 3, 4)], ["ArtBridgeFrames"] * 4)
        self.assertEqual(parent(join, 1)["type"], "ArtHoldFrames")
        motions = sorted((n for n in nodes.values() if n["type"] == "ArtMotionText"), key=lambda n: n["pos"][1])
        self.assertTrue(all(parent(motions[i], 1)["id"] == bridges[i - 1]["id"] for i in range(1, 4)))
        saves = [n for n in nodes.values() if n["type"] == "SaveVideo"]
        self.assertEqual(len(saves), 5)
        self.assertTrue(all(n["widgets_values"][1:] == ["auto", "auto"] and not n["outputs"] for n in saves))

    def test_wan_pilot_only_generates_last_approach(self):
        data = self.build_video_wan(pilot=True)
        nodes, parent = self.graph(data)
        self.assertEqual(sum(n["type"] == "Wan22ImageToVideoLatent" for n in nodes.values()), 1)
        bridge = next(n for n in nodes.values() if n["type"] == "ArtBridgeFrames")
        self.assertEqual(parent(bridge, 2)["type"], "ArtLoadApproved")
        self.assertEqual(sum(n["type"] == "ArtJoinFrames" for n in nodes.values()), 1)

    def test_one_pass_uses_each_generated_anchor_then_actual_video_tail(self):
        data = self.build_one_pass_wan()
        nodes, parent = self.graph(data)
        self.assertFalse(any(n["type"] == "ArtLoadApproved" for n in nodes.values()))
        self.assertEqual(sum(n["type"] == "NunchakuQwenImageDiTLoader" for n in nodes.values()), 1)
        frames = {n["widgets_values"][0]: n for n in nodes.values() if n["type"] == "ArtSaveKeyframe"}
        self.assertEqual(sorted(frames), [1, 2, 3, 4])
        latents = sorted((n for n in nodes.values() if n["type"] == "Wan22ImageToVideoLatent"), key=lambda n: n["pos"][1])
        bridges = sorted((n for n in nodes.values() if n["type"] == "ArtBridgeFrames"), key=lambda n: n["pos"][1])
        tails = sorted((n for n in nodes.values() if n["type"] == "ArtLastFrame"), key=lambda n: n["pos"][1])
        self.assertEqual((len(latents), len(bridges), len(tails)), (4, 4, 3))
        self.assertEqual(parent(latents[0], 1)["id"], frames[1]["id"])
        for i in range(1, 4):
            self.assertEqual(parent(latents[i], 1)["id"], tails[i - 1]["id"])
            self.assertEqual(parent(tails[i - 1], 0)["id"], bridges[i - 1]["id"])
        self.assertEqual([parent(bridges[i], 2)["id"] for i in range(3)], [frames[2]["id"], frames[3]["id"], frames[4]["id"]])
        self.assertEqual(parent(bridges[3], 2)["type"], "ArtPrepare")
        join = next(n for n in nodes.values() if n["type"] == "ArtJoinFrames")
        self.assertEqual(len(join["inputs"]), 5)
        self.assertEqual(sum(n["type"] == "SaveVideo" and n["title"] == "最终单工作流 MP4" for n in nodes.values()), 1)


if __name__ == "__main__":
    unittest.main()
