# 熵增定律 · 无声动画制作工程

输入是上一级目录的 `storyboard.json`。14 个镜头的图形按该分镜专门实现；字幕、时长、帧率、阶段、导航事件和20种组合读取同一份数据。改变故事结构时需要同步重新编排图形，不是把自然语言 JSON 自动转换为任意视频的通用引擎。

## 播放与输出

在 `vibe_entropy_storyboard` 目录启动：

```sh
python3 -m http.server 8767 --bind 127.0.0.1
```

打开 <http://127.0.0.1:8767/production/>。空格播放/暂停，左右键逐帧，拖动进度条或点击阶段跳转。原始画面入口加 `?capture=1`；指定起始帧可用 `?frame=1800`。播放器控件不进入导出画面。

- `../output/entropy.mp4`：150秒、4500帧、1920×1080、30fps，H.264／BT.709，没有音轨。
- `../output/entropy.srt`：可编辑的21组讲解字幕；原片画面中已经绘制字幕。
- `../output/poster.png`：片尾封面。
- `../review/contact_sheet.jpg`：主要关键帧。
- `../review/render_contract.json`：跳帧像素一致性、文字边界及播放器控制检查。
- `../review/video_qa.json`：全帧解码与实际 MP4 规格检查。
- `../review/visual_review.md`：实际视觉检查方式、修正与限制。

## 运行环境

需要 Node.js、Python、Google Chrome、FFmpeg。Python 依赖见 `requirements.txt`。当前制作使用已有 `vibe_quantum_pilot/.venv`，工程不携带虚拟环境；复制工程后可以自行创建独立环境：

```sh
python3 -m venv production/.venv
production/.venv/bin/python -m pip install -r production/requirements.txt
```

以下命令从 `vibe_entropy_storyboard` 运行，且预览服务器保持启动。也可以将 Python 路径换成本机已有安装 Playwright/Pillow 的环境：

```sh
node --test production/tests/timeline.test.cjs
production/.venv/bin/python production/tests/render_contract.py
production/.venv/bin/python production/render.py --review
production/.venv/bin/python production/contact_sheet.py
production/.venv/bin/python production/render.py
production/.venv/bin/python production/audit_video.py
```

局部导出：

```sh
production/.venv/bin/python production/render.py --start 56 --end 64 --output preview_combinations.mp4
```

无头 Chrome 使用临时隔离会话，不访问个人登录资料。系统黑体未随工程复制；在其他操作系统渲染时，需要提供合适的中文字体并检查布局。

## 时间和画面接口

- `stateAtFrame(frame)`：根据绝对帧号返回镜头、阶段、字幕、水样相态、对象姿态、粒子身份和当前卡片。超范围帧号钳制到首尾。
- `renderFrame(frame)`：绘制同一帧，预览和编码共用此函数。
- `window.filmDiagnostics`：供检查读取当前帧、镜头、阶段、文字边界和卡片ID，不显示在成片中。

播放时钟只决定选择哪个帧号，绘图不依赖真实经过的时间。宏观粒子示意使用固定种子。杯子和水样保持身份，20张卡片来自分镜中的全部真实组合，最后字幕保持到末帧。

## 表达边界

本片是二维原理示意，不是物理实验实拍。六标记模型仅比较左右分配，卡片不是运动轨迹；局部熵下降只针对重新冷却结冰这一段。热量使用连续方向线，电能使用不同形状的线路，熵使用边界与文字记账，不把它画成流动的物质。完整科学说明与来源保留在上级分镜文件中。
