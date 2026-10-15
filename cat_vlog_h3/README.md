# 小猫 Vlog v4：详细提示词、通用参考与样片验收

唯一正式节点图：[01_one_pass_10x7s_h3_cu128.json](workflows/01_one_pass_10x7s_h3_cu128.json)。文件名沿用历史名称，内容已是两阶段、十镜、逐镜约5–10秒。首帧候选JoyAI-Image-Edit-Plus BF16，40步/CFG4；视频为现有H3 FL2VA，1344×768、24fps、基础20步、只接首帧。当前未做本项目GPU画质验收，不能说达到ChatGPT Image＋即梦Seedance的效果。

## 文件与分镜

- [舞蹈社面试完整v4 JSON](storyboards/dance_club_audition_story.json)，默认内置；原剧情、台词和音乐意图保留，每镜仍175帧。
- [完整中文审稿及实际英文提示词](storyboards/dance_club_audition_story.review.md)。中文首帧、运镜概述、动作分段和声音逐项可读。
- [少量验收用v4分镜](acceptance/acceptance_story.json)及[评分表](acceptance/README.md)。仅在同一正式图选择1,4,7，不恢复单镜试跑文件。
- [编剧Skill源文件](skills/cat-vlog-storyboard/SKILL.md)。个人安装在~/.codex/skills/cat-vlog-storyboard；官网用户可用[PROMPT](PROMPT_ChatGPT_十镜编剧.md)。

分镜JSON是文本数据；导入ComfyUI的是正式节点图。新一期只换story_json，声音、唱歌或跳舞仍由H3原生生成。当前默认人物还是狸花白主角与银灰室友，不加入成功样例中的布偶学姐或粉裙。

## 两次运行和验收

1. 将完整JSON粘入「01 通用剧本与阶段」story_json。新一期或模型改版使用新run_id，例如dance_v4_01。
2. selected_shots默认all，也可填1,4,7；model_quality初始pending。phase保持1_生成首帧并审查，Run只生成所选首帧。02参考库展示实际照片；03展示所选编号总览和原图。
3. 不满意的图改对应首帧／状态／参考，或增加该镜variation，保持阶段1再Run；未变的图从磁盘复用。
4. 审图通过后保持run_id和镜号，切2_已审查_生成视频，Run。pending最多三镜视频用于验收，不能直接十镜全量；H3读已保存首帧，不重画图片。
5. 看片按评分表记录问题。通过后选择model_quality=accepted，再选择all生成正式十镜；未变片段可复用。失败选择rejected停止视频生成，按具体失败修稿或素材，不宣布模型已经更强。
6. 只有十张图和十个片段都符合当前条件且model_quality已accepted时才合片。所选验收片段完成、其他缺失时正常提示，不生成缺镜的正式MP4。

少量视频在数据盘output/<run_id>/clips/shot_01.mp4等文件中。可在Jupyter进入/root/autodl-tmp/cat_vlog_h3/output/<run_id>/clips/打开或下载看片；不用等待十镜合片。

同一期的审图和视频阶段run_id保持一致。只改对白、声音、后续动作或时长，可复用首帧；改身份、服装、场景、开场状态、图片种子或图像后端需重审。切阶段2是用户审图确认，软件不能自动判断图片是否满意。用户手改其他模型或采样参数须重新预检、用新run_id，不能沿用旧缓存。

## 通用参考与时间

assets/asset_catalog.json注册path、purpose（identity/wardrobe/scene）、owner（稳定图库ID，场景null）及身份图可选view。只登记实际存在且位于assets目录内的图片。两猫身份图目前共十张，服装和场景默认没有资产。

主要猫角度与细节、第二猫角度先选入，再加入服装与场景，总计最多六张，不重复凑输入。编码节点通过当前ComfyUI的原生JoyAI编码路径传入真实图片列表。服装图管衣服，身份图管身体；裸身身份照不会在文字规则上覆盖已确认服装。H3只接已审首帧，不接三视图、舞蹈视频、原曲或上一段实际尾帧。

例：添加服装图assets/outfits/my_outfit.png后，在目录中登记实际资产：

```json
"protagonist_outfit": {"path":"outfits/my_outfit.png","purpose":"wardrobe","owner":"protagonist"}
```

角色wardrobe.reference_asset_id使用该ID。场景资产purpose=scene、owner=null，在shots.reference_assets选择。资产缺失、用途或owner不匹配时先报错。

请求5–10秒，按最近合法17k+5帧、24fps解析；等距选较长。5秒→124帧/5.167秒，6秒→141帧/5.875秒，8秒→192帧/8秒，10秒→243帧/10.125秒。先解析真实时长再写action_segments，首段从states.start开始，最后到states.end。重叠、空洞、越界或状态引用断链会报错；文字姿态的物理可达性仍需导演审稿。

```bash
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/skills/cat-vlog-storyboard/scripts/resolve_timing.py 5 6 8 --project-root /root/ComfyUI/custom_nodes/cat_vlog_h3
```

camera_mode=static支持固定机位；嘴部、对白、猫叫和音乐逐镜读取。人体禁令限定猫的解剖结构，不抹掉允许出现的背景人类。时长变化不会偷偷删动作；成片总长由十镜实际帧数相加。

## 手动安装与预检

将新版cat_vlog_h3_bundle.zip上传/root，等Jupyter上传完成后执行：

```bash
unzip -t /root/cat_vlog_h3_bundle.zip
unzip -o /root/cat_vlog_h3_bundle.zip -d /root/ComfyUI/custom_nodes/
```

numpy/Pillow是本包依赖，已有时无需重装；不默认升级Torch。重启ComfyUI后先核对节点和JoyAI适配器版本，尚未下载模型也能做这一步：

```bash
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/preflight.py --url http://127.0.0.1:6006 --comfy-root /root/ComfyUI
```

missing native JoyAI或API changed表示当前ComfyUI不支持此包，先处理版本；不要先下载50GB再发现不能用。不自动运行git pull或重装CUDA/Torch。

JoyAI新增三份权重约50.3GB，候选来自[官方Apache-2.0仓库](https://huggingface.co/jdopensource/JoyAI-Image-Edit-Plus-ComfyUI)。确认节点可用后，在无卡模式先比较文件线路，再下载：

```bash
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/ensure_joyai_models.py --comfy-root /root/ComfyUI --probe-only
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/ensure_joyai_models.py --comfy-root /root/ComfyUI --download
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/ensure_joyai_models.py --comfy-root /root/ComfyUI --check-only
```

各线路4MB/20秒有界测速，默认低于5MB/s停止；同URL续传.part并校验固定官方大小/SHA256，通过才安装。下载中断可重跑，不能把历史速度当今天保证。模型进入/root/ComfyUI/models的数据盘软链接。H3原有四份权重继续复用，旧Qwen图片权重不被新图引用。

下载完成、ComfyUI服务已启动后检查模型文件、数据盘、FFmpeg及节点：

```bash
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/preflight.py --url http://127.0.0.1:6006 --comfy-root /root/ComfyUI --check-models
```

预检只读取，不加载模型或发起GPU推理；文件大小检查不等于此处重新验证SHA，完整哈希由安装脚本检查。字符预算在编译时检查，运行时用实际CLIP tokenizer检查项目4096纯文本token预算；预算检查不等于画质验收。

## 迁移、输出与验证

v3明确迁移，保持原件：

```bash
python3 /root/ComfyUI/custom_nodes/cat_vlog_h3/scripts/migrate_story_v4.py /root/old_story.json --output /root/new_story_v4.json
```

另写完整原文的迁移报告。原175帧仍175帧；未明确分段的旧动作整体保留并标记需审稿，不静默猜测台词或丢音乐。迁移后补齐中文审稿、状态与时序；旧图审查记录不能复用。当前两个示例已迁移并人工梳理，原文保存在migration_reports。

数据盘/root/autodl-tmp/cat_vlog_h3/output/<run_id>/包含所选首帧及哈希、编号总览、review.json、单镜clips、完整story.json、中文story_review.md、实际timing_report.json、使用的references及用途记录、每镜正向／负向／视频提示词、manifest.json。十镜完成输出1280×720的cat_vlog_h3.mp4。

本地测试覆盖动态参考传递、服装优先级、时序状态、嘴部声音、选择与缓存、两阶段lazy路径、真实合成音频和不同长度视频拼接。运行python3 -m unittest discover -s cat_vlog_h3/tests -q。当前没有JoyAI/H3本项目GPU样片验收；原实例Torch2.8/CUDA12.8、音频VAE下载与旧节点检查的证据见AGENTS.md。
