# 通用名画飞行导演提示词（MiniMax H3 版）

每次换画：在 ChatGPT 官网新开对话，上传**完整原画**，若有馆藏作品页也附上，然后复制下面代码框内的提示词。先审三条创意路线；决定后回复「定稿 JSON」。最终 JSON 粘贴进 ComfyUI 的 `ArtPrepare.story_json`。

```text
你是艺术史研究者、空间叙事导演和主观飞行镜头设计师。我上传了一幅历史画作。请先认真分析这幅画，再为它设计一条“进入画中世界”的四镜飞行旅程。每幅画都必须从自身的视觉母题、空间、透视、媒介、光线、年代和情绪出发；绝不套用村庄、山、教堂、树或星晕这些属于《星月夜》示例的路线。

成片为无声、全程保持原画媒介与笔触的 16:9 横屏视频：四段各约五秒的主观无人机式飞行，最后接一秒上传的完整原画。无人机本体不可见；场景可以大胆想象，但史实与虚构必须明确分开。镜头从画作一部分深入、穿过画中或合理想象的画外空间，发现某个画作独有的关键建筑、地貌或信息，再借画中的形状、材质、影子、光线、颜色或笔触做巧妙转场，最终精确回到原画视角。需要视觉上的小剧情，不要只是四张漂亮风景的排列。转场既要出人意料，也要能回到画作本身解释其合理性。

制作机制必须纳入设计：ComfyUI 先从原画逆向生成 KF4→KF3→KF2→KF1 四张关键帧。视频用本地 MiniMax H3 首尾帧模型：镜头1由 KF1→KF2；镜头2由上一镜桥接后的实际尾帧→KF3；镜头3由上一镜实际尾帧→KF4；镜头4由上一镜实际尾帧→上传原画的统一画布。四张关键帧中的 KF2/3/4 同时是上一镜出口和下一镜入口，必须定义成“接口帧”，共享接点物体、方向、屏幕位置和遮挡。模型有原生首尾帧约束，但仍需要你用文字明确描述如何飞向目标，不能指望模型自动理解空间路径。四段视频仍是一键顺序生成。

先做史实核对：识别作品、馆藏机构、创作年代、地点与不确定处，给可点击的原始来源。不要编造网址。把确有依据的资料放在 verified_context；画框外道路、人物动作和空间连接放在 imagined_context。画作身份或重要地点不确定时先问我。不要因为观众想看“当时真实的地方”而把想象叙述成真实复原。

第一轮不要输出 JSON，也不要生成图片。请提出 A、B、C 三条显著不同的四镜路线：各包含一句小剧情、起始画作细节或合理画外空间、四个空间位置、三个镜间转场和最终如何抵达原画。三条路线要在空间运动与转场机制上真正不同。比较每条的想象力、画作关联、空间连续性、四段五秒的可生成性；推荐一条并等我选择或修改。每镜动作要在五秒内可理解，不要安排过多大幅度绕行、反复急转或跨越不合理的距离。

我选择后，先给我中文四镜表并接受修改。只有我明确说“定稿 JSON”时才输出严格合法的单个 JSON 对象，不带代码围栏和解释。沿用以下字段名与层级；keyframes 与 shots 都严格四项，id 按 1、2、3、4 排列。除 schema_version=2 外，所有示例值应替换为这幅画自己的内容：
{
  "schema_version": 2,
  "artwork": {"title":"作品原文标题","artist":"作者","year":"年代","place":"有依据的地点；不确定要注明"},
  "source_links": [{"label":"馆藏作品页或图像来源页","url":"https://..."}],
  "verified_context": ["有可靠来源支撑的事实"],
  "imagined_context": ["本片想象的内容"],
  "visual_anchors": ["必须跨镜稳定的原画视觉地标"],
  "keyframes": [
    {
      "id":1,"beat_zh":"第一张接口帧",
      "camera_position":"相机在画中空间的位置，用英文",
      "camera_direction":"相机朝向，用英文",
      "camera_path_from_next_frame":"从更靠近原画的下一关键帧逆向移至当前帧的运动，用英文",
      "shared_landmarks":["相邻画面共用的地标，用英文"],
      "transition_object":"接点物体，用英文",
      "transition_object_screen_position":"接点物体在屏幕的方位和占比，用英文",
      "entry_state":"该帧作为当前镜头入口的状态，用英文",
      "exit_state":"由此帧继续飞行时的可行方向，用英文",
      "end_frame_constraints":["目标尾帧必须满足的构图约束，用英文"],
      "must_preserve":["不得丢失的画作元素、媒介和笔触，用英文"],
      "must_not_generate":["禁止生成的物件与风格，用英文"],
      "image_prompt_en":"自然语言补充画面质感和空间的英文提示词"
    },
    {"id":2,"beat_zh":"...","camera_position":"...","camera_direction":"...","camera_path_from_next_frame":"...","shared_landmarks":["..."],"transition_object":"...","transition_object_screen_position":"...","entry_state":"...","exit_state":"...","end_frame_constraints":["..."],"must_preserve":["..."],"must_not_generate":["..."],"image_prompt_en":"..."},
    {"id":3,"beat_zh":"...","camera_position":"...","camera_direction":"...","camera_path_from_next_frame":"...","shared_landmarks":["..."],"transition_object":"...","transition_object_screen_position":"...","entry_state":"...","exit_state":"...","end_frame_constraints":["..."],"must_preserve":["..."],"must_not_generate":["..."],"image_prompt_en":"..."},
    {"id":4,"beat_zh":"...","camera_position":"...","camera_direction":"...","camera_path_from_next_frame":"...","shared_landmarks":["..."],"transition_object":"...","transition_object_screen_position":"...","entry_state":"...","exit_state":"...","end_frame_constraints":["..."],"must_preserve":["..."],"must_not_generate":["..."],"image_prompt_en":"..."}
  ],
  "shots": [
    {
      "id":1,"beat_zh":"第一镜剧情",
      "start_state":"START STATE 英文描述",
      "camera_path":"CAMERA PATH，按时间百分比写分段动作",
      "speed_profile":"SPEED PROFILE",
      "parallax":"PARALLAX",
      "environment_motion":"ENVIRONMENT MOTION",
      "transition_approach":"TRANSITION APPROACH，怎样进入接点物",
      "final_quarter_target_state":"FINAL 25% TARGET STATE，最后四分之一如何逼近下一关键帧",
      "transition_type":"generic_occlusion",
      "motion_prompt_en":"整体导演意图的英文补充提示词",
      "transition_zh":"中文解释接点"
    },
    {"id":2,"beat_zh":"...","start_state":"...","camera_path":"...","speed_profile":"...","parallax":"...","environment_motion":"...","transition_approach":"...","final_quarter_target_state":"...","transition_type":"landmark_match","motion_prompt_en":"...","transition_zh":"..."},
    {"id":3,"beat_zh":"...","start_state":"...","camera_path":"...","speed_profile":"...","parallax":"...","environment_motion":"...","transition_approach":"...","final_quarter_target_state":"...","transition_type":"radial_light","motion_prompt_en":"...","transition_zh":"..."},
    {"id":4,"beat_zh":"...","start_state":"...","camera_path":"...","speed_profile":"...","parallax":"...","environment_motion":"...","transition_approach":"...","final_quarter_target_state":"...","transition_type":"final_artwork_alignment","motion_prompt_en":"...","transition_zh":"..."}
  ]
}

transition_type 当前可选 `generic_occlusion`、`landmark_match`、`radial_light`、`final_artwork_alignment`，以及《星月夜》专用的 `hill_occlusion`、`steeple_match`、`radial_star_halo`。这些名称用于记录接点诊断；不要为了字段名强行给其他画作发明山、尖塔或星晕。接点本体由 `transition_object` 和 `transition_approach` 准确说明。

为每张 image_prompt_en 再自行核对：KF4 的输入图1是原画、没有图2；KF3/KF2/KF1 的输入图1是下一张更靠近原画的关键帧，输入图2是原画。工作流会自动把这层关系与上面的字段组成实际图像提示词，所以你不要颠倒逆向位移方向。所有画面以 1344×768 统一画布；不要裁掉原画关键部分。每段 motion prompt 的最后 25% 专门朝下一张关键帧靠近，末段仅做减速与细微视角校正。检查相邻镜头共享物的左右位置、尺度、朝向与运动速度是否连续；禁止科幻传送门和与画作无关的现代物件。最终输出前自行校验 JSON 格式、来源链接、数组长度、字段完整性和英文提示词。
```

## 实际使用

1. 上传画作并发送提示词，评审 A/B/C；修改到满意时再回复「定稿 JSON」。
2. 可对照 [`examples/starry_night_story.json`](examples/starry_night_story.json) 检查字段，整段复制最终 JSON 到 `00_one_pass_minimax_h3.json` 的 `ArtPrepare.story_json`。上传原画并设置新的 `project_id` 后点击一次运行。
3. 《星月夜》范例中的村庄路线属于想象。按 [MoMA 作品页](https://www.moma.org/collection/works/79802)，画中村庄并不是梵高窗外可见的真实村庄；换画时也要核对各自的史实与想象边界。
