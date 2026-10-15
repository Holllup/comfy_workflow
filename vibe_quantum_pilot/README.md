# 上帝会不会掷骰子？

55 秒 · 1920×1080 · 30fps · 无声视觉样片。

主线：逐个落点 → 累积出条纹 → 拉远看双缝装置 → 单次发射与探测 → 概率曲线 → 单次与整体。

## 看样片

- `output/quantum_pilot.mp4`：完整视频，H.264，1650 帧，没有音轨。
- `output/poster.png`：片尾封面。
- `review/contact_sheet.jpg`：12 张关键帧。
- `review/all_frames.jpg`：72 张逐秒及边界检查图。
- `review/qa_report.json`：最终视频的全帧解码、变化与规格检查。
- `output/captions.srt`：与六个镜头对应的可编辑字幕。

在本目录运行 `python3 -m http.server 8766 --bind 127.0.0.1`，打开 <http://127.0.0.1:8766> 即可预览。空格播放/暂停；左右方向键逐帧；拖动时间条或点击章节跳转。直接双击 HTML 无法读取分镜 JSON，请通过本地服务器访问。

## 重新制作

需要 Node.js、Python、FFmpeg 和 Google Chrome。本项目使用独立的无头浏览器，不读取个人浏览器资料。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
node --test tests/model.test.cjs
```

保持预览服务运行，另开终端执行：

```sh
.venv/bin/python tests/render_contract.py
.venv/bin/python scripts/render.py --review
.venv/bin/python scripts/contact_sheet.py
.venv/bin/python scripts/render.py
.venv/bin/python scripts/audit_video.py
```

导出局部转场：

```sh
.venv/bin/python scripts/render.py --start 14 --end 20 --output transition_apparatus.mp4
```

## 文案与时间接口

`scenes.json` 保存片名、六段起止时间、标题、字幕行与强调词。后续编剧 skill 可以先输出这个文件的数据。当前六段视觉顺序保持固定；在总长 55 秒内调整各段时长，动画按每段的相对进度重定时。重新设计镜头数量或视觉动作时，需要修改绘图逻辑。

`window.renderFrame(frame)` 是预览、截图和 MP4 导出的统一入口。输入帧号，完成确定性绘制并返回 `{frame, count}`。绘图不依赖真实播放时间；预览的时钟只负责选择帧号。

`model.js` 负责干涉概率密度、CDF 抽样、落点累积、单次事件和时序映射。`film.js` 负责画面、字体、图形衔接与预览控制。

随机种子固定为 613。每一个已出现的落点都保留其探测屏坐标；屏幕整体移动或缩放时，落点随屏幕一起变换。概率曲线和落点共用同一个归一化分布。

## 科学依据

[日立的单电子累积实验](https://www.hitachi.com/rd/research/materials/quantum/doubleslit/index.html)支持单次探测累积形成条纹的现象。该实验采用电子双棱镜，本片画的是教学双缝示意，两者装置不同。

[IBM Quantum 对 Born 规则的介绍](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)说明测量概率如何由量子态给出。

模型、无量纲坐标、时间编排及简化边界记在 `sources.json`。本片讨论给定实验中的单次探测与统计规律，不声称解决量子力学的诠释争论。

## 本轮审看重点

先看一次完整样片，再记录不满意的时间点：哪里没看懂、哪里停留太久、哪里文字或图形不够灵动。正式脚本仍可由后续编剧 skill 改进。
