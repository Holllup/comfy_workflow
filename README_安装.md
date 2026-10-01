# 小猫一天 Vlog：AutoDL ComfyUI v22 安装与使用

## 交付内容

- `workflows/cat_vlog_6x5s.json`：可拖入 ComfyUI 的工作流文件。
- `cat_vlog/`：八个自定义节点，负责本地编剧、固定主角、按镜头串行运行和视频合成。
- `cat_vlog/download_models.py`：只下载缺失的 Qwen3 剧情模型和 Wan 2.2 5B 文件。

工作流针对用户当前的 AutoDL v22 镜像、RTX 4090D 24GB 和数据盘编制。镜像中已有 Z-Image Turbo、Nunchaku Qwen-Image-Edit-2509 Lightning 及其模型；Wan 5B 和本地剧情模型需要另行下载。单独导入 JSON 后若看到 `Cat...` 缺失节点，先安装下述节点包。

## 在 AutoDL 安装

1. 将 `cat_vlog_bundle.zip` 上传到 JupyterLab 的 `/root/autodl-tmp/`，打开 **Terminal**，执行以下命令。首次下载约需 26GB 数据盘空间，GPU 实例运行期间持续计费。

```bash
cd /root/autodl-tmp
unzip -o cat_vlog_bundle.zip -d cat_vlog_bundle
python -m pip install modelscope-hub
python /root/autodl-tmp/cat_vlog_bundle/cat_vlog/download_models.py
cp -R /root/autodl-tmp/cat_vlog_bundle/cat_vlog /root/autodl-tmp/ComfyUI/custom_nodes/
```

2. 确认 ComfyUI 容器里有 `ffmpeg`：

```bash
ffmpeg -version
```

3. 在镜像的 `启动器.ipynb` 中按其说明**重启内核并运行全部单元格**，待 ComfyUI 重新出现。然后从自己电脑把 `cat_vlog_6x5s.json` 拖进 ComfyUI 画布。首次打开模型下拉框如未刷新，刷新 ComfyUI 页面。

下载器从 ModelScope 的 Qwen 与 Comfy-Org 官方仓库获取模型；它会跳过已经存在的文件。下载位置是 `/root/autodl-tmp/cat_vlog/models/` 和 `/root/autodl-tmp/models/`，与镜像的模型目录配置匹配。

## 运行和输出

在左上方 **“01 · 随机生成六镜剧情”** 节点只需修改 `theme`（主题）；保持 `auto_random=true`，每次点右上角“运行”都会生成新剧情。`seed` 在自动随机模式下无需填写。例子：`小猫雨天第一次去公园，轻松幽默，最后平安回家`。六镜的首帧与动作提示词由本地编剧模型自动生成，不需要手写。

首次运行会创建固定的橘白小猫定妆照，后续运行复用它。画布里的 **“主角定妆照预览”** 和六个 **“首帧预览”** 节点会显示生成的图片；也可到下述输出目录查看 PNG。预览不会暂停任务，六张首帧完成后视频阶段会自动继续。六条首帧分支和六条视频分支在画布上并列排布，节点依赖保证实际推理串行。

输出保存在 `/root/autodl-tmp/ComfyUI/output/cat_vlog/`：

- `reference.png`：跨运行复用的小猫定妆照。
- `<run_id>/shot_01.png` 至 `shot_06.png`：六张首帧。
- `<run_id>/shot_01.mp4` 至 `shot_06.mp4`：六段精确 5 秒、704×1280、24 fps、无声视频。
- `<run_id>/cat_vlog_30s.mp4`：按顺序合成的 30 秒成片。
- `<run_id>/story.json`、`manifest.json`：剧情、种子和模型信息。

如果某镜失败，已保存的镜头仍在该次运行目录中。工作流不会自动降低分辨率；发生显存不足时先记录失败镜头和显存峰值，再调整模型配置。若想换一只固定主角，先备份并删除 `reference.png`，下一次运行会重新生成定妆照。

## 当前版本限制

首版固定六镜各五秒、竖屏写实、无声、无字幕。运行成本和耗时取决于实例、模型下载速度及重试次数；尚未在用户云端完成六镜端到端实测。工作流、节点文件和下载脚本都可在本地检查，导入后先用一镜确认模型与显存，再运行完整工作流。
