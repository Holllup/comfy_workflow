from pathlib import Path
import unittest

from cat_vlog_h3.scripts import check_runtime
from cat_vlog_h3.workflow_builder import build_workflow


class V4PreflightTests(unittest.TestCase):
    def test_wrapper_still_requires_supported_native_joyai_backend(self):
        graph = {'nodes': [{'type': 'CatH3JoyEncode', 'inputs': [], 'outputs': []}]}
        info = {'CatH3JoyEncode': {'input': {}, 'output': []}}
        self.assertTrue(any('JoyAI' in error for error in check_runtime.graph_errors(graph, info)))

    def test_modified_parameters_are_reported_before_any_model_run(self):
        try:
            from cat_vlog_h3.scripts.preflight import graph_configuration_errors
        except ImportError:
            self.fail('v4 needs an artifact and parameter preflight')
        graph = build_workflow()
        self.assertEqual(graph_configuration_errors(graph), [])
        sampler = next(node for node in graph['nodes'] if node['type'] == 'KSampler')
        sampler['widgets_values'][2] = 4
        self.assertTrue(graph_configuration_errors(graph))

    def test_artifact_preflight_resolves_every_asset_and_reports_pending_quality(self):
        try:
            from cat_vlog_h3.scripts.preflight import inspect_artifacts
        except ImportError:
            self.fail('v4 needs an artifact and parameter preflight')
        project = Path(__file__).resolve().parents[1]
        report = inspect_artifacts(project)
        self.assertEqual(report['schema_version'], 4)
        self.assertEqual(report['errors'], [])
        self.assertFalse(report['model_quality_verified'])
        self.assertEqual(report['total_frames'], 1750)


if __name__ == '__main__':
    unittest.main()
