import json
import unittest


def _node_map(graph):
    return {node["id"]: node for node in graph["nodes"]}


def _incoming(graph, node, input_name):
    port = next(item for item in node["inputs"] if item["name"] == input_name)
    return next(link for link in graph["links"] if link[0] == port["link"])


class WorkflowTests(unittest.TestCase):
    def test_cast_reference_bank_reaches_all_dynamic_joyai_encoders(self):
        from cat_vlog_h3.workflow_builder import build_workflow
        graph = build_workflow()
        nodes = _node_map(graph)
        texts = [n for n in graph["nodes"] if n["type"] == "CatH3JoyEncode"]
        self.assertEqual(len(texts), 20)
        for text in texts:
            link = _incoming(graph, text, "references")
            select = nodes[link[1]]
            self.assertEqual(select["type"], "CatH3SelectReferences")
            self.assertEqual(link[2], 0)
            reference = nodes[_incoming(graph, select, "references")[1]]
            self.assertEqual(reference["type"], "CatH3References")

    def test_full_graph_has_ten_independent_av_lanes_and_shared_models(self):
        try:
            from cat_vlog_h3.workflow_builder import build_workflow
        except ImportError as exc:
            self.fail(f"H3 workflow builder is missing: {exc}")
        graph = build_workflow()
        types = [node["type"] for node in graph["nodes"]]
        for kind, count in (
            ("MiniMaxH3ImageToVideo", 10), ("SamplerCustomAdvanced", 10),
            ("VAEDecodeAudio", 10), ("CatH3SaveAV", 10),
            ("CatH3SaveFrame", 10), ("CatH3ShotFields", 10),
            ("CatH3VideoGate", 10), ("CatH3JoyEncode", 20),
            ("UNETLoader", 2), ("CatH3Finish", 1),
        ):
            self.assertEqual(types.count(kind), count, kind)
        joyai_loader = next(node for node in graph["nodes"] if node["type"] == "UNETLoader" and "JoyAI" in node["title"])
        self.assertEqual(joyai_loader["widgets_values"][0], "joyai_image_edit_plus_bf16.safetensors")
        self.assertNotIn("Wan22ImageToVideoLatent", types)
        self.assertNotIn("CatStoryPlanner", types)
        scheduler = next(node for node in graph["nodes"] if node["type"] == "BasicScheduler")
        self.assertEqual(scheduler["widgets_values"][1], 20)
        for node in graph["nodes"]:
            if node["type"] == "MiniMaxH3ImageToVideo":
                self.assertEqual(node["widgets_values"][1:4], [1344, 768, 175])
        self.assertTrue(any(node["type"] == "VAELoader" and node["widgets_values"][0] == "minimax_h3_audio_vae_fp32.safetensors" for node in graph["nodes"]))

    def test_shots_use_their_own_frames_and_video_execution_is_serial(self):
        from cat_vlog_h3.workflow_builder import build_workflow
        graph = build_workflow()
        nodes = _node_map(graph)
        gates = sorted((node for node in graph["nodes"] if node["type"] == "CatH3VideoGate"), key=lambda n: n["widgets_values"][0])
        saves = sorted((node for node in graph["nodes"] if node["type"] == "CatH3SaveAV"), key=lambda n: n["widgets_values"][0])
        stage = next(node for node in graph["nodes"] if node["type"] == "CatH3Stage")
        for index, (gate, save) in enumerate(zip(gates, saves), 1):
            start_source = nodes[_incoming(graph, gate, "start")[1]]
            self.assertEqual(start_source["type"], "CatH3SaveFrame")
            self.assertEqual(start_source["widgets_values"], [index])
            prior = nodes[_incoming(graph, gate, "prior_done")[1]]
            self.assertEqual(prior["id"], stage["id"] if index == 1 else saves[index - 2]["id"])
            video = next(node for node in graph["nodes"] if node["type"] == "MiniMaxH3ImageToVideo" and f"{index:02d}" in node["title"])
            self.assertEqual(nodes[_incoming(graph, video, "first_frame")[1]]["id"], gate["id"])
            self.assertFalse(any(port["name"] == "last_frame" and port.get("link") for port in video["inputs"]))
            audio_decode = nodes[_incoming(graph, save, "audio")[1]]
            self.assertEqual(audio_decode["type"], "VAEDecodeAudio")
        finish = next(node for node in graph["nodes"] if node["type"] == "CatH3Finish")
        self.assertEqual([nodes[_incoming(graph, finish, f"clip_{i:02d}")[1]]["id"] for i in range(1, 11)], [node["id"] for node in saves])

    def test_review_and_render_lazy_paths_exclude_opposite_stage_models(self):
        from cat_vlog_h3.workflow_builder import build_workflow
        from cat_vlog_h3 import NODE_CLASS_MAPPINGS
        from cat_vlog_h3.nodes import REVIEW, RENDER
        graph = build_workflow()
        nodes = _node_map(graph)
        links = {link[0]: link for link in graph["links"]}
        for phase, forbidden_title, required_title in ((REVIEW, "H3 模型", "JoyAI Plus"),
                                                       (RENDER, "JoyAI Plus", "H3 模型")):
            visited = set()
            def visit(node_id):
                if node_id in visited:
                    return
                visited.add(node_id)
                node = nodes[node_id]
                cls = NODE_CLASS_MAPPINGS.get(node["type"])
                schema = cls.INPUT_TYPES().get("required", {}) if cls else {}
                lazy = {name for name, spec in schema.items() if len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get("lazy")}
                needed = {p["name"] for p in node.get("inputs", []) if p["name"] not in lazy}
                if cls and hasattr(cls, "check_lazy_status"):
                    needed.update(cls().check_lazy_status(phase=phase, ready="approved:" + json.dumps({"selected": list(range(1, 11)), "frames": {"1": {"sha256": "test"}}}) if phase == RENDER else None))
                    if phase == RENDER and "ready" in lazy:
                        needed.add("ready")
                for port in node.get("inputs", []):
                    if port["name"] in needed and port.get("link"):
                        visit(links[port["link"]][1])
            for node in graph["nodes"]:
                cls = NODE_CLASS_MAPPINGS.get(node["type"])
                if cls and getattr(cls, "OUTPUT_NODE", False):
                    visit(node["id"])
            titles = {nodes[i].get("title", "") for i in visited}
            self.assertFalse(any(forbidden_title in title for title in titles), titles)
            self.assertTrue(any(required_title in title for title in titles), titles)

    def test_exported_links_resolve_to_matching_ports(self):
        from cat_vlog_h3.workflow_builder import build_workflow
        graph = build_workflow()
        nodes = _node_map(graph)
        self.assertEqual(graph["last_node_id"], len(graph["nodes"]))
        self.assertEqual(graph["last_link_id"], len(graph["links"]))
        for link_id, source_id, source_slot, target_id, target_slot, kind in graph["links"]:
            self.assertIn(link_id, nodes[source_id]["outputs"][source_slot]["links"])
            self.assertEqual(nodes[target_id]["inputs"][target_slot]["link"], link_id)
            self.assertEqual(kind, nodes[source_id]["outputs"][source_slot]["type"])
        json.dumps(graph)


if __name__ == "__main__":
    unittest.main()
