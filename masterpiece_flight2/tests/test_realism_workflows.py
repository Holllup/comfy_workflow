import importlib
import importlib.util
import unittest


class RealismWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('masterpiece_flight2.realism_workflows'))
        self.graphs = importlib.import_module('masterpiece_flight2.realism_workflows').build_stages()

    def test_four_stages_have_three_candidates_and_only_morph_sees_artwork(self):
        self.assertEqual(len(self.graphs), 4)
        endpoints, morph, frames, full = self.graphs.values()
        candidates = [n for n in endpoints['nodes'] if n['type'] == 'ArtV3SaveImage' and n['widgets_values'][0].startswith('r5_candidate')]
        self.assertEqual(len(candidates), 3)
        self.assertEqual(sum(n['type'] == 'SamplerCustomAdvanced' for n in frames['nodes']), 4)
        self.assertEqual(sum(n['type'] == 'MiniMaxH3ImageToVideo' for n in morph['nodes']), 1)
        self.assertEqual(sum(n['type'] == 'MiniMaxH3ImageToVideo' for n in full['nodes']), 4)
        nodes = {n['id']: n for n in full['nodes']}
        for link in full['links']:
            if nodes[link[1]]['type'] == 'ArtV3LoadFrames' and link[2] == 5:
                self.fail('The artwork must not be wired into a flight node')

    def test_reverse_frames_use_only_the_next_realistic_frame(self):
        graph = list(self.graphs.values())[2]
        nodes = {n['id']: n for n in graph['nodes']}
        links = {link[0]: link for link in graph['links']}
        encodes = sorted((n for n in nodes.values() if n['type'] == 'VAEEncode'), key=lambda n: n['pos'][1])
        self.assertEqual(len(encodes), 4)
        sources = [nodes[links[n['inputs'][0]['link']][1]]['type'] for n in encodes]
        self.assertEqual(sources, ['ArtV3KeyframeStart', 'ArtV3SaveImage', 'ArtV3SaveImage', 'ArtV3SaveImage'])
        self.assertFalse(any(n['type'] in ('LoadImage', 'ArtPrepare', 'ArtSpatialStyleSeed') for n in nodes.values()))

    def test_graphs_have_valid_links_no_cycles_and_registered_custom_nodes(self):
        from masterpiece_flight2 import NODE_CLASS_MAPPINGS
        for graph in self.graphs.values():
            nodes = {n['id']: n for n in graph['nodes']}
            parents = {i: set() for i in nodes}
            for lid, src, ss, dst, ds, kind in graph['links']:
                self.assertIn(src, nodes); self.assertIn(dst, nodes)
                self.assertEqual(nodes[dst]['inputs'][ds]['link'], lid)
                self.assertIn(lid, nodes[src]['outputs'][ss]['links'])
                self.assertEqual(nodes[src]['outputs'][ss]['type'], kind)
                parents[dst].add(src)
            removed = set()
            while True:
                ready = {i for i, ps in parents.items() if i not in removed and ps <= removed}
                if not ready: break
                removed.update(ready)
            self.assertEqual(removed, set(nodes))
            for node in nodes.values():
                if node['type'].startswith('ArtV3'):
                    self.assertIn(node['type'], NODE_CLASS_MAPPINGS)
                    cls = NODE_CLASS_MAPPINGS[node['type']]
                    self.assertEqual(tuple(o['type'] for o in node['outputs']), cls.RETURN_TYPES)
                    inputs = cls.INPUT_TYPES()
                    allowed = set(inputs.get('required', {})) | set(inputs.get('optional', {}))
                    self.assertTrue(all(i['name'] in allowed for i in node['inputs']))

    def test_flux_has_one_reference_and_quality_profile_without_nunchaku(self):
        for graph in (list(self.graphs.values())[0], list(self.graphs.values())[2]):
            nodes = graph['nodes']
            self.assertFalse(any('Nunchaku' in n['type'] for n in nodes))
            loader = next(n for n in nodes if n['type'] == 'UNETLoader')
            self.assertEqual(loader['widgets_values'][0], 'flux2_dev_fp8mixed.safetensors')
            clip = next(n for n in nodes if n['type'] == 'CLIPLoader')
            self.assertEqual(clip['widgets_values'][0], 'mistral_3_small_flux2_bf16.safetensors')
            self.assertEqual(sum(n['type'] == 'ReferenceLatent' for n in nodes), 4)
            self.assertTrue(all(n['widgets_values'] == [20, 1344, 768] for n in nodes if n['type'] == 'Flux2Scheduler'))


if __name__ == '__main__': unittest.main()
