# FLUX.2 dev＋H3：写实飞行到原画（v3）

四段电影式梦幻写实飞行，到原画对应视角停稳，再用独立 H3 片段逐渐画作化。最后完整原画居中、AI 扩展的两侧一起画作化并定格一秒。成片 1280×720、24 fps、无声、640 帧，约 26.67 秒。

## 镜像与环境

用户截图中的 AutoDL 社区镜像 `ComfyUI_2024 v18.2` 标注 PyTorch 2.12.1、CUDA 13.0，包含 H3 相关工作流，可作为安装候选。GitHub 的 [Comfy-Org/ComfyUI](https://github.com/Comfy-Org/ComfyUI) 是官方源码；截图镜像由社区维护。仅凭标签不能确认所有节点、模型文件和显存组合已通过推理，开机后要运行下面的检查。

新图使用原生 FLUX.2 编辑节点和 H3 FP8/FP16 组合，适用于支持这些节点的 Cu128 或 Cu130 环境。不需要安装 Nunchaku，也不要求先更换 Torch。H3 的 Qwen3-VL 文件仍是视频编码器，不是旧的 Qwen 图片生成模型。

优先使用现有 RTX 6000D 等大显存实例试镜；建议系统内存 128GB，以便模型卸载与加载。实际显存峰值和单镜耗时以试片为准。新实例六个模型约 113.3GB，另需输出与下载缓存空间；已有 H3 时新增 FLUX 三文件约 71.4GB。

## 安装与开机检查

将 `masterpiece_flight2_flux_h3_v3.zip` 上传到服务器 `/root`，确认文件在服务器后解压：

```bash
unzip -o /root/masterpiece_flight2_flux_h3_v3.zip -d /root/ComfyUI/custom_nodes/
```

重启 ComfyUI，然后在服务器终端执行只读检查；如果服务端口不是 6006，替换 URL：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/realism_install.py inspect --comfy-root /root/ComfyUI --url http://127.0.0.1:6006
```

报告包含 Python、Torch/CUDA、显卡、内存、数据盘真实路径、ffmpeg、模型文件及所需节点。无卡模式不会列出 GPU；实际推理前需回到 GPU 再检查。`present_unverified` 只代表文件存在，不代表校验通过。缺少 FLUX/H3 节点时先核对 ComfyUI 启动日志与版本，不要直接重装 Torch。

## 模型与下载

| 文件 | 目录 | 约大小 |
|---|---|---:|
| `flux2_dev_fp8mixed.safetensors` | `diffusion_models` | 35.5GB |
| `mistral_3_small_flux2_bf16.safetensors` | `text_encoders` | 35.6GB |
| `flux2-vae.safetensors` | `vae` | 336MB |
| `minimax_h3_fl2va_pruned_fp8_scaled.safetensors` | `diffusion_models` | 21GB |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | `text_encoders` | 15.7GB |
| `minimax_h3_video_vae_fp16.safetensors` | `vae` | 5.21GB |

来源：[Comfy-Org FLUX.2](https://huggingface.co/Comfy-Org/flux2-dev)、[Comfy-Org MiniMax H3](https://huggingface.co/Comfy-Org/MiniMax-H3)。安装工具保存了 2026-10-11 官方文件页的 SHA256，只有完整匹配才安装或跳过。若官方文件更新导致校验不匹配，停止并核对新版本，不绕过校验。

本次实例尚未开机，未做当前线路测速。先在同一实例无卡模式比较两个来源；已有 H3 可将 `--set all` 改为 `--set flux`：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/realism_install.py probe --set all --source modelscope
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/realism_install.py probe --set all --source huggingface
```

每个目标只读取约 4MB，要求 HTTP 206 和完整分段。低于 5MB/s、超时或返回网页都不能作为大文件下载依据。安装工具的 `download` 动作已实现：按当前测速选择来源后使用；它会再次测速、检查空间、通过 Hub 客户端续传，并在 SHA256 通过后移动到模型目录。此处不预先指定未测速的下载线路。模型目录必须落在 `/root/autodl-tmp` 数据盘；可用 `--model-root` 指定真实模型目录，但 ComfyUI 也须已配置该路径。

下载工具只需要 `modelscope` 或 `huggingface_hub` 中对应的一个客户端。中断时按 Ctrl+C；重跑同一动作续传，不能让两个进程写同一模型目录。结束后完整校验：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/realism_install.py verify --comfy-root /root/ComfyUI --set all
```

## 先共创分镜

使用 `masterpiece-flight-storyboard` skill，上传原画并描述大致怎么飞。Codex 会与你确定四镜路线、地形遮挡和接点，确认后输出包含所有图片与视频提示词的 schema v3 JSON。示例 `examples/starry_night_realism_v3.json` 仅供试流程，路线仍需要用户确认。

v3 包含五张写实关键帧 R1–R5、四段飞行、原画扩展和独立画作化。旧 v2 JSON 不能直接用于新图。只在第一阶段粘贴一次完整 JSON；`project_id` 另填，例如 `starry_realism_01`。

## 四个阶段

工作流在 `workflows/flux_h3_v3/`。按顺序导入，每阶段使用同一 `project_id`。

1. **01_flux_endpoints.json**：上传完整原画，粘贴 v3 JSON。生成横屏扩展画作 A 和三个写实 R5 候选。检查中心原画、两侧接缝，以及候选的材质和地标位置。选好后复制对应 `PreviewAny` 显示的 `approval_code`。
2. **02_h3_morph_pilot.json**：填项目 ID、候选编号与确认码。H3 生成 R5→A 的五秒画作化。查看 25%/50%/75% 中间画面，确认机位稳定、材质在变化、没有平面插画或透明重影。满意后复制 `morph_approval_code`。
3. **03_flux_flight_keyframes.json**：填项目 ID 和渐变确认码。从 R5 逆向生成 R4→R3→R2→R1，每步只参考相邻写实图。检查五帧中的地形、地标和遮挡接点，复制最后显示的 `frames_approval_code`。
4. **04_h3_full_flight.json**：填项目 ID 和五帧确认码，生成四段写实飞行；复用已确认渐变缓存，去除重复接点帧，再定格一秒。完整原画不会接入前四段视频。

确认码绑定实际素材内容。新图或新视频产生后旧码可能失效，不能用旧码批准没看过的结果。已经批准且素材没有改变时，可留空确认码读取现有批准状态。源图或分镜变化会重置该项目的批准与缓存；重做某张关键帧后，其前序关键帧与相应视频需重新生成/确认。一个项目一次只运行一个队列。

修改 `ArtV3Prompt.seed_base` 或 `variation` 可重试，种子自动送入采样器和缓存记录。更换模型或采样配置时另建项目并重新试片；本版验证基线是 FLUX 20 步/euler/guidance 4，H3 20 步/res_multistep/simple。

## 生成内容与验收

输出默认位于 `ComfyUI/output/masterpiece_flight2/<project_id>/`：

- `source.png`、`source_canvas.png`、`story_v3.json`、`manifest_v3.json` 保存来源、分镜和状态。
- `draft/` 保存原画扩展与候选；批准是 manifest 中的哈希记录，不会把第一张草稿自动视为通过。
- `cache/` 保存五段无损 uint8 NPY 帧，单段约 384MB，可跨队列复用。
- `diagnostics/` 保存每段原始 0/25/50/75/100% PNG 和目标尾帧。
- `final_720p.mp4`、`final_native.png` 为最终视频和编码前原生尾帧；原画中心像素在规范缩放后保持完整，MP4 有正常有损压缩。

模型按阶段使用；最后合成通过 ffmpeg 流式读取缓存，不把 640 帧拼成一个巨大浮点张量。画作化本身由 H3 生成，程序只做最后两帧校正。两侧接缝、三维连续性、停稳与材质变化仍需看实际结果，结构测试不代表画质通过。

本地检查：`python3 -m unittest discover -s masterpiece_flight2/tests -q`。本次本地环境未加载 FLUX/H3 大模型，AutoDL 实机推理与显存记录留待实例启动后完成。
