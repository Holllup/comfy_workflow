import json
import unittest

from cat_vlog_h3 import NODE_CLASS_MAPPINGS, nodes
from cat_vlog_h3.workflow_builder import build_workflow


class V4WorkflowTests(unittest.TestCase):
    def test_graph_routes_dynamic_photo_packs_and_real_lengths_to_native_models(self):
        graph = build_workflow()
        by_id = {node['id']: node for node in graph['nodes']}
        links = {link[0]: link for link in graph['links']}
        encoders = [node for node in graph['nodes'] if node['type'] == 'CatH3JoyEncode']
        self.assertEqual(len(encoders), 20)
        for node in encoders:
            port = next(port for port in node['inputs'] if port['name'] == 'references')
            self.assertEqual(by_id[links[port['link']][1]]['type'], 'CatH3SelectReferences')
        for node in (node for node in graph['nodes'] if node['type'] == 'MiniMaxH3ImageToVideo'):
            port = next(port for port in node['inputs'] if port['name'] == 'length')
            incoming = links[port['link']]
            self.assertEqual(by_id[incoming[1]]['type'], 'CatH3ShotFields')
            self.assertEqual(incoming[2], 6)
            self.assertFalse(any(port['name'] == 'last_frame' and port['link'] for port in node['inputs']))
        control = next(node for node in graph['nodes'] if node['type'] == 'CatH3Story')
        self.assertEqual(control['widgets_values'][-2:], ['all', 'pending'])

    def test_lazy_model_requests_match_phase_and_selected_shots(self):
        graph = build_workflow()
        by_id = {node['id']: node for node in graph['nodes']}
        links = {link[0]: link for link in graph['links']}
        for phase in (nodes.REVIEW, nodes.RENDER):
            visited = set()
            ready = 'approved:' + json.dumps({'selected': [3], 'frames': {'3': {'sha256': 'sample'}}})
            def visit(node_id):
                if node_id in visited:
                    return
                visited.add(node_id)
                node = by_id[node_id]
                cls = NODE_CLASS_MAPPINGS.get(node['type'])
                schema = cls.INPUT_TYPES().get('required', {}) if cls else {}
                lazy = {name for name, spec in schema.items() if len(spec) > 1 and isinstance(spec[1], dict) and spec[1].get('lazy')}
                needed = {port['name'] for port in node.get('inputs', []) if port['name'] not in lazy}
                if cls and hasattr(cls, 'check_lazy_status'):
                    index = node.get('widgets_values', [None])[0] if node.get('widgets_values') else None
                    needed.update(cls().check_lazy_status(phase=phase, ready=ready if phase == nodes.RENDER else None,
                                                          selected_shots='3', index=index))
                for port in node.get('inputs', []):
                    if port['name'] in needed and port.get('link'):
                        visit(links[port['link']][1])
            for node in graph['nodes']:
                cls = NODE_CLASS_MAPPINGS.get(node['type'])
                if cls and getattr(cls, 'OUTPUT_NODE', False):
                    visit(node['id'])
            titles = [by_id[index].get('title', '') for index in visited]
            if phase == nodes.REVIEW:
                self.assertFalse(any('H3 模型' in title for title in titles))
                self.assertTrue(any('JoyAI Plus' in title for title in titles))
            else:
                self.assertFalse(any('JoyAI Plus' in title for title in titles))
                self.assertTrue(any('H3 模型' in title for title in titles))
            samplers = [by_id[index] for index in visited if by_id[index]['type'] in ('KSampler', 'SamplerCustomAdvanced')]
            self.assertEqual(len(samplers), 1)
            self.assertIn('03', samplers[0]['title'])


if __name__ == '__main__':
    unittest.main()
