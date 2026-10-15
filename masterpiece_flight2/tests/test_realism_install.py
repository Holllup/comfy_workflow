import hashlib
import importlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('masterpiece_flight2.scripts.realism_install'))
        self.m = importlib.import_module('masterpiece_flight2.scripts.realism_install')

    def test_only_exact_checksum_is_treated_as_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model'; path.write_bytes(b'complete')
            sha = hashlib.sha256(b'complete').hexdigest()
            self.assertTrue(self.m.verified(path, sha))
            path.write_bytes(b'incomplete')
            self.assertFalse(self.m.verified(path, sha))

    def test_probe_rejects_full_response_and_short_sample(self):
        class Reply(io.BytesIO):
            status = 200
            headers = {'Content-Type': 'application/octet-stream', 'Content-Range': 'bytes 0-7/100'}
        with self.assertRaisesRegex(RuntimeError, '206'):
            self.m.probe('https://example.test/model', 8, opener=lambda *a, **k: Reply(b'abcdefgh'))
        Reply.status = 206
        with self.assertRaisesRegex(RuntimeError, 'sample'):
            self.m.probe('https://example.test/model', 8, opener=lambda *a, **k: Reply(b'abc'))
        speed = self.m.probe('https://example.test/model', 8, opener=lambda *a, **k: Reply(b'abcdefgh'))
        self.assertGreater(speed, 0)

    def test_missing_comfy_nodes_are_reported_before_render(self):
        problems = self.m.check_nodes({'UNETLoader': {}})
        self.assertTrue(any('Flux2Scheduler' in item for item in problems))
        self.assertTrue(any('MiniMaxH3ImageToVideo' in item for item in problems))

    def test_autodl_download_rejects_system_disk_model_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp) / 'autodl-tmp'; data.mkdir()
            self.assertTrue(callable(getattr(self.m, 'check_model_location', None)))
            with self.assertRaisesRegex(RuntimeError, 'data disk'):
                self.m.check_model_location(Path(tmp) / 'ComfyUI' / 'models', data)
            self.m.check_model_location(data / 'models', data)

    def test_matching_models_are_skipped_and_bad_download_never_replaces_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            weight = self.m.Model('flux', 'diffusion_models/x.safetensors', 'org/repo', 'x.safetensors', 8,
                                  hashlib.sha256(b'complete').hexdigest())
            target = root / weight.target; target.parent.mkdir(); target.write_bytes(b'complete')
            calls = []
            def fetch(weight, staging, source):
                calls.append(weight.target)
                path = staging / 'bad'; path.write_bytes(b'bad'); return path
            self.m.install([weight], root, 'huggingface', fetch=fetch, probe_fn=lambda url: 9_000_000)
            self.assertEqual(calls, [])
            target.write_bytes(b'old')
            with self.assertRaisesRegex(RuntimeError, 'checksum'):
                self.m.install([weight], root, 'huggingface', fetch=fetch, probe_fn=lambda url: 9_000_000)
            self.assertEqual(target.read_bytes(), b'old')


if __name__ == '__main__': unittest.main()
