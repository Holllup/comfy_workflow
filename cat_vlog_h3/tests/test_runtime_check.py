import unittest


class RuntimeCheckTests(unittest.TestCase):
    def test_autogrow_image_port_is_valid_only_when_parent_input_exists(self):
        from cat_vlog_h3.scripts.check_runtime import graph_errors

        graph = {"nodes": [{"type": "TextEncodeJoyImageEdit", "inputs": [
            {"name": "clip", "type": "CLIP"},
            {"name": "images.image0", "type": "IMAGE"},
        ], "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING"}]}]}
        definition = {"input": {"required": {"clip": ["CLIP"]},
                                "optional": {"images": ["AUTOGROW"]}}, "output": ["CONDITIONING"]}
        self.assertEqual(graph_errors(graph, {"TextEncodeJoyImageEdit": definition}), [])
        definition["input"]["optional"].clear()
        self.assertTrue(graph_errors(graph, {"TextEncodeJoyImageEdit": definition}))

    def test_graph_matches_object_info_ports(self):
        from cat_vlog_h3.scripts.check_runtime import graph_errors

        graph = {"nodes": [{
            "id": 1, "type": "Example", "inputs": [{"name": "image", "type": "IMAGE"}],
            "outputs": [{"name": "out", "type": "IMAGE"}],
        }]}
        info = {"Example": {"input": {"required": {"image": ["IMAGE"]}}, "output": ["IMAGE"]}}
        self.assertEqual(graph_errors(graph, info), [])
        self.assertTrue(any("missing input" in item for item in graph_errors(
            graph, {"Example": {"input": {"required": {}}, "output": ["IMAGE"]}}
        )))
        self.assertTrue(any("output" in item for item in graph_errors(
            graph, {"Example": {"input": {"required": {"image": ["IMAGE"]}}, "output": ["AUDIO"]}}
        )))
        self.assertTrue(any("missing node" in item for item in graph_errors(graph, {})))


if __name__ == "__main__":
    unittest.main()
