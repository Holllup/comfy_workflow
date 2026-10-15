"""Download only the models needed by the AutoDL v22 workflow."""

import argparse
import shutil
from pathlib import Path


QWEN_FILES = [
    "config.json", "generation_config.json", "merges.txt", "vocab.json",
    "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json",
    "model-00001-of-00003.safetensors", "model-00002-of-00003.safetensors",
    "model-00003-of-00003.safetensors",
]

WAN_FILES = [
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     "split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors",
     "models/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors"),
    ("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
     "split_files/vae/wan2.2_vae.safetensors",
     "models/vae/wan2.2_vae.safetensors"),
    ("Comfy-Org/Wan_2.1_ComfyUI_repackaged",
     "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
     "models/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"),
]


def install_models(data_root: Path, download) -> None:
    data_root = Path(data_root)
    story_folder = data_root / "cat_vlog/models/Qwen3-4B-Instruct-2507"
    if not all((story_folder / name).is_file() for name in QWEN_FILES):
        story_folder.mkdir(parents=True, exist_ok=True)
        download(
            model_id="Qwen/Qwen3-4B-Instruct-2507",
            local_dir=str(story_folder),
            allow_file_pattern=QWEN_FILES,
        )

    for model_id in dict.fromkeys(row[0] for row in WAN_FILES):
        missing = [row for row in WAN_FILES if row[0] == model_id and not (data_root / row[2]).is_file()]
        if not missing:
            continue
        staging = data_root / "cat_vlog/downloads" / model_id.replace("/", "_")
        staging.mkdir(parents=True, exist_ok=True)
        download(
            model_id=model_id,
            local_dir=str(staging),
            allow_file_pattern=[row[1] for row in missing],
        )
        for _, relative, destination in missing:
            source = staging / relative
            if not source.is_file():
                raise FileNotFoundError(f"Model download did not produce {source}")
            target = data_root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(target))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default="/root/autodl-tmp")
    args = parser.parse_args()
    from modelscope_hub.compat import snapshot_download

    install_models(Path(args.data_root), snapshot_download)


if __name__ == "__main__":
    main()
