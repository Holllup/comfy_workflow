# `masterpiece_flight2` 分镜 JSON v2：字段与镜头语义

以当前项目的 `core.validate_story`、`compose_image_prompt`、`compose_motion_prompt` 为最终校验依据；此页用于定稿时速查。原图、示例与代码可能更新，实际文件优先。

## 必需结构

顶层是单个 JSON 对象，不加注释，不保存 Markdown 代码围栏：

| 字段 | 要求 |
| --- | --- |
| `schema_version` | 数字 `2`，避免落入宽松的旧版校验。 |
| `conditioning_mode` | 固定字符串 `spatial_style_seed`；当前 H3 空间接线会拒绝缺少此标记的旧分镜。 |
| `artwork` | 非空 `title`、`artist`、`year`、`place`。若地点有争议，在值中准确写不确定性，不编造。 |
| `source_links` | 至少一个 `{ "label": "...", "url": "https://..." }`；优先馆藏作品页与原始图像文件页。 |
| `verified_context` | 至少一条有可靠来源支持的事实。 |
| `imagined_context` | 至少一条明确是本片虚构的空间、动作或人物活动。 |
| `visual_anchors` | 至少一条跨镜稳定的原画地标或笔触、色彩、空间关系。 |
| `keyframes` | 恰好四项，`id` 严格为 `1,2,3,4`。 |
| `shots` | 恰好四项，`id` 严格为 `1,2,3,4`。 |

每个 `keyframes[i]` 的**非空字符串**：

`beat_zh`, `camera_position`, `camera_direction`, `camera_path_from_next_frame`, `transition_object`, `transition_object_screen_position`, `entry_state`, `exit_state`, `image_prompt_en`。

每个关键帧的**非空字符串数组**：

`shared_landmarks`, `end_frame_constraints`, `must_preserve`, `must_not_generate`。

每个 `shots[i]` 的**非空字符串**：

`beat_zh`, `start_state`, `camera_path`, `speed_profile`, `parallax`, `environment_motion`, `transition_approach`, `final_quarter_target_state`, `transition_type`, `motion_prompt_en`, `transition_zh`。

`transition_type` 只能取：`generic_occlusion`、`landmark_match`、`radial_light`、`final_artwork_alignment`、`hill_occlusion`、`steeple_match`、`radial_star_halo`。最后三个名称来自《星月夜》示例，别为了用它们而给其他画加山、尖塔或星晕。类型目前用于诊断记录，实际画面仍由模型提示词和首尾帧决定。

## 接口帧和两种相反的运动

| 帧 | 视频中的作用 | 图像生成时的输入与逆向移动 |
| --- | --- | --- |
| KF1 | 镜头1首帧 | 唯一输入图为 KF2，描述从 KF2 后退到 KF1。 |
| KF2 | 镜头1目标尾帧、镜头2首帧 | 唯一输入图为 KF3，描述从 KF3 后退到 KF2。 |
| KF3 | 镜头2目标尾帧、镜头3首帧 | 唯一输入图为 KF4，描述从 KF4 后退到 KF3。 |
| KF4 | 镜头3目标尾帧、镜头4首帧 | 唯一输入图为抽象色彩种子，描述如何从色彩重建接近原画视角的可进入空间；它不是原画。 |
| 上传原画 | 镜头4目标尾帧及最终静态定格 | 原画本身，不由模型重画。 |

关键帧按 **KF4→KF3→KF2→KF1** 生成，视频按 **1→2→3→4** 前进。对每个接点检查两侧的相机到达方向、地标左右、遮挡物屏幕位置和占比、景别、速度、色调是否一致。`camera_path_from_next_frame` 写逆向位移；`shots.camera_path` 写正向飞行，二者不能混同。

## 单镜运动文本的内容

`ArtMotionText` 会把 `start_state`、`camera_path`、`speed_profile`、`parallax`、`environment_motion`、`transition_approach`、`final_quarter_target_state` 与 `motion_prompt_en` 拼成 H3 提示词。`camera_path` 最好按约五秒内的时间百分比安排少量可辨认的动作；最后 25% 只负责逼近下一帧的接点。让观众看得出“为什么下一镜从那里开始”。

当前 H3 工作流使用 1344×768 画布、每镜 124 帧/24 fps，四镜后接同一原画画布的 24 帧静止。分镜只控制生成内容，不应改动工作流设定，也不应要求 AI 重画原画终点。

## 定稿前校验

在项目根目录（`masterpiece_flight2` 的父目录）运行项目已有校验器，例如：

```bash
python3 - <<'PY'
from pathlib import Path
from masterpiece_flight2.core import validate_story
story_path = Path('masterpiece_flight2/storyboards/painting_slug_story.json')
plan = validate_story(story_path.read_text(encoding='utf-8'))
assert plan['schema_version'] == 2
assert plan['conditioning_mode'] == 'spatial_style_seed'
print('VALID', len(plan['keyframes']), len(plan['shots']))
PY
```

把示例路径改为实际文件。这个校验器检查结构和非空字段，**不保证**史实正确、镜头连续或提示词可生成；还要人工检查每个接口帧和最终原画视角。
