"""User-visible contracts for the reusable painting-flight graph."""

import unittest

from masterpiece_flight.workflow_builder import build_workflow


class MasterpieceWorkflowTests(unittest.TestCase):
    def _sources(self, graph):
        nodes = {node["id"]: node for node in graph["nodes"]}
        links = {link[0]: link for link in graph["links"]}

        def source(node, slot):
            link_id = node["inputs"][slot]["link"]
            self.assertIsNotNone(link_id)
            return nodes[links[link_id][1]]

        return nodes, links, source

    def test_four_shots_follow_keyframes_and_finish_on_source_painting(self):
        graph = build_workflow(4)
        nodes, links, source = self._sources(graph)
        qwen_type = "eba40a3a-f6c5-48ac-b58e-55525d06b373"
        ltx_type = "cf70afc4-5a03-47ce-8210-734b1de6c6bc"
        keyframes = sorted((n for n in nodes.values() if n["type"] == qwen_type), key=lambda n: n["pos"][1])
        clips = sorted((n for n in nodes.values() if n["type"] == ltx_type), key=lambda n: n["pos"][1])
        self.assertEqual((len(keyframes), len(clips)), (4, 4))
        self.assertEqual([n["widgets_values"][2:5] for n in clips], [[5, 1280, 720]] * 4)
        canvas = next(n for n in nodes.values() if n["type"] == "ArtFrameCanvas")
        for index, clip in enumerate(clips):
            self.assertEqual(source(clip, 0)["id"], keyframes[index]["id"])
            self.assertEqual(source(clip, 1)["id"], keyframes[index + 1]["id"] if index < 3 else canvas["id"])
        self.assertEqual(source(keyframes[0], 0)["id"], canvas["id"])
        self.assertEqual(source(keyframes[1], 0)["id"], keyframes[0]["id"])

    def test_joins_four_clips_then_holds_full_original_painting(self):
        graph = build_workflow(4)
        nodes, _, source = self._sources(graph)
        joined = next(n for n in nodes.values() if n["type"] == "ConcatenateVideo")
        save = next(n for n in nodes.values() if n["type"] == "SaveVideo")
        still = next(n for n in nodes.values() if n["type"] == "ArtHoldFrames")
        self.assertEqual(source(still, 0)["type"], "ArtFrameCanvas")
        self.assertEqual(source(joined, 4)["type"], "CreateVideo")
        self.assertEqual(source(save, 0)["id"], joined["id"])
        self.assertEqual([source(joined, i)["type"] for i in range(4)], ["cf70afc4-5a03-47ce-8210-734b1de6c6bc"] * 4)

    def test_story_planner_drives_all_image_and_motion_prompts(self):
        graph = build_workflow(4)
        nodes, _, source = self._sources(graph)
        planner = next(n for n in nodes.values() if n["type"] == "ArtStoryPlanner")
        self.assertEqual(source(planner, 0)["type"], "LoadImage")
        fields = [n for n in nodes.values() if n["type"] == "ArtShotFields"]
        self.assertEqual(len(fields), 4)
        self.assertTrue(all(source(field, 0)["id"] == planner["id"] for field in fields))
        for node in nodes.values():
            if node["type"] == "eba40a3a-f6c5-48ac-b58e-55525d06b373":
                self.assertEqual(source(node, 3)["type"], "ArtShotFields")
            if node["type"] == "cf70afc4-5a03-47ce-8210-734b1de6c6bc":
                self.assertEqual(source(node, 2)["type"], "ArtShotFields")

    def test_graph_links_and_subgraph_definitions_are_complete(self):
        graph = build_workflow(4)
        nodes = {n["id"]: n for n in graph["nodes"]}
        defs = {s["id"] for s in graph["definitions"]["subgraphs"]}
        self.assertIn("eba40a3a-f6c5-48ac-b58e-55525d06b373", defs)
        self.assertIn("cf70afc4-5a03-47ce-8210-734b1de6c6bc", defs)
        for link_id, src, src_slot, dst, dst_slot, kind in graph["links"]:
            self.assertIn(src, nodes)
            self.assertIn(dst, nodes)
            self.assertEqual(nodes[src]["outputs"][src_slot]["type"], kind)
            self.assertIn(kind, nodes[dst]["inputs"][dst_slot]["type"].split(","))
            self.assertEqual(nodes[dst]["inputs"][dst_slot]["link"], link_id)
            self.assertIn(link_id, nodes[src]["outputs"][src_slot]["links"])

    def test_one_clip_pilot_retains_exact_original_still(self):
        graph = build_workflow(1)
        nodes = graph["nodes"]
        self.assertEqual(sum(n["type"] == "cf70afc4-5a03-47ce-8210-734b1de6c6bc" for n in nodes), 1)
        self.assertEqual(sum(n["type"] == "eba40a3a-f6c5-48ac-b58e-55525d06b373" for n in nodes), 1)
        self.assertTrue(any(n["type"] == "ArtHoldFrames" for n in nodes))


if __name__ == "__main__":
    unittest.main()
