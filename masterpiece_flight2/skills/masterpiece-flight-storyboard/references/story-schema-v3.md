# 分镜 JSON v3：FLUX 写实飞行到原画

以 `masterpiece_flight2.realism.validate_story_v3` 为结构校验依据，公共入口 `core.validate_story` 会按版本转交。首次粘贴到 `ArtV3Prepare.story_json`；工程 ID 单独填写。v3 不能直接粘进旧 v2 节点。

## 必需顶层

- `schema_version`: 数字 `3`。
- `conditioning_mode`: `photoreal_to_artwork`。
- `artwork`: 非空 `title`、`artist`、`year`、`place`；地点不确定时直接说明。
- `source_links`: 至少一个 `{label, url}`，URL 为真实的纯 HTTPS 地址。
- `verified_context`、`imagined_context`、`visual_anchors`: 非空字符串数组，分别记事实、虚构与跨镜稳定的地标。
- `artwork_extension`: 非空 `prompt_en`，要求按原画媒介扩展边缘、接缝连续、不复制主要地标。原画中心由程序复原，不能要求重绘它。
- `keyframes`: 五项，`id` 严格为 `1,2,3,4,5`。
- `shots`: 四项，`id` 严格为 `1,2,3,4`。
- `morph`: `camera_locked: true`，以及非空 `motion_prompt_en`、`material_progression_en`。

## 关键帧与飞行字段

每张关键帧的非空字符串：`beat_zh`、`camera_position`、`camera_direction`、`camera_path_from_next_frame`、`transition_object`、`transition_object_screen_position`、`entry_state`、`exit_state`、`image_prompt_en`。

每张关键帧的非空字符串数组：`shared_landmarks`、`end_frame_constraints`、`must_preserve`、`must_not_generate`。

关键帧是一张静态接口图。`entry_state` 和 `exit_state` 都描述这张接口图自身的机位与物体状态，供前后视频共用；不要在同一关键帧中要求两种姿态。位移过程放进 `shots.camera_path`，逆向改图意图放进 `camera_path_from_next_frame`。

每镜的非空字符串：`beat_zh`、`start_state`、`camera_path`、`speed_profile`、`parallax`、`environment_motion`、`transition_approach`、`final_quarter_target_state`、`transition_type`、`motion_prompt_en`、`transition_zh`。

转场类型可用 `generic_occlusion`、`landmark_match`、`radial_light`、`final_artwork_alignment`；兼容的旧名字还有 `hill_occlusion`、`steeple_match`、`radial_star_halo`。这些字段只描述接点，实际遮挡靠关键帧和 H3 提示词，不是自动特效开关。第四段终点是写实 R5，建议使用 `landmark_match`，画作化放在独立 `morph`。

## 输入图语义

| 素材 | FLUX 唯一参考图 | 要生成的内容 |
|---|---|---|
| 扩展原画 A | 原画居中的规范画布 | 补齐外部场景；中心恢复为规范化原图 |
| R5 | A | 同构图、同地标位置的摄影场景，完全写实材质 |
| R4 | R5 | 比最终视角稍近的写实视点 |
| R3 | R4 | 再向飞行起点退一步的写实视点 |
| R2 | R3 | 前一接点的写实视点 |
| R1 | R2 | 第一镜入口的写实视点 |

R5 的 `camera_path_from_next_frame` 描述在同机位把扩展原画重建为写实空间；R4–R1 描述从下一张写实图逆向移动。没有输入图 B，也没有抽象画风种子。原画和 A 不进入四段 H3 飞行，只有画作化段以 A 为尾帧。

四段飞行分别为 R1→R2、R2→R3、R3→R4、R4→R5。第四段最后 25% 完成减速与对齐，最后约 6 帧已经固定；整个飞行段保持写实。`morph` 描述锁定机位后材质、色彩、云层逐渐转成原画，中心与两侧一起变化；避免对象搬动、平面插入、画框和透明重影。

时长与尺寸由工作流控制：五段各 124 帧/24fps，四处接点各去掉一张重复帧，再加 24 帧静止，共 640 帧，约 26.67 秒。模型画布 1344×768，最终 1280×720；JSON 不应改采样参数。

## 验证

在工作区根目录调用：

```python
from pathlib import Path
from masterpiece_flight2.core import validate_story
plan = validate_story(Path('masterpiece_flight2/storyboards/example_v3.json').read_text())
assert plan['schema_version'] == 3
assert len(plan['keyframes']) == 5 and len(plan['shots']) == 4
```

可参考 `examples/starry_night_realism_v3.json` 的字段结构；它是需要用户确认路线的演示，不能把其中的村庄、柏树和教堂照搬到其他画。
