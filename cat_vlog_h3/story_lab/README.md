# 小猫故事创作室

两份独立 skill，分别解决“故事好不好看”和“怎样把定稿拍好并写成生成提示词”。

| 入口 | 适用请求 | 交付 |
| --- | --- | --- |
| [小猫创意编剧](skills/cat-vlog-writer/SKILL.md) | 想点子、加强矛盾、人猫互动、改剧情、对白与结尾 | 完整剧情，可按故事场景分段 |
| [小猫电影导演与生成提示词](skills/cat-vlog-director-prompts/SKILL.md) | 定稿后的分镜、拍法、首帧图与视频提示词 | 导演方案、逐镜首帧提示词、逐镜视频与声音提示词 |

导演 skill 可直接处理你从任何地方带来的定稿，不要求先调用编剧 skill。编剧不选择摄影机位；导演不擅自改变故事的动机、事件或结尾。

## 使用

在本目录工作时，AGENTS.md 按任务选择入口。也可以在新对话中指定文件：

> 请读取 /Users/zhwh/Desktop/sd_workflow/cat_vlog_h3/story_lab/skills/cat-vlog-writer/SKILL.md，和我共创一个有趣的人猫故事。我想到的题材是：……

> 请读取 /Users/zhwh/Desktop/sd_workflow/cat_vlog_h3/story_lab/skills/cat-vlog-director-prompts/SKILL.md。下面是定稿剧情和我提供的参考，请先给整体导演方案与关键镜头的完整首帧图、视频提示词样稿：……

当前是项目内 skill 源文件，未安装全局技能目录。无需接入现有 H3 工作流。

导演默认 ChatGPT 生图＋即梦视频，真实摄影质感、横屏 16:9、逐镜生成后剪辑，中文声画提示词。开始每期时核对实际即梦版本及输入方式，只使用你提供的参考。缺关键身份或服装素材时说明缺口，不替你发明新形象。

## 看效果与检查

- [三组剧情对照](skills/cat-vlog-writer/references/contrast-examples.md)：保留校园、合租与悬念故事正文，供剧情口味校准。
- [完整导演案例与三组提示词样稿](skills/cat-vlog-director-prompts/references/worked-sequence.md)：固定剧情如何转成连续镜头；测试素材和平台条件均标注为模拟。
- [导演方法](skills/cat-vlog-director-prompts/references/directing-craft.md)：注意力、调度、摄影、剪辑怎样服务戏。
- [检查记录](validation/check-report.md)与[请求演练](validation/behavior-trials.md)：分工、异常输入、连续性和局部修改的证据与限制。

实际使用时，你手动生成图像和视频，可将结果反馈给导演 skill 做针对性修订。文本检查通过与真实成片效果分别验收。

保存文件时，剧情默认进入 `stories/<故事短名>.md`，导演稿与提示词进入 `productions/<故事短名>_director.md`。只在需要拆开长稿时增加文件，不自动覆盖定稿剧情。
