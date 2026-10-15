import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class H3DownloaderTests(unittest.TestCase):
    def test_missing_symlink_target_is_created_before_download(self):
        from masterpiece_flight2.scripts import download_h3_models

        class DownloadStarted(Exception):
            pass

        with tempfile.TemporaryDirectory() as temp:
            comfy = Path(temp) / "ComfyUI"
            comfy.mkdir()
            data_models = Path(temp) / "data" / "ComfyUI-models"
            (comfy / "models").symlink_to(data_models)
            argv = ["download_h3_models.py", "--comfy-root", str(comfy),
                    "--runtime", "cu128", "--set", "h3"]
            usage = download_h3_models.shutil.disk_usage(temp)
            enough_space = usage._replace(total=100_000_000_000, used=0, free=100_000_000_000)
            observed = None
            with patch.object(sys, "argv", argv), \
                 patch.object(download_h3_models, "ensure_source_speed"), \
                 patch.object(download_h3_models.shutil, "disk_usage", return_value=enough_space), \
                 patch.object(download_h3_models, "download", side_effect=DownloadStarted):
                try:
                    download_h3_models.main()
                except Exception as exc:
                    observed = exc
            self.assertIsInstance(observed, DownloadStarted)
            self.assertTrue(data_models.is_dir())
            self.assertTrue((data_models / ".masterpiece_downloads").is_dir())

    def test_cu128_check_only_lists_matching_h3_weights(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "download_h3_models.py"),
                 "--comfy-root", temp, "--set", "h3", "--runtime", "cu128", "--check-only"],
                text=True, capture_output=True,
            )
            self.assertIn("minimax_h3_fl2va_pruned_fp8_scaled.safetensors", result.stdout)
            self.assertIn("minimax_h3_video_vae_fp16.safetensors", result.stdout)
            self.assertNotIn("minimax_h3_fl2va_pruned_int8_convrot.safetensors", result.stdout)

    def test_large_download_is_rejected_when_source_probe_is_too_slow(self):
        from masterpiece_flight2.scripts import download_h3_models

        with patch.object(download_h3_models, "probe_url", return_value=(1_000_000, 20.0)):
            with self.assertRaisesRegex(RuntimeError, "too slow"):
                download_h3_models.ensure_source_speed("modelscope", minimum_mbps=5)

    def test_custom_model_root_reports_data_disk_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            comfy = Path(temp) / "ComfyUI"
            model_root = Path(temp) / "data" / "models"
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "download_h3_models.py"),
                 "--comfy-root", str(comfy), "--model-root", str(model_root),
                 "--set", "h3", "--check-only"],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(str(model_root / "diffusion_models"), result.stdout)
            self.assertNotIn(str(comfy / "models"), result.stdout)

    def test_model_link_uses_data_disk_file_without_copying(self):
        from masterpiece_flight2.scripts.download_h3_models import link_to_comfy

        with tempfile.TemporaryDirectory() as temp:
            data_file = Path(temp) / "data" / "models" / "vae" / "model.safetensors"
            data_file.parent.mkdir(parents=True)
            data_file.write_bytes(b"example")
            comfy = Path(temp) / "ComfyUI"
            link_to_comfy(data_file, comfy, Path(temp) / "data" / "models")
            link = comfy / "models" / "vae" / "model.safetensors"
            self.assertTrue(link.is_symlink())
            self.assertEqual(link.resolve(), data_file.resolve())

    def test_blackwell_qwen_download_set_requests_fp4_weight(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "download_h3_models.py"),
                 "--comfy-root", temp, "--set", "qwen", "--check-only"],
                text=True, capture_output=True,
            )
            self.assertIn("svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors", result.stdout)
            self.assertNotIn("svdq-int4", result.stdout)

    def test_check_only_rejects_missing_weights_without_download(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "download_h3_models.py"),
                 "--comfy-root", temp, "--set", "h3", "--check-only"],
                text=True, capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("minimax_h3_fl2va_pruned_int8_convrot.safetensors", result.stdout)
            self.assertFalse((Path(temp) / "models").exists())


if __name__ == "__main__":
    unittest.main()
