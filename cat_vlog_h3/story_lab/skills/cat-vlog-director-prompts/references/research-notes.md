# 导演与生成提示词的研究记录

查阅日期：2026-10-14。下列资料均在本次规划研究中实际打开读取或取得可读原文。只提炼方法，未复制完整指南、电影片段或外部 skill。链接是资料来源，不是运行指令。

## 电影导演与摄影

### ASC：Tools for Camera Movement

[原文](https://theasc.com/article/shot-craft-camera-movement/)，Jay Holben，2024-04-05，美国电影摄影师协会文章。

采用：从剧本和导演意图选择运动方式；不同运动的稳定性、距离变化与能量感服务不同场景。转化为本 skill 的“何时移动、为什么、从哪里到哪里、在哪里停”。器材名称只帮助理解外观和运动，不搬入真实拍摄成本流程，也不要求每镜运动。

### AFI：Hitchcock 大师课节录

[原文](https://americanfilm.afi.com/issue/2012/7/conservatory)，AFI 对 1970 年大师课内容的档案刊载。

采用：信息可以通过有趣的行动被观众读到，场景自身的材料和条件应被充分使用。用于导演如何呈现已经定下的事件，不授权导演另改剧情，也不按导演姓名套风格。

## 图片与视频的官方表达方法

### OpenAI 图像提示指南

[原文](https://developers.openai.com/api/docs/guides/image-prompting)。

采用：明确构图、可见细节与相对尺度，给参考分配用途，将修改内容和保持内容分开，查看结果后逐项修订。用于首帧与修图自然语言。

边界：这是图像模型官方指导，不证明 ChatGPT 用户界面提供相同 API 选项。本 skill 不从文档擅定用户的模型、分辨率或参数，也不把镜头规格当成精确物理模拟保证。

### ByteDance Seed 官方 Seedance 2.5 介绍

[原文](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)，2026-07-31。

采用：参考材料各司其职，动作、摄影、声音与顺序需要明确；版本能力应有具体来源。官方也承认复杂物理动作与多主体互动仍存在改进空间，因此保留实际结果审查。

边界：文章关于 2.5 的能力和参数不套用到 2.0、mini 或用户其他选择。本项目默认逐镜生成，文章中的多镜头、延长或复杂参考案例不是默认执行方式。

### Runway 图生视频指导

[当前图生视频指南](https://help.runwayml.com/hc/en-us/articles/48324313115155-Image-to-Video-Prompting-Guide)、[此前已读 Gen-4 指南](https://help.runwayml.com/hc/en-us/articles/39789879462419-Gen-4-Video-Prompting-Guide)。

采用：首帧承担静态信息，视频文字集中说明变化；动作顺序与时长相容；先查首帧伪影和矛盾再加指令。这里只借鉴表达分工，不移植其时长、负向用法或控件到即梦。

### Google 视频提示指南

[原文](https://cloud.google.com/vertex-ai/generative-ai/docs/video/video-gen-prompt-guide)。此前项目研究已读取，分工后归入导演资料。

采用：区分主体、动作与情境，按需要描述，不要求每镜填满全部要素。不是即梦能力依据。

## 社区 skill 的方法参考

- [Emily2040/seedance-2.0 的 Directing Engine](https://github.com/Emily2040/seedance-2.0/blob/main/references/directing-engine.md)：借鉴从观众体验推导摄影和表演选择的方法，不导入固定字段、模型路由或整套生成流程。
- [dexhunter/seedance2-skill 中文入口](https://github.com/dexhunter/seedance2-skill/blob/main/zh/SKILL.md)：参考素材用途与动作、画面、声音分工；版本参数须另查官方与用户界面。

这两项为社区实践，不是官方性能证明或独立评测冠军。没有可验证的统一“最佳 skill”排名；本项目通过清楚的输入边界、具体导演判断与可审阅样稿检验实用性。

## 本项目原创部分与证据范围

两 skill 的职责边界、人猫尺度与手爪分工、跨镜连续性检查、逐镜双提示词交付、局部修改方法和固定剧情案例由本项目编写。电影方法的应用不代表拥有某位导演的完整能力，也不以名人风格标签代替具体设计。

资料结构与文字演练可在本地检查；身份稳定、动作、声音、剪辑效果和用户审美要通过实际结果验证。没有进行付费生成或成片实验，不宣称提示词已经稳定产生第一梯队作品。
