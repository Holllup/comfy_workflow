import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


class JoyAIModelDownloadTests(unittest.TestCase):
    def test_h3_audio_check_does_not_require_obsolete_qwen_image_weights(self):
        from cat_vlog_h3.scripts.ensure_models import EXISTING_MODELS

        self.assertNotIn("diffusion_models/svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors", EXISTING_MODELS)
        self.assertNotIn("clip/qwen_2.5_vl_7b_fp8_scaled.safetensors", EXISTING_MODELS)
        self.assertNotIn("vae/qwen_image_vae.safetensors", EXISTING_MODELS)

    def test_corrupt_or_truncated_model_is_never_treated_as_installed(self):
        from cat_vlog_h3.scripts.ensure_joyai_models import verify_spec

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "model.safetensors"
            payload = b"verified model bytes"
            expected = (len(payload), hashlib.sha256(payload).hexdigest())
            self.assertFalse(verify_spec(path, expected))
            path.write_bytes(payload[:-1])
            self.assertFalse(verify_spec(path, expected))
            path.write_bytes(payload)
            self.assertTrue(verify_spec(path, expected))

    def test_route_probe_uses_the_same_pinned_model_file_for_every_source(self):
        from cat_vlog_h3.scripts.ensure_joyai_models import qualified_routes

        seen = []
        def probe(url):
            seen.append(url)
            return 4_194_304, 0.5 if "hf-mirror" in url else 3.0

        with patch("cat_vlog_h3.scripts.ensure_joyai_models.probe_source", side_effect=probe):
            routes = qualified_routes("vae/wan_2.1_vae.safetensors", 253_815_318, min_mbps=5)
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0][1], "hf-mirror")
        self.assertTrue(all("/vae/wan_2.1_vae.safetensors" in url for url in seen))
        self.assertTrue(all("/resolve/a90b1a3ba2829a476dbcaeb9c4819601a8b1e561/" in url for url in seen))

    def test_probe_only_reports_success_without_starting_any_download(self):
        from cat_vlog_h3.scripts.ensure_joyai_models import main

        with tempfile.TemporaryDirectory() as directory, \
             patch("cat_vlog_h3.scripts.ensure_joyai_models._model_root", return_value=Path(directory)), \
             patch("cat_vlog_h3.scripts.ensure_joyai_models.qualified_routes", return_value=[(8_000_000, "hf-mirror", "url")]), \
             patch("cat_vlog_h3.scripts.ensure_joyai_models.fetch_verified", side_effect=AssertionError("download started")):
            self.assertEqual(main(["--probe-only"]), 0)


if __name__ == "__main__":
    unittest.main()
