# H3 实例交接与小猫 Vlog 项目约束

本目录是新的十镜小猫 Vlog 项目。下一个 Codex 窗口先读本文件，再读本目录 README 与测试。现有 `../cat/` 是独立的六镜 Wan 5B 草稿；`../masterpiece_flight2/` 是名画飞行工作流。不要把它们的 JSON 字段、节点或模型路径当作本项目已部署的代码。

## 2026-10-08 首帧模型改版：本地完成，云端尚未部署

用户实测旧版 Qwen-Image-Edit-2509 FP4 Lightning 的首帧，反馈它没有体现提示词且画面单调。核查旧图为4步、CFG1、参考猫照片贴在灰色画布上；舞蹈社十镜前九镜又反复使用同一排练室、正面全身猫和蓝色地标，长提示词本身未带来视觉变化。旧版 AutoDL 实例截图显示 RTX 6000D 正在运行，`check_runtime.py` 对旧图返回 `OK ... 175 nodes`；这只证明旧节点可加载，**不证明首帧质量或十镜 H3 运行成功**。截图也显示音频 VAE SHA256 已验证、FFmpeg/FFprobe 后续已安装。Codex 没有远程操作实例或 GPU。

本地新图保持 `schema_version: 3`、两阶段十镜、H3 175帧/24fps/20步声画和原文件名，但首帧链路改为 **JoyAI-Image-Edit-Plus BF16**：三张真实角色照片直接作为参考，空白1344×768潜空间、40步、CFG4、Euler/normal。单角色的第三张重复主角照片，不能混入未出场室友。官方 Apache-2.0 模型需要新增约50.3 GB 权重；官方 ComfyUI 示例与文件SHA记录见 `references/joyai_edit_plus_official.json`、`scripts/ensure_joyai_models.py` 和 `README.md`。旧 Qwen 权重仍可留在数据盘作为历史，不被新图引用。首帧指纹包含新后端版本，旧审图不可复用，建议新 run_id。**新 JoyAI 图没有在 AutoDL 做节点检查、下载或 GPU 质量验收；先检查运行中的 ComfyUI 是否支持 `TextEncodeJoyImageEdit`，再考虑在无卡模式下载。**

舞蹈社默认分镜 `storyboards/dance_club_audition_story.json` 已重新区分十张首帧的机位、景别、前后景、神态和道具关系；剧本事件与声画结构保留。`cat-vlog-storyboard` 项目源 Skill 与官网编剧提示词新增首帧视觉变化审稿规则。用户问到 SD 系列：SDXL+IP-Adapter/猫 LoRA 作为可选路线，但需要额外训练或控制节点；当前替代选择是原生多图编辑的 JoyAI Plus，不声称尚未实测的效果优于所有 SD 模型。旧版 Qwen 相关描述在下文是历史记录，以本节及 README 的当前交付为准。

## 这台 AutoDL 实例：已证实与待确认

以下来自用户提供的终端及 ComfyUI 截图，时间为 2026-10-04 至 2026-10-05；**不是当前实例的实时查询**。

| 项目 | 已有证据 |
| --- | --- |
| GPU/主机 | RTX 6000D 84 GB、约 110 GB 内存、单 GPU；曾切无卡模式完成下载，之后在 ComfyUI 进入 H3 第一镜 20 步采样。当前 GPU 是否仍开机须重新查询。 |
| Python/Torch | Python 3.12、`torch 2.8.0+cu128`，`torch.version.cuda == 12.8`。不要为了本项目默认重装 Torch。 |
| ComfyUI | `/root/ComfyUI` 位于系统盘；`/root/ComfyUI/models` 软链接指向数据盘 `/root/autodl-tmp/ComfyUI-models`。数据盘当时 200 GB，剩余容量须重查。 |
| 自定义节点 | `masterpiece_flight2` 包已解压到 `/root/ComfyUI/custom_nodes/`；Nunchaku Qwen 节点已足以完成关键帧并进入 H3 视频采样。最新用户终端截图已确认 Nunchaku 1.2.1+cu12.8torch2.8 已安装。 |
| 已见运行阶段 | ComfyUI 中 `00_one_pass_minimax_h3_cu128` 第一镜 H3 采样曾到约 35%；**没有收到四镜全部成功或最终 MP4 完成的证据**。不得写成已实机验收。 |

截图显示以下六个权重在 `/root/ComfyUI/models` 的检查结果均为 `OK`，通过软链接实际位于数据盘：

1. `diffusion_models/minimax_h3_fl2va_pruned_fp8_scaled.safetensors`
2. `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
3. `vae/minimax_h3_video_vae_fp16.safetensors`
4. `diffusion_models/svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors`
5. `clip/qwen_2.5_vl_7b_fp8_scaled.safetensors`
6. `vae/qwen_image_vae.safetensors`

本项目使用 H3 原生环境音。最新用户终端截图显示 `vae/minimax_h3_audio_vae_fp32.safetensors` 已通过脚本下载，并输出 **`READY ... SHA256 verified`**；实际位于数据盘软链接后的模型目录。此前六个权重均显示 `OK`。若参考图生成的角色仍持续漂移，本版不下载 H3 Ref2VA 约 21 GB 权重、不训练猫 LoRA、不启用 Turbo。

## 本地已交付，不等于云端已部署

当前本地目录包含 `cat_vlog_h3_bundle.zip`、一份两阶段十镜 ComfyUI UI JSON、主角六视角、室友四视角和原参考拼图、十镜示例、ChatGPT 编剧提示词、自定义节点、音频 VAE 下载脚本和 ComfyUI 节点核对脚本。自定义节点独立于 `masterpiece_flight2`，输出默认在数据盘 `/root/autodl-tmp/cat_vlog_h3/output`。本地 49 项测试以及 JSON 连线、节点输入检查已通过；**没有 AutoDL 当前实例的接入与真实 175 帧音视频推理结果**。用户目前不需要 Codex 远程部署、开机或使用 GPU 测试；只交付本地文件。实施顺序和文件名见本目录 `README.md`。

在实例上重新确认，而不是依赖本文件的旧状态：

```bash
python3 --version
python3 -c 'import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())'
python3 -m pip show nunchaku
nvidia-smi
readlink -f /root/ComfyUI/models
df -h / /root/autodl-tmp
ls -lh /root/ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors
```

## 下载部署经验与现有 Skill

- `../masterpiece_flight2/AGENTS.md` 是**下载避坑记录**，不是 Codex Skill：它记录了 PyTorch CDN 在付费 GPU 上约 0.1 MB/s、ModelScope 约 12 MB/s、GitHub Release 内置代理约 0.46 MB/s、公共代理经校验后约 9.6 MiB/s 的实际经历。给下载命令前须做有界测速、检查数据盘位置、支持续传并核对哈希；这些历史速度不能当作今天的保证。
- 个人 Codex Skill `~/.codex/skills/masterpiece-flight-storyboard/` 专用于**名画四镜**分镜 JSON，不应直接用于小猫十镜。
- 用户于 2026-10-07 确认创建小猫 Skill：`~/.codex/skills/cat-vlog-storyboard/`，项目源文件为 `skills/cat-vlog-storyboard/`。AI 宠物 Vlog 脚本／分镜请求可自动调用，也可用 `$cat-vlog-storyboard`；先追问素材和拟人边界，再导演审稿、设计前两镜钩子，最后输出经真实项目校验的十镜 JSON。计划模式只讨论与预览，允许写文件时保存至本项目 `storyboards/`。Skill 的五项 CLI 测试使用真实 `core.py` 检查示例、无效数量、缺失首帧和不受支持字段；创作流程的本地人工走查记录在 `tests/storyboard_skill_review.md`，不是模型生成质量验收。
- 本轮已确定保持**固定十镜、每镜约 7.29 秒**；更多场景另列备选，不写虚假的可变时长字段。钩子、共鸣和讨论点由画面与本期选择的原生声画表达；可有对白、演唱和音乐。Skill 不授权远程部署、开机、下载或使用 GPU。
- [AutoDL 学术网络说明](https://www.autodl.com/docs/network_turbo/)提示内置代理可能影响普通网络。模型优先从可核对的官方 ModelScope 仓库取得；第三方传输代理只在测速更快且有官方 SHA256 可核对时用于二进制文件。

## 当前项目选择

- 同一只狸花白猫，固定复用工作区根目录的两张 `Weixin Image_20261005231616_35694_55.png` 与 `Weixin Image_20261005231617_35695_55.png`。第一张含正、侧、背三视图，第二张含脸部和左右 45° 角；先提取不带文字的参考图，并保留原件。棕灰虎斑与白色脸部、胸腹和四爪、粉鼻、环纹尾巴须稳定。首版不训练 LoRA。
- ChatGPT 官网一次对话规划十镜，用户审稿后手动粘贴一份十镜 JSON；ComfyUI 不接付费编剧 API。十镜共享一条松散主线，画面互不接帧；跟拍、自拍感和猫主观视角由分镜选择，动作轻度拟人但保持正常猫身体结构。
- 16:9 横屏、1344×768 H3 原生画布、24 fps、每镜 175 帧（约 7.29 秒）、基础模式 20 步。阶段1每镜由 Qwen 生成一张首帧；审查通过后阶段2用 H3 FL2VA 仅首帧生成声画；十条画布分支按一张 GPU 的显存约束顺序推理。
- 环境声、对白、演唱和配乐按每镜 audio 配置由 H3 同步生成，已删除统一禁言禁乐。最终保存 10 张已审首帧、十个带音频的单镜 MP4、一个 1280×720 合成 MP4（约 72.9 秒）、JSON、角色参考和运行清单到数据盘。
- 2026-10-07 用户要求删除单镜试跑图，已删除。唯一正式图先出十张首帧供人工审查，再由用户在同一 run_id 下切到视频阶段点击 Run。首帧保存后写入哈希，阶段2从磁盘读取，失配或未审查时拒绝生成；阶段1通过原生 lazy evaluation 不请求 H3，阶段2不请求 Qwen。不能把本地结构检查说成 AutoDL 推理成功，也不因失败默默降低分辨率或换模型。

## 2026-10-07 首帧审查改版

唯一工作流仍保留原文件名 `01_one_pass_10x7s_h3_cu128.json`，内容已改为两阶段。`CatH3Story.phase` 默认 `1_生成首帧并审查`；审图通过后选 `2_已审查_生成视频` 再点击 Run。`CatH3References` 会显示角色库中的实际照片；`CatH3Stage` 展示编号总览和十张原图。某镜不满意时在阶段1增加该镜 `variation` 后重新运行。生成照片一直真实接入 Qwen，此前问题是没有可见预览。

首次首帧审查改版曾使用 schema_version 2；目前已升级到下述 v3。Skill、官网编剧提示词、示例和校验脚本同步。当前仍建议先使用参考图约束，暂不训练 LoRA；这并不保证模型生成的猫身份完全稳定。

## 2026-10-07 通用双角色与原生声画改版（当前接口）

- schema_version 3 使用 characters／shots.cast／shots.audio。每镜1–2个可见角色；主要角色两个视角、第二角色一个视角，真实连接Qwen的三路图片。只有画外声音的角色 reference_set 为 null，不进入图片。
- 角色库 assets/reference_sets.json：protagonist 保留原六视角，roommate 使用根目录 Weixin Image_20261007211555_35901_55.png 无文字裁切出的正、侧、背、脸部四视角。原拼图一并保存。换角色以数据注册，不用改主题专用节点。
- 同一个 H3 节点原生生成自然声音、中文对白、演唱及音乐。字段对应官方 I2VA 提示词结构，台词／歌词逐字进入 <d> 标签，说话角色有稳定声音描述。没有外部TTS、音乐混入节点或付费API。跨镜精确同曲、声纹和卡点不作保证。
- 首帧条件指纹只包含该镜图片指令、可见角色、实际参考文件和图像种子。只改声音／视频动作保留审图；改变首帧或照片需重审受影响图片。阶段1从磁盘复用未变图片，阶段2仍不调用Qwen。实际模型提示词保存到输出 prompts/。
- 已批准舞蹈招新剧本保存为 storyboards/dance_club_audition_story.json，并作为默认工作流输入；examples/rainy_day_cat_story.json 也迁移到v3，证明自然日常可用同一图。
- v1/v2不再静默自动迁移：校验器清楚提示升级，由Skill逐句拆分旧自由音频文字，保持剧情、台词和音乐意图；详细映射在Skill字段说明中。旧版图片审查记录需重新生成审查。
- 当前仍只交付本地文件和测试，不远程操作AutoDL、不启动GPU。安装新版包后必须重启ComfyUI并重新导入节点图。

## 音频 VAE 下载故障修复（最新用户截图）

用户截图确认 Python 3.12.3、Torch 2.8.0+cu128、Nunchaku 1.2.1+cu12.8torch2.8，六个原模型为OK。FFmpeg/ffprobe 当时为None，APT候选来自 repo.huaweicloud.com/ubuntu；尚无安装完成的截图。

旧下载脚本测 ModelScope 文件URL后又转到SDK请求，用户中断时调用栈停在 getaddrinfo；后续测速从2.73降至0.37 MB/s。5MB/s门槛对这个605MB文件过高，但不应一路降低门槛掩盖差线路。

当前 ensure_models.py 用 curl 对 ModelScope/HF-Mirror/Hugging Face 三条文件URL做并行有界测速（各4MB/20秒），默认最低2MB/s。通过后直接用同一个URL续传，连接超时10秒、持续低速25秒会暂停；保留.part文件。校验大小和官方SHA256后才原子安装。无需ModelScope SDK，不改变既有Torch。用户已把修复脚本上传到服务器并运行，最新截图显示 ModelScope 线路测速约3.22 MB/s，完整文件下载用约36秒，最终显示 `READY ... SHA256 verified`。这些速度只代表当时线路，不代表今后稳定速度。Codex 未远程执行，也尚无小猫工作流实际GPU推理结果。
