import tempfile
import unittest
from pathlib import Path

from cat_vlog.download_models import install_models


class ModelDownloadTests(unittest.TestCase):
    def test_places_selected_wan_files_in_comfyui_model_folders(self):
        calls = []

        def fake_download(model_id, local_dir, allow_file_pattern):
            calls.append((model_id, tuple(allow_file_pattern)))
            for relative in allow_file_pattern:
                file = Path(local_dir) / relative
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(b"model-data")
            return local_dir

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            install_models(root, fake_download)
            self.assertTrue((root / "models/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors").is_file())
            self.assertTrue((root / "models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors").is_file())
            self.assertTrue((root / "models/vae/wan2.2_vae.safetensors").is_file())
            self.assertTrue((root / "cat_vlog/models/Qwen3-4B-Instruct-2507/model-00001-of-00003.safetensors").is_file())
            self.assertEqual(len(calls), 3)


if __name__ == "__main__":
    unittest.main()
