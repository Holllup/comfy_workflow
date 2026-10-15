# AutoDL 安装与使用：名画空间飞行

## 推荐：ChatGPT 定稿后一次运行

先在 ChatGPT 官网上传原画，使用 `PROMPT_ChatGPT编剧.md`：让它先提出三条不同的空间穿越概念，你选定和修改后发送“定稿 JSON”。再把 `workflows/00_one_pass_wan5b.json` 拖入 ComfyUI，上传同一张原画；把 JSON 粘进 `ArtPrepare` 的 `story_json`，设置一个**未用过**的 `project_id`，点击一次“运行”。这一个画布会先生成四张预设首帧，再串行生成四段 Wan 视频：每段末尾接入下一张预设首帧，截取这个实际尾帧给下一段，最后定格完整原画。输出为 `output/masterpiece_flight2/<project_id>/onepass_final_*.mp4`，各段为 `onepass_shot_01_*.mp4` 等。无需再导入其他 JSON。

Wan 5B 只接收首帧，接到预设下一帧时有约 8 帧渐变；要让转场好看，ChatGPT 的相邻图像提示词和视频提示词必须设计**同一个遮挡物或匹配轮廓**。这能保证接点图像连续，不能保证视频模型生成的中间空间完全符合剧本。RTX 4090D 24GB 尚未完成实机四镜测试，建议首次关注显存和第一镜输出。

## 1. 准备原画

- 《星月夜》：打开 [Wikimedia Commons 的高清文件页](https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg)，选择 **3,840 × 3,041** 的 JPEG 下载。原始超高分辨率文件约数百 MB，做 720p 视频无需下载它。把 JPEG 上传到 ComfyUI 的 `LoadImage` 节点，也上传同一张图给 ChatGPT。
- 换另一幅画：优先查作品的馆藏机构页面。可从 [大都会博物馆开放接口](https://metmuseum.github.io/) 搜索公共领域作品，确认作品记录的 `isPublicDomain=true` 且 `primaryImage` 不为空，再下载图像；也可使用提供明确许可的 Wikimedia Commons 文件页。保存作品页链接和图像来源。不要只凭搜索结果缩略图判断许可。
- 图像可为 JPEG、PNG 或 WebP。保留完整原画，不要先裁成 16:9；工作流会按原比例居中放进 1280×720，空出的两侧或上下用画作边缘的静态综合色填充。

## 2. 在 ChatGPT 审分镜

把原画和你下载图片时使用的文件页网址发给有识图能力的 ChatGPT 对话，发送 `PROMPT_ChatGPT编剧.md` 中的提示词。检查作品识别、馆藏来源、图像来源、历史事实、虚构部分、四张关键帧及四段飞行；有不满意的地方就在对话中修改。复制最终的纯 JSON。《星月夜》可以直接先用 `examples/starry_night_story.json` 试跑；其中村庄穿行被明确记为想象，依据见 [MoMA 作品页](https://www.moma.org/collection/works/79802)。

## 3. 安装节点与模型

本包内不含模型权重。推荐先在原 AutoDL RTX 4090D 24GB 实例上测试。**已有模型快速路径**复用该镜像的 Nunchaku Qwen 与 Wan 2.2 5B，不需要新下载模型；它使用镜像现有的 `TextEncodeQwenImageEditPlus`、`Wan22ImageToVideoLatent`、`CreateVideo` 和 `SaveVideo` 节点。**可选的 LTX 原版路径**才需要 `ConcatenateVideo`、`GetVideoComponents`、`LTXVAddGuide` 等较新的节点及额外模型。若选择 LTX 路径而这些节点缺失，先按[官方更新指南](https://docs.comfy.org/installation/update_comfyui)更新 ComfyUI。

将 `masterpiece_flight2_bundle.zip` 上传到 AutoDL 的 `/root/autodl-tmp/`，在终端中执行，按实际 ComfyUI 路径调整；若像当前实例一样上传到了 `/root/`，先 `cd /root` 再解压即可：

```bash
cd /root/autodl-tmp
unzip -o masterpiece_flight2_bundle.zip
python -m pip install -r masterpiece_flight2/requirements.txt
cp -a masterpiece_flight2 /root/autodl-tmp/ComfyUI/custom_nodes/
```

随后重启 ComfyUI，按下文选择对应工作流。**这个镜像的“缺少模型”弹窗里的“下载”按钮会让浏览器把文件下载到你自己的电脑；不会存进 AutoDL 数据盘。**若将来要装 LTX 路径，需在 Jupyter 终端下载到 `/root/autodl-tmp/ComfyUI/models/`。

### 已有模型快速路径：先用这套试跑

如果实例已有以下文件，可直接使用新提供的 Nunchaku + Wan 版本：

- `svdq-int4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors`、`qwen_2.5_vl_7b_fp8_scaled.safetensors`、`qwen_image_vae.safetensors`
- `wan2.2_ti2v_5B_fp16.safetensors`、`umt5_xxl_fp8_e4m3fn_scaled.safetensors`、`wan2.2_vae.safetensors`

这台 AutoDL 实例的文件位于 `/root/autodl-tmp/models/`，镜像需要通过模型路径配置让 ComfyUI 搜索该目录。按 **`01_keyframes_nunchaku.json` → `02_pilot_wan5b.json` → `03_full_wan5b.json`** 运行。如果 Nunchaku 节点的模型下拉框没有自动选中上述文件，就在下拉框中手动选它；不需要下载 19 GB 的 Qwen FP8 文件。此前网络中断产生的两个 0 字节文件会冒充可选模型，确认大小仍为 0 后可删除：

```bash
rm -f /root/autodl-tmp/ComfyUI/models/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors
rm -f /root/autodl-tmp/ComfyUI/models/loras/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors
```

Wan 2.2 5B 是**首帧驱动**的视频模型，不能像 LTX-2.5 那样直接接收尾帧。[ComfyUI 的 Wan 节点定义](https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_wan.py)只提供 `start_image`。快速路径把每段生成的最后 8 帧渐变到下一张已选关键帧，强制输出 1280×720 并保持原画定格；渐变可能比 LTX 首尾帧原生生成更明显。

### 可选：另装官方 Qwen FP8 + LTX-2.5

| 阶段 | 所需模型 | 来源与目录 |
| --- | --- | --- |
| 关键帧 | Qwen-Image-Edit-2509 FP8、Qwen 2.5 VL 7B FP8 文本编码器、Qwen Image VAE、2509 Lightning 4-step LoRA | [ComfyUI 官方模板](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_edit_2509.json)；分别放入 `models/diffusion_models/`、`models/text_encoders/`、`models/vae/`、`models/loras/` |
| 视频 | LTX-2.5 distilled Comfy int8 transformer、Gemma4 12B Comfy int8 文本编码器、LTX-2.5 视频和音频 VAE | [ComfyUI 官方首尾帧模板](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_ltx2_5_flf2v.json)；分别放入 `models/diffusion_models/`、`models/text_encoders/`、`models/vae/` |

工作流已关闭 LTX 的 `prompt_enhance`。额外的 Gemma4 E2B 提示词增强模型不必优先下载；如果 ComfyUI 仍把它显示为缺失，再按模板提示安装。LTX-2.5 权重按其[模型许可](https://huggingface.co/Lightricks/LTX-2.5)使用。

手动下载时，文件名必须与工作流模板完全一致：

- Qwen：`qwen_image_edit_2509_fp8_e4m3fn.safetensors`、`qwen_2.5_vl_7b_fp8_scaled.safetensors`、`qwen_image_vae.safetensors`、`Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors`。官方模板的 [Model links](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_qwen_image_edit_2509.json) 给出了各文件下载地址。
- LTX：`ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors`、`gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors`、`ltx-2.5-video-vae-bf16.safetensors`、`ltx-2.5-audio-vae-bf16.safetensors`。下载地址见 [首尾帧模板的 Model links](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_ltx2_5_flf2v.json)。

当前《星月夜》关键帧弹窗若只提示缺 **19.03 GB Qwen 模型**和 **810 MB LoRA**，在 **Jupyter 终端**运行以下两条下载命令；`wget -c` 可在网络中断后重运行来续传：

```bash
model_root=/root/autodl-tmp/ComfyUI/models
mkdir -p "$model_root/diffusion_models" "$model_root/loras"
wget -c -O "$model_root/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" 'https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors'
wget -c -O "$model_root/loras/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors" 'https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors'
ls -lh "$model_root/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors" "$model_root/loras/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors"
```

若日后导入视频工作流时提示缺 LTX 模型，也在 Jupyter 终端下载到同一数据盘目录：

```bash
model_root=/root/autodl-tmp/ComfyUI/models
mkdir -p "$model_root/diffusion_models" "$model_root/text_encoders" "$model_root/vae"
wget -c -O "$model_root/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors" 'https://huggingface.co/Lightricks/LTX-2.5/resolve/main/diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors'
wget -c -O "$model_root/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors" 'https://huggingface.co/Lightricks/LTX-2.5/resolve/main/text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors'
wget -c -O "$model_root/vae/ltx-2.5-video-vae-bf16.safetensors" 'https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/ltx-2.5-video-vae-bf16.safetensors'
wget -c -O "$model_root/vae/ltx-2.5-audio-vae-bf16.safetensors" 'https://huggingface.co/Lightricks/LTX-2.5/resolve/main/vae/ltx-2.5-audio-vae-bf16.safetensors'
```

下载完成后检查文件大小，避免把网络错误页当成模型文件；再刷新 ComfyUI 的模型列表或重启。若 Hugging Face 网络不可达，先不要运行工作流，把终端错误发来再换下载源。

## 4. 第一阶段：生成并挑选四张关键帧

1. 已有模型快速路径打开 `01_keyframes_nunchaku.json`；另装官方模型才打开 `01_keyframes.json`。在 **上传原画** 节点选图，在 `ArtPrepare` 节点设置只含英文字母、数字、`_` 或 `-` 的 `project_id`，把审定后的 JSON 粘进 `story_json`。同一作品的一次分镜使用同一个项目 ID；换原画或改分镜时改用新 ID。
2. 点击运行。四张图从靠近原画的 **04** 开始逆向生成到最远的 **01**；画布上的预览和输出目录都能检查。第一版工作流固定 1280×720。
3. 输出在 `/root/autodl-tmp/ComfyUI/output/masterpiece_flight2/<project_id>/`。`draft/frame_01.png` 至 `frame_04.png` 是最新生成图，`approved/` 下是视频阶段会读取的四张选定图。第一次生成会自动把草稿复制到 `approved/`；以后重跑只刷新 `draft/`，不会覆盖你已确认的图片。若想采用新草稿，手动把对应 `draft/frame_XX.png` 复制到 `approved/frame_XX.png`；也可以放入自己修过的 1280×720 PNG。
4. 检查四张图的地标、画风、飞行方向是否能顺次接起来，尤其 `frame_04` 是否接近原画视角。`ending.png` 是完整原画的横屏尾帧，`source.png` 是上传的原画。

## 5. 第二阶段：先试一镜，再出成片

1. 已有模型快速路径导入 `02_pilot_wan5b.json`；LTX 路径导入 `02_pilot_5s.json`。把 `ArtLoadApproved` 的 `project_id` 改为第一阶段的 ID。它只生成 **frame_04 → 原画** 的五秒末镜，再加一秒原画定格。Wan 内部生成 1280×704，衔接节点统一输出 1280×720、24 fps。
2. 同时开一个终端运行 `nvidia-smi -l 1`，记录显存峰值和单镜耗时，检查有无 OOM、闪烁、构图跳变、画风漂移或尾帧明显变形。Wan 试镜结果为项目目录的 `wan_pilot_*.mp4`；LTX 为 `pilot_*.mp4`。图像输入和参数记录在 `render_settings.json`。
3. 单镜稳定后，已有模型快速路径导入 `03_full_wan5b.json`；LTX 路径导入 `03_full_20s.json`。设置同一 ID 并运行。Wan 成片与分镜文件为 `wan_final_*.mp4`、`wan_shot_01_*.mp4` 等；LTX 成片为 `final_*.mp4`、`shot_01_*.mp4` 等。四段每段约五秒，再加一秒定格，最终时长约 21 秒，均为无声 MP4。
4. 若在 4090D 上 OOM，可**仅在试镜工作流**把 Wan 潜空间的 1280×704 或 LTX 节点的 1280×720 改成 960×544 做诊断，同时记录失败位置；最终尾帧仍由原画生成。若目标规格持续失败，换 48GB 显卡，不把低分辨率试镜当作最终交付。

## 检查与限制

- 观看四段接点是否像连续飞行。首尾帧约束和遮挡提示能改善连贯性，但生成模型不能保证真正无缝的一镜到底；不满意时先改关键帧或分镜，再重跑对应项目。
- 最后 1 秒直接来自 `ending.png`，不经 AI 重画。MP4 的有损编码仍可能造成轻微颜色和像素差异；要核对原图请看 `source.png` 和 `ending.png`。
- 当前不在画面叠加“AI 想象”字样，但 `story.json` 明确保存史实与虚构信息。若日后公开发布，请在发布文案中说明想象重构和图像来源。
- 本包已完成本地结构与文件流程测试；AutoDL 上的真实显存、速度和画面效果需按上述步骤试跑后确认。
