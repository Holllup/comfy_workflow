# 名画空间飞行 · ComfyUI 工作流

新增 **FLUX.2 dev 写实飞行 → MiniMax H3 画作化（schema v3）**，采用四阶段审核流程，完整说明见 [FLUX＋H3 安装与使用](README_FLUX_H3.md)。新版图在 `workflows/flux_h3_v3/`，使用 `starry_night_realism_v3.json` 字段结构；下面的旧 v2 油画空间流程继续使用旧分镜。

MiniMax H3 的 Cu130/INT8 和 Cu128/FP8 默认工作流已改为空间版。**先检查现有 PyTorch/CUDA 版本和下载源速度，再选单镜工作流**：

1. **H3 一键完整工作流**：`workflows/00_one_pass_minimax_h3.json` 对应 Cu130；`workflows/00_one_pass_minimax_h3_cu128.json` 对应 Cu128。上传原画、粘贴带有 `"conditioning_mode": "spatial_style_seed"` 的空间版四镜分镜 JSON、点击一次运行；四张关键帧逆向生成，四镜用 H3 首尾帧约束顺序生成，最后接未经 AI 重画的原画定格。
2. **H3 单镜试跑**：选择同后缀的 `00_pilot_minimax_h3*.json`。它一次点击生成四张关键帧及第一镜，先验证运行环境、显存、画风和山肩接点。
3. **原 Wan 5B 一键工作流**：`workflows/00_one_pass_wan5b.json` 保留作旧实例或低成本草稿。另有旧分阶段流程可先审关键帧。

### 避免原画被复制成固定背景

旧 H3 图在生成关键帧时反复输入完整原画及大块留边，可能让它成为远处不动的矩形。现在 Cu128/Cu130 默认图及 `*_spatial_cu128.json` 别名都使用空间接线，并配合 `examples/starry_night_story_spatial.json`。关键帧从原画的**抽象色彩种子**逆向生成，KF1–KF3 不再接入完整原画；画作笔触由分镜文字描述。上传的完整原画只用于第四镜终点与最后 24 帧静止。对应可复用编剧提示词见 [空间版提示词](PROMPT_ChatGPT%E7%BC%96%E5%89%A7_%E7%A9%BA%E9%97%B4%E7%89%88.md)。

新版 `ArtFrameText` 会校验空间分镜标记，防止把仍要求“第二张图是原画”的旧分镜误贴进新接线。旧实例需上传新版安装包并重启 ComfyUI；仅导入新 JSON 会缺节点或沿用旧提示词。先比较 `draft/frame_01.png`～`frame_04.png` 与视频里的视差。2D 模型仍不能保证真正的三维几何；第四镜的原画尾帧条件也可能使它较早收束为平面，需单独检查中间帧。

在 AutoDL 上，将新生成的 `masterpiece_flight2_spatial_bundle.zip` 上传到 `/root`，运行 `unzip -o /root/masterpiece_flight2_spatial_bundle.zip -d /root/ComfyUI/custom_nodes/`，再重启 ComfyUI。导入 `00_one_pass_minimax_h3_cu128.json`，上传原画，粘贴 `examples/starry_night_story_spatial.json` 的完整内容到 `ArtPrepare.story_json`，并使用新的 `project_id`。已有六个模型无需重下。若第四镜也表现为平面收束，需查看视频 25%/50%/75% 帧和 `diagnostics/shot_04_raw_last.png` 再调整。

新实例逐条操作见 [MiniMax H3 中文说明](README_H3_%E6%96%B0%E5%AE%9E%E4%BE%8B.md)；旧 Wan/LTX 流程见 [原安装说明](README_%E5%AE%89%E8%A3%85.md)。当前 H3 的可复用编剧提示词在 [空间版提示词](PROMPT_ChatGPT%E7%BC%96%E5%89%A7_%E7%A9%BA%E9%97%B4%E7%89%88.md)；《星月夜》JSON 演示山肩、教堂和星晕接点，其他画作应设计自己的路线。

首版支持有可进入空间的风景、城市、建筑和室内场景画。作品识别和史料核对由 ChatGPT 完成，你审稿后再粘贴 JSON；ComfyUI 不调用 OpenAI API。完整原画保存在项目目录的 `source.png`，横屏尾帧保存在 `ending.png`，尾帧没有经过 AI 重画。成片 MP4 编码会造成正常的像素压缩。

本地检查：从工作区根目录运行 `python3 -m unittest discover -s masterpiece_flight2/tests -q`。本地没有 NVIDIA GPU 或 AutoDL 连接时，这些检查不代表已完成模型推理。
