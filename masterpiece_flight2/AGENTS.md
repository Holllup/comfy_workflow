# 下载前必读：AutoDL 网络避坑记录

适用范围：`masterpiece_flight2` 的模型、Python wheel、Git 仓库及安装包下载。今后给用户任何较大的下载命令前，先按本文件检查。下面的速度是 **2026-10-04 这台 AutoDL 实例的实测记录**，不是各站点今后的速度保证。

## 这次踩过的坑

| 操作与来源 | 当时观测 | 教训 |
| --- | --- | --- |
| 在按小时计费的 RTX 6000D 上直接从 PyTorch CDN 安装 Torch 2.10/CUDA 13 | 约 642 MB 的 wheel 下载约 58 分钟，约 0.1 MB/s | 没有先测速，也没先检查镜像已有的 Torch；后来换用 Torch 2.8/CUDA 12.8 的镜像，避免了这次重装。 |
| 直连 Hugging Face 下载 Qwen | 连接卡住，留下 0 字节模型文件 | 不能把文件名出现当作下载成功；检查实际字节数和模型文件完整性。 |
| ModelScope 下载本项目六个 H3/Qwen 权重 | 约 65 GB；小样本测速约 12 MB/s，最终六项均为 `OK` | 本实例能高速下载模型，但不能据此推断 GitHub/PyTorch CDN 也快。 |
| `source /etc/network_turbo` 后下载 Nunchaku 官方 GitHub Release wheel | 8.4 MB 测速约 0.46 MB/s；`aria2c` 实际一度只有约 94 KiB/s | AutoDL 内置学术加速不保证稳定；短样本速度也可能高估持续速度。 |
| 经 AutoDL 文档推荐的公共 GitHub 代理入口，测试到的 `ghfast.top` | 4 MB Range 请求返回 HTTP 206，约 11.5 MB/s；约 142 MB wheel 实际约 9.6 MiB/s 下载完成 | 同一文件应先比较线路，再用快线路；第三方代理下载的二进制必须与官方 SHA256 核对。 |

本次匹配的 Nunchaku wheel 是 `nunchaku-1.2.1+cu12.8torch2.8-cp312-cp312-linux_x86_64.whl`，其[官方 v1.2.1 发布页](https://github.com/nunchux-ai/nunchaku/releases/expanded_assets/v1.2.1)列出的 SHA256 为 `e0cfe5a034bc2607ba78fe4d037ba1a90396e8c89b4cdce36146706c6cd4a54c`。此值**只适用于这个精确文件**，更换版本后必须重新查官方校验值。

## 给下载命令之前的检查顺序

1. **先确认是否真的需要下载。** 读取实际 `python3 --version`、`torch.__version__`、`torch.version.cuda`、ComfyUI 路径及现有文件。不要为了“更新”而默认重装几 GB 的 Torch，或重新下载已有模型。
2. **先确定文件和位置。** 写清精确文件名、预计大小、官方来源、版本匹配关系和保存目录。大文件放 `/root/autodl-tmp` 数据盘；pip 缓存也用 `PIP_CACHE_DIR=/root/autodl-tmp/pip-cache`。`/root/ComfyUI/models` 在本镜像里指向 `/root/autodl-tmp/ComfyUI-models`，但软链接目标最初不存在：`readlink -f` 后还要 `test -d`，必要时 `mkdir -p /root/autodl-tmp/ComfyUI-models`。用 `df -h` 查可用空间。
3. **先比较候选网络线路。** 优先用已有本地文件或镜像预置文件；外部文件逐一测 ModelScope、官方直连、AutoDL 内置加速或 [AutoDL 推荐的公共 GitHub 加速入口](https://www.autodl.com/docs/network_turbo/)。`ghproxy.link` 列出的域名会变，不能把本次的 `ghfast.top` 当作永久最快来源。AutoDL 文档说明 `network_turbo` 可能影响普通网络；测试公共代理时临时移除 `http_proxy`、`https_proxy` 等代理环境变量。
4. **先做有界测速再下完整文件。** 测同一个目标文件，限制请求大小和时间。例如对支持 HTTP Range 的来源读取约 4 MB，并要求 HTTP `206`、实际收到约 4 MB；若返回 HTML/JSON、`200` 全量响应、超时或样本不足，就不要据此推断大文件速度。根据总大小估算耗时：65 GB 大模型低于约 5 MB/s 时先找其他来源；约 142 MB wheel 可以在无卡模式接受较慢线路，但应先比较代理。测速只是预估，启动后还要观察数分钟的持续速度。
5. **选择可续传的下载工具。** 大文件优先 ModelScope Hub 的单文件下载或 `aria2c -c`；不要在两个进程中同时写同一目标文件。断线后保留部分文件和 `.aria2` 控制文件，再运行同一命令续传。切换下载来源后必须重新校验完整文件。
6. **二进制安装前做完整性校验。** 优先使用官方 SHA256。公共代理或第三方镜像只提供传输，不能替代来源验证；`aria2c` 的 `OK` 只代表传输完成。先 `sha256sum -c` 得到 `OK`，再对本地 wheel 执行 `python3 -m pip install --no-deps 文件.whl`，避免 pip 顺手重新下载或更换 Torch。
7. **把下载和推理分开计费。** 大模型、插件和依赖尽量在同一实例的无卡模式完成，六个模型和节点均核对后再开 GPU。无卡模式只省租金，**不会自动提高网速**。开 GPU 后先跑单镜，确认环境、显存和画质，再跑四镜。
8. **确认文件确实在服务器。** ComfyUI 缺模型弹窗中的“下载”曾触发浏览器下载到用户本机；不要把它当作服务器端安装。Jupyter 上传到 `/root` 后用绝对路径 `ls -lh /root/文件名`、`unzip /root/文件名 -d ...`，避免终端当前目录不同导致找不到文件。

### 有界测速示例

以下是模板，运行前换成**当前已核对的目标 URL**；不是所有服务器都支持 Range。代理线路与直接线路要分别测试，不得凭印象选择：

```bash
candidate_url='https://example.invalid/exact-file.whl'
curl -fLsS --range 0-4194303 --max-time 20 --max-filesize 8388608 \
  --output /dev/null \
  --write-out 'HTTP=%{http_code} BYTES=%{size_download} SPEED=%{speed_download} B/s\n' \
  "$candidate_url"
```

如果当前 shell 已运行 `source /etc/network_turbo`，测试公共代理时可只对这一条命令移除代理环境变量，不必修改用户整体配置：

```bash
env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
  -u all_proxy -u ALL_PROXY curl ...
```

## 给用户命令时的交付要求

- 先说**为何选择这个来源**，写出同一实例的测速结果、文件大小和预计耗时；没有测速就先给测速命令，不直接给大文件下载命令。
- 下载命令写明服务器端绝对目标路径、续传方式、失败时如何停止，以及完成后的大小/哈希检查。
- 说明哪些操作可在无卡模式完成，哪些必须等 GPU；不在付费 GPU 上等待慢速 PyTorch、GitHub 或模型下载。
- 若测速与实际持续速度差距明显，及时停下比较其他线路；不要把“无卡便宜”当成“下载速度问题已解决”。
- 不把本地静态测试写成 AutoDL 实机推理成功。若下载或运行失败，索取**第一条报错和当前实际速度**，按证据修正命令。

来源：[AutoDL 学术资源加速说明](https://www.autodl.com/docs/network_turbo/)、[AutoDL 公网网盘与上传下载说明](https://www.autodl.com/docs/instance_data/)、[ModelScope Hub 客户端](https://github.com/modelscope/modelscope_hub)、[Nunchaku 官方发布文件](https://github.com/nunchux-ai/nunchaku/releases/expanded_assets/v1.2.1)。
