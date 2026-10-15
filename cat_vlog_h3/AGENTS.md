# 小猫 Vlog v4 交接（2026-10-09）

先读本文件及README。cat/六镜Wan草稿和masterpiece_flight2名画项目独立，勿恢复或改动工作区已有的无关Git删除。旧交接原文保存在references/handoff_before_v4.md。

## 当前交付与证据

本地唯一正式图workflows/01_one_pass_10x7s_h3_cu128.json沿用文件名，内容为schema_version4、十镜两阶段、逐镜约5–10秒。首帧JoyAI-Image-Edit-Plus BF16，40步/CFG4/euler/normal；视频现有H3 FL2VA FP8，1344×768、24fps、20步res_multistep/simple、只接首帧。JoyAI/H3本项目画质仍待用户实测，不得把本地测试、预检或大模型参数说成达到ChatGPT Image＋即梦Seedance效果。

用户截图曾证实AutoDL RTX6000D约84GB、110GB内存，Python3.12.3/Torch2.8.0+cu128/CUDA12.8、Nunchaku1.2.1已安装。ComfyUI在/root/ComfyUI，models软链接指向/root/autodl-tmp/ComfyUI-models；数据盘200GB。旧图曾返回OK 175 nodes，H3名画第一镜进入采样；没有四镜最终MP4或当前小猫十镜成功证据。音频VAE已显示READY SHA256 verified，FFmpeg/FFprobe后续已显示/usr/bin路径。上述不是实时机器查询。

用户明确不需要Codex远程部署、开机或GPU测试。本次只交付本地文件；由用户手动运行并看片。当前JoyAI新增约50.3GB权重未由Codex下载到实例，当前ComfyUI是否支持原生JoyAI需preflight核对。不要默认重装Torch/CUDA或偷偷启用Turbo、LoRA、Ref2VA、动作视频控制和付费API。

## v4关键约束

- 保留当前狸花白主角、银灰室友及舞蹈社面试剧情。用户布偶学姐、粉裙、33秒舞蹈视频的提示词只参考详细写法；这几种素材不在当前资产库，不能说已附入。
- 用户首帧成功基准为ChatGPT Image，视频为即梦Seedance2.0mini；全部本地生成，拒绝外部首帧导入作为正式替代。动作验收按顺序、空间关系、表演与服装准确，允许小幅时间偏差，不承诺逐秒逐爪复刻。
- 时长请求5–10秒，取最近合法17k+5帧，等距取较长。约5秒起，接受网格真实时长；不裁切成强行6秒。原175帧迁移后仍175帧。action_segments连续到真实终点，状态从start到end，前15秒钩子按累计真实时间审稿。
- assets/asset_catalog.json登记实际身份／服装／场景图，路径在assets内，owner为稳定图库ID。首猫两身份图、第二猫一图，再按需要加服装／场景，最多六张，不重复凑第三路。CatH3JoyEncode调用当前ComfyUI原生JoyAI _encode路径，实际图片传入列表。preflight检查原生节点和适配器签名。
- 服装单列characters.wardrobe。无衣服身份图不能覆盖确认服装。H3只读取已审首帧；不在视频提示词伪造三视图、动作视频、音轨或上一镜实际尾帧。
- static机位不变成follow；嘴部逐猫、声音逐镜；背景人类允许出现时人体禁令只针对猫。image_must_avoid进入图像负向，H3重要要求用正向保持描述。
- selected_shots默认all，可选1,4,7做少量验收。阶段1生成／复用选中图，用户看过后切阶段2确认。model_quality=pending最多三镜视频，accepted才可十镜正式运行，rejected停止。没有单镜试跑文件。
- 图片和视频缓存分别按当前条件检查，改声音／后续动作／时长可复用首帧。只有十个匹配片段和accepted状态才合片。媒体合成按逐镜帧数和音频时长，不固定72.9秒；默认舞蹈稿仍约72.9秒。质量状态只代表用户选择，不是自动画质判断。

## 分镜、Skill与迁移

storyboards/dance_club_audition_story.json是内置v4，原剧情、全部中文台词和音乐意图保留；相应review.md包含完整中文审稿和真实英文提示词。examples/rainy_day_cat_story.json为自然日常v4，保留叼物与一次猫叫等既有要求。migration_reports保留原v3全文和迁移说明；未定时动作整体保留，标记人工审稿，不丢台词和音乐。

个人Skill在~/.codex/skills/cat-vlog-storyboard，项目源在skills/cat-vlog-storyboard。入口保持先访谈与导演审稿，再详细首帧／动作／声音和v4 JSON，使用真实项目校验器；计划模式不写文件。detailed-prompt-standard.md保存用户完整成功原稿，并说明只是示例。名画Skill不适用本项目。

## 本地验证与后续实机验收

本地测试应覆盖实际照片列表与用途、服装优先级、背景人物、静态机位、闭嘴／对白、时长状态、镜号选择／缓存、两阶段不请求相反模型，以及不同长度合成视频与音频切口。scripts/preflight.py只读：资产／参数／节点／模型文件／数据盘／版本检查，不加载权重或GPU推理。提示词编译不截断；运行前实际CLIP tokenizer进行项目4096纯文本token预算检查，图像token不算在这个项目文本预算内。

acceptance/README.md及acceptance_story.json提供同一正式图中的少量案例与评分表。没有真实服装参考时将该项标记未测试，不能给满分或宣布全场景通过。用户看片失败时记录具体帧、问题、参数，再针对性修改；本地检查通过只能写代码结构完成。

下载遵守../masterpiece_flight2/AGENTS.md避坑经验：先限时限量比较同一文件URL，下载同线路，数据盘存储、续传、官方大小和SHA核对；速度是当次证据。新下载器默认5MB/s门槛，不逐次降低门槛掩盖坏线路；在无卡模式下载，不远程操作GPU。

最终本地验证：2026-10-09，82项测试通过；项目和个人Skill格式校验通过，离线资产／参数预检无错误。详见acceptance/code_validation_report.json。这不代表AutoDL节点版本已接入或模型样片通过。
