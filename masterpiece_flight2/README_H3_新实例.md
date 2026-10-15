# MiniMax H3 一键四镜：新 AutoDL 实例操作

## 1. 先省租金，再检查环境

当前 RTX 6000D 实例已经关机。按 [AutoDL 无卡模式说明](https://www.autodl.com/docs/save_money/)把**同一实例**以无卡模式开机，用它做环境检查与大模型下载；系统盘和 200GB 数据盘都会保留。无卡模式只有 0.5 核、2GB 内存，下载用流式传输，实际推理仍须重新开 GPU。无卡会释放 GPU，回来时若已被别人租用，需要等待或迁移。不要克隆旧数据盘到另一实例。

在 Jupyter 终端先执行**只读检查**，此时不要安装 Torch，也不要下载大模型：

```bash
python3 --version
python3 -c 'import torch; print(torch.__version__, torch.version.cuda)'
df -h / /root/autodl-tmp
```

根据实际输出选择唯一一套工作流及权重：

| 已装 PyTorch | 工作流 | H3 权重 | 下一步 |
| --- | --- | --- | --- |
| `2.8.x`、`12.8` | `00_pilot_minimax_h3_cu128.json` → `00_one_pass_minimax_h3_cu128.json` | FP8 模型 + FP16 视频 VAE | **先不重装 PyTorch**，用现有环境试镜。 |
| `2.10.x`、`13.0` | `00_pilot_minimax_h3.json` → `00_one_pass_minimax_h3.json` | INT8 ConvRot 模型与 VAE | 保留已装环境。 |
| 其他或导入失败 | 暂不导入工作流 | 暂不下载 | 把版本和第一条报错发来，选匹配组合。 |

Cu128/FP8 是免重装的**验证路线**，尚未在你的实例上跑过真实视频；如果画质或速度不够，再考虑 Cu130/INT8。官方说明 H3 原生首尾帧、1344×768、24fps，且 [INT8 ConvRot 优先配 cu130](https://huggingface.co/Comfy-Org/MiniMax-H3)。四镜每镜 124 帧，加 24 帧原画，最终约 21.67 秒。

**只有确定需要升级 Cu130 时**，先运行本包 `network_preflight.py --source pytorch --min-mbps 5`。若报告 `TOO SLOW`，不要执行数 GB 的 PyTorch 安装。若速度达标，再把 pip 缓存指向数据盘并按[PyTorch 官方版本命令](https://pytorch.org/get-started/previous-versions/)安装匹配包；安装结束重新执行上述版本检查。本次直接从 `download.pytorch.org` 开始下载，在这台机器上 642MB 耗时约 58 分钟，今后不得跳过测速。

## 2. ComfyUI 和本项目

社区镜像中的 ComfyUI 位于 **`/root/ComfyUI` 系统盘**，大文件要去 `/root/autodl-tmp` 数据盘。**不用再次克隆 ComfyUI，也不要先升级 PyTorch。**当前镜像已有 H3 相关脚本，先用现有 ComfyUI 安装本项目并检查节点；若缺少 H3 原生节点，再针对实际报错更新 ComfyUI。官方 H3 基础节点需要 0.30.0 或更新版本。

你现在换用的 **H3 CUDA128 社区镜像**另有预设：其 `README.md` 说明 `/root/ComfyUI/models` 已软链接到 `/root/autodl-tmp/ComfyUI-models`。先用 `ls -ld /root/ComfyUI/models` 核对。确认是该软链接后，下面 Cu128 下载命令**不需要**另设 `--model-root`；模型会自动写到数据盘。镜像自带 `minimax_dl.sh`（aria2 多线程），但执行前要核对其具体权重文件名；本项目下载脚本只取与本工作流相符的六个文件。

先确认大模型目录确实落在数据盘：

```bash
readlink -f /root/ComfyUI/models
df -h /root/autodl-tmp
```

第一条应显示 `/root/autodl-tmp/ComfyUI-models`；不符合时暂停，避免把 65GB 权重写进 30GB 系统盘。安装 Python 包前设置 `export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache`，避免缓存占满系统盘。
该镜像的软链接目标目录可能还未创建。确认路径正确后先运行 `mkdir -p /root/autodl-tmp/ComfyUI-models`；已安装的旧版下载脚本在该目录缺失时会报 `FileExistsError: /root/ComfyUI/models`。新版脚本会自动初始化，但手动创建同样安全。

把本机的 **`masterpiece_flight2_h3_bundle.zip`** 用 Jupyter 左侧上传按钮传到服务器根目录 `/root`。终端里确认 `ls -lh /root/masterpiece_flight2_h3_bundle.zip` 后执行：

```bash
unzip -o /root/masterpiece_flight2_h3_bundle.zip -d /root/ComfyUI/custom_nodes/
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
python3 -m pip install -r /root/ComfyUI/custom_nodes/masterpiece_flight2/requirements.txt
```

旧对话里 ZIP 放在 `/root`、终端却位于 `/root/autodl-tmp`，导致 `unzip` 报找不到文件。上面的命令使用绝对路径。ZIP 和小型自定义节点放在系统盘；**大模型放在数据盘**。

解压后即可先做 PyTorch 下载源测速；**仅当需要升级且测速通过时**，才在无卡模式运行安装命令：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/network_preflight.py --source pytorch --min-mbps 5
```

测速只读取约 8MB、最多约 20 秒，不会下载整包。`TOO SLOW` 或请求失败意味着停止该来源；Cu128 版本可先跳过这项升级，按第一节表格继续。

## 3. 仍在无卡模式时安装 Nunchaku

模型下载不需要 Nunchaku。六个模型都显示 `OK` 后，继续在无卡模式安装 Nunchaku，避免占用 RTX 6000D 等待网络。本图的关键帧使用 Qwen-Image-Edit-2509 Lightning；RTX 6000D Blackwell 使用 **Nunchaku FP4**。wheel 必须与实际 Python/PyTorch/CUDA 匹配：[Nunchaku 官方精度建议](https://nunchaku.tech/docs/nunchaku/faq/model.html)。

当前实例的 GitHub 直连/内置代理测速只有约 0.46 MB/s，已改用 [AutoDL 推荐的公共代理入口](https://www.autodl.com/docs/network_turbo/)所列 `ghfast.top`，4 MB 分段样本约 11.5 MB/s。wheel 已下载到数据盘时，先核对[官方发布 SHA256](https://github.com/nunchux-ai/nunchaku/releases/expanded_assets/v1.2.1)，再从本地文件安装。校验不过绝不安装：

```bash
echo 'e0cfe5a034bc2607ba78fe4d037ba1a90396e8c89b4cdce36146706c6cd4a54c  /root/autodl-tmp/wheels/nunchaku-1.2.1+cu12.8torch2.8-cp312-cp312-linux_x86_64.whl' | sha256sum -c -
python3 -m pip install --no-deps '/root/autodl-tmp/wheels/nunchaku-1.2.1+cu12.8torch2.8-cp312-cp312-linux_x86_64.whl'
```

安装匹配的 [ComfyUI-nunchaku v1.2.1](https://github.com/nunchux-ai/ComfyUI-nunchaku/releases/tag/v1.2.1) 插件。通过公共代理下载的 Git 仓库需核对官方发布页的 commit `e9f7eec`。若代理不支持 Git 克隆，暂停并改用官方仓库浅克隆；不要直接安装来源不明的插件代码：

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY -u all_proxy -u ALL_PROXY git clone --depth 1 --branch v1.2.1 'https://ghfast.top/https://github.com/nunchux-ai/ComfyUI-nunchaku.git' /root/ComfyUI/custom_nodes/ComfyUI-nunchaku
git -C /root/ComfyUI/custom_nodes/ComfyUI-nunchaku rev-parse --short HEAD
```

第二行应以 `e9f7eec` 开头。先安装本工作流 Qwen 节点的插件依赖；完整依赖中另含 PuLID 的 `insightface`，在 2GB 无卡环境编译可能很慢，故此处先跳过它：

```bash
export PIP_CACHE_DIR=/root/autodl-tmp/pip-cache
sed '/^insightface$/d' /root/ComfyUI/custom_nodes/ComfyUI-nunchaku/requirements.txt > /root/autodl-tmp/nunchaku-qwen-requirements.txt
printf 'torch==2.8.0+cu128\n' > /root/autodl-tmp/torch-pin.txt
python3 -m pip install -r /root/autodl-tmp/nunchaku-qwen-requirements.txt -c /root/autodl-tmp/torch-pin.txt
```

最后在无卡模式运行 `python3 -m pip show nunchaku` 和 `python3 -c 'import torch; print(torch.__version__, torch.version.cuda)'` 核对。`nunchaku` 的 GPU 导入与实际 Qwen 节点加载留到开 GPU 后验证；无卡时导入可能因为没有 CUDA 设备而失败。

## 4. 无卡模式先测速，再下载权重

**请在 Jupyter 终端运行以下命令；ComfyUI 弹窗的「下载」若触发浏览器下载，不会把文件放进服务器。** 安装下载工具：

```bash
python3 -m pip install 'modelscope>=1.20' 'huggingface_hub>=0.26'
```

先用最多少量字节测试 ModelScope 的实际下载速度：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/network_preflight.py --source modelscope --min-mbps 5
```

如果输出 `TOO SLOW`、请求失败或预计 65GB 耗时过长，**停止，别启动大文件下载**。若通过，按第一节查到的 CUDA 版本，**以下两条只执行一条**；下载脚本会再测速一次、自动拒绝低于 5MB/s 的来源。ModelScope 支持大文件分段续传与校验，[官方客户端说明](https://github.com/modelscope/modelscope_hub)。

已装 PyTorch 2.8/CUDA 12.8，使用 Cu128/FP8 权重：

```bash
MODELSCOPE_DOWNLOAD_PARALLEL_WORKERS=4 python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/download_h3_models.py --comfy-root /root/ComfyUI --runtime cu128 --set all --source modelscope
```

已装 PyTorch 2.10/CUDA 13.0，使用 Cu130/INT8 权重：

```bash
MODELSCOPE_DOWNLOAD_PARALLEL_WORKERS=4 python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/download_h3_models.py --comfy-root /root/ComfyUI --model-root /root/autodl-tmp/models --link-into-comfy --runtime cu130 --set all --source modelscope
```

无卡模式只有 2GB 内存；若并行下载内存不足，把 `WORKERS=4` 改为 `WORKERS=2` 重跑，已完整文件会跳过。若 ModelScope 失败，先运行 `network_preflight.py --source huggingface --min-mbps 5`；确认 Hugging Face 镜像或代理速度可用后再把下载命令最后一项改为 `--source huggingface`。不要猜测来源一定快。查看结果时也带同一个 `--runtime`：

```bash
python3 /root/ComfyUI/custom_nodes/masterpiece_flight2/scripts/download_h3_models.py --comfy-root /root/ComfyUI --runtime cu128 --set all --check-only
```

Cu130 用户把上面 `cu128` 改成 `cu130`。`--check-only` 六项都显示 `OK` 才继续。Cu130 六权重约 62GB，Cu128 因视频 VAE 使用 FP16 约 65GB。在当前 H3 CUDA128 镜像中，Cu128 下载会经 `/root/ComfyUI/models` 软链接写入数据盘 `/root/autodl-tmp/ComfyUI-models`；**不会把大权重写进 30GB 系统盘**，也不会下载 525GB 全仓库。[H3 模型目录](https://huggingface.co/Comfy-Org/MiniMax-H3/tree/main)

## 5. 回到 GPU，单镜测试后跑全片

六项模型检查和第三节的 Nunchaku 安装都通过后，关掉无卡模式，以 GPU 正常开机。在 GPU 终端先运行 `nvidia-smi` 及 `python3 -c 'import torch, nunchaku; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())'`。若 ComfyUI 未自动启动，可从已存在的目录运行：

```bash
cd /root/ComfyUI
python3 main.py --listen 0.0.0.0 --port 6006
```

AutoDL 控制台把端口 `6006` 配成自定义服务，再从网页打开 ComfyUI。长时间运行请用镜像自带启动器或 `screen`。若导入图时显示缺失 `MiniMaxH3ImageToVideo`，说明 ComfyUI 版本仍旧；若缺失 `NunchakuQwenImageDiTLoader`，检查 Nunchaku 安装及 ComfyUI 启动日志。

1. 按第一节表格导入匹配的单镜 JSON：Cu128 用 `00_pilot_minimax_h3_cu128.json`；Cu130 用 `00_pilot_minimax_h3.json`。在 `LoadImage / 上传原画` 选择完整《星月夜》图片；在 `ArtPrepare.story_json` 粘贴 `examples/starry_night_story_spatial.json` 的**整个 JSON 内容**，把 `project_id` 改成新的英文数字名，如 `starry_h3_spatial_pilot_01`。旧版 `starry_night_story.json` 会因仍要求原画参考图而被拒绝。点击一次运行；它先生成四张关键帧，再生成**第一镜**供检查。
2. 记录第一镜画风、飞行方向、山肩遮挡，以及日志里的耗时。另开终端可记录显存峰值：`nvidia-smi --query-gpu=timestamp,memory.used --format=csv -l 2 | tee /root/autodl-tmp/h3_vram.csv`。测试结束用 `Ctrl+C` 停止监控。
3. 试镜满意后导入匹配的四镜 JSON：Cu128 用 **`00_one_pass_minimax_h3_cu128.json`**；Cu130 用 **`00_one_pass_minimax_h3.json`**。重新选择原画并粘贴同一空间版分镜 JSON，使用新 ID（例如 `starry_h3_spatial_full_01`），点击一次运行。不同画作或修改后的分镜必须换 `project_id`。

输出在 `/root/ComfyUI/output/masterpiece_flight2/<project_id>/`：

- `h3_shot_01...mp4` 至 `h3_shot_04...mp4`：1344×768、24 fps、每段约 5.17 秒的无声原生片段。
- `h3_final...mp4`：缩放到 1280×720、24 fps，以每帧自身边缘填补两侧约 10 像素；末尾是同一原画画布的 24 帧静止。
- `source.png` 是上传原图的 PNG 副本；`ending.png` 是保持原画比例的 H3 规范画布；`story.json`、`manifest.json` 保存分镜与来源。
- `diagnostics/shot_XX_raw_last.png` 是 H3 原始尾帧；`shot_XX_bridged_last.png` 是精确接点帧；`shot_XX_target.png` 是目标关键帧，`shot_XX_gap.json` 记录平均像素差。该分数只用于发现明显硬融，最终仍需肉眼看片。

如果运行失败，请保留 ComfyUI **第一条报错**、完整节点名、`nvidia-smi` 峰值及单镜耗时。未在你的新 AutoDL 实例上完成实际推理前，不能保证 80GB 卡、当前 wheel 和模型镜像组合已实测成功。正式商用前核对 [MiniMax H3 本地权重授权](https://docs.comfy.org/tutorials/video/minimax/minimax-h3)。
