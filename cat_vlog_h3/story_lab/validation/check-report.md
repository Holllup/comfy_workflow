# 分工调整与导演 Skill 检查记录

日期：2026-10-14。当前版本为“纯编剧＋独立导演提示词”两份 skill。

## 交付与迁移

- [cat-vlog-writer](../skills/cat-vlog-writer/SKILL.md)只处理创意、人物、冲突、互动、因果、对白和结尾。
- [cat-vlog-director-prompts](../skills/cat-vlog-director-prompts/SKILL.md)独立接收定稿，交付导演方案与逐镜首帧图、视频声画提示词。
- 旧视觉叙事参考已迁至导演 skill；三个旧分镜与导演自审保存在其[迁移记录](../skills/cat-vlog-director-prompts/references/migrated-storyboards.md)，标明旧表格不等于当前单次生成单位。
- 三个原故事的完整剧情段落已与迁移前 SHA-256 摘要逐一核对，内容逐字不变；迁移记录内的故事副本也一致。
- 旧验证报告及旧演练原文保存在[历史快照](history/2026-10-14-before-split.txt)。当前记录不把旧分镜测试当作新纯编剧 skill 的验收。

本次编辑限于 story_lab。未修改上层视频工程、全局 cat-vlog-storyboard 或其他项目，未安装全局 skill，未调用生成服务。

## 格式与引用

两份 skill 均运行官方 quick_validate.py，返回 Skill is valid!。另行解析并核对两份界面元数据的描述长度、名称与默认提示中的 skill 名；没有设置禁止自动选择的策略。

检查所有当前 Markdown 的本地链接、代码围栏与脚手架占位，未发现错误。历史纯文本快照中的旧相对路径作为历史原文保留，不充当当前导航。

使用机器已有的 Miniforge Python 与 PyYAML 6.0.3，没有安装新依赖：

```bash
/opt/homebrew/Caskroom/miniforge/base/bin/python /Users/zhwh/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/zhwh/Desktop/sd_workflow/cat_vlog_h3/story_lab/skills/cat-vlog-writer
/opt/homebrew/Caskroom/miniforge/base/bin/python /Users/zhwh/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/zhwh/Desktop/sd_workflow/cat_vlog_h3/story_lab/skills/cat-vlog-director-prompts
```

只检查本次文档和 skill，不运行未改变的上层视频代码测试。

## 固定剧情到提示词的检查

[完整案例](../skills/cat-vlog-director-prompts/references/worked-sequence.md)包含八个独立连续镜头的计划，以及 S01、S03、S05 的三组完整首帧／视频提示词，共六个复制块。案例标明模拟参考与模拟时长条件，没有把文案当成已出图或已生成视频。

作者审查并修正：

1. 动作交接：S01 只伸手停住与猫转头，S02 才压线和收脚，S03 只低头，S04 才揭两端，S05 完成剥离，避免重复主要动作。
2. 手的占用：S04 先将插头放到东侧地板，S05 持胶带时插头留在地板；S05→S06 明确省略收胶带、取插头和走向西墙的机械过程，不让同一只手同时持两物。
3. 猫的姿态：S02 增加自然的上身侧转，S03 起点对应修正，避免身体仍背离界线却要求前爪够到它。
4. 道具区分：纸箱旁收起的旧胶带、纸箱上原有的半卷胶带分别记录，S08 不将已揭掉的界线突然复原。
5. 空间与摄影：固定西窗、东桌灯的世界位置，机位在轴线同侧，低位关系镜、猫近景与斜俯接触镜服务不同观看任务。
6. 素材与声音：视频默认只输入本镜首帧，不虚构附入其他参考；示例原剧情无对白，未擅加台词或猫叫，声音服务既有动作。

## 手工行为演练

见[完整输入与输出](behavior-trials.md)，共两类编剧、六类导演请求。

| 编号 | 检查重点 | 本次样稿结果 |
| --- | --- | --- |
| W1 | 编剧提案不输出摄影或模型指令 | 三个剧情方向、推荐及少量问题 |
| W2 | 纯剧情的局部修改 | 只替换事件段落并检查因果 |
| D1 | 接受其他来源定稿 | 比较拍法，保留原事件含义 |
| D2 | 缺参考、未知版本 | 说明最小缺口，继续可完成的导演设计，不虚构素材或参数 |
| D3 | 首帧提前完成、固定／推进冲突、闭嘴／对白冲突 | 给出修正的首帧编辑稿与视频稿，保留台词和动作 |
| D4 | 动作与对白超过时长 | 指出冲突、提出拆镜或修改体量的选择，不偷删内容 |
| D5 | 局部机位调整 | 只改 S03 的首帧与视频机位，检查相邻衔接 |
| D6 | 只有失败文字反馈 | 明确未看片，给条件诊断与具体视频修稿 |

这些是同一作者的手工演练，不是独立模型评测。结构检查也不评判画面美学。真实首帧、视频动作、身份稳定、声音与整段剪辑效果尚未验证，需用户实际生成并反馈后验收。
