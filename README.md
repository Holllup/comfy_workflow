# Cat Vlog ComfyUI Workflow

A six-shot, 30-second vertical cat vlog workflow for AutoDL ComfyUI v22. Each run drafts a new day-in-the-life story locally, reuses the same cat reference image, generates six keyframes and six five-second video clips, then joins them into one silent MP4.

- Importable workflow: [`workflows/cat_vlog_6x5s.json`](workflows/cat_vlog_6x5s.json)
- Installable bundle: [`cat_vlog_bundle.zip`](cat_vlog_bundle.zip)
- Setup and usage: [`README_安装.md`](README_%E5%AE%89%E8%A3%85.md)

Model weights are not included. The installer downloads the missing Qwen3 and Wan 2.2 files to the rented instance's data disk. Run `python3 -m unittest discover -s tests -q` for the local checks.
