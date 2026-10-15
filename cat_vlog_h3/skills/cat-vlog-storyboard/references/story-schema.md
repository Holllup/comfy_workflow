# v4 工作流与JSON接口

正式图仍在workflows/01_one_pass_10x7s_h3_cu128.json，文件名是历史名称；内容为十镜、两阶段、逐镜可变时长。阶段1生成／复用所选首帧；阶段2读取已审图生成H3声画。没有尾帧、动作视频、外部音轨输入。

顶层只含schema_version:4、episode、characters、shots。episode含title_zh、theme_zh、arc_zh，可选visual_style_prompt_en。

characters按英文ID索引，每项含name_zh、identity_prompt_en、must_not_change_en（非空英文数组）、reference_set（图库ID，画外角色null）、voice_prompt_en及wardrobe。wardrobe无本期服装时为null，有服装时为对象：prompt_en、must_preserve_en（非空数组）、reference_asset_id（实际服装资产ID或null）。身份文字只描述身体，不同时写No clothing与裙装。

当前protagonist有front/side/back/left45/right45/face；roommate有front/side/back/face。默认没有服装或场景资产，用户成功样例中的布偶图、校园图不在当前库。

shots恰好十项、id按1–10排列：

|字段|约定|
|---|---|
|beat_zh、time_of_day_zh、location_zh|剧情作用、时间、地点|
|camera_mode|static/follow/selfie/pov|
|duration_seconds|请求5–10秒，最近合法17k+5帧，等距取较长；先显示实际秒数再写动作|
|cast|1–2项，每项character_id、views；首猫两个不同视角，第二猫一个|
|reference_assets|额外资产数组，可为空；每项asset_id、purpose（identity/wardrobe/scene）、character_id（场景为null）|
|first_frame_zh|完整中文静态首帧稿，不自动翻译|
|video_overview_zh、sound_notes_zh|接口可选，Skill定稿应填完整中文视频概述和声音说明|
|start_image_prompt_en|英文场景、光线、构图、机位及首帧细节，与states.start一致|
|background_prompt_en|背景人物与环境；不要求时空字符串|
|states|状态ID→英文可见状态；至少start、end，start只描述开场静态姿态|
|action_segments|每项start_seconds、end_seconds、from_state、to_state、action_en、action_zh|
|motion_prompt_en|英文总体运镜、连续镜头和表达要求；时间只在action_segments写一次|
|mouth_policy|每个可见猫对应closed/speech/expressive|
|ambience_prompt_en|英文环境声与物理声，完全没有用N/A|
|audio|utterances、diegetic_music_prompt_en、background_music_prompt_en、cat_vocalizations_prompt_en|
|must_preserve_en、must_avoid_en|非空视觉保持／禁止数组，禁止项进首帧负向；视频重要限制用正向保持描述|

动作从0开始、连续无重叠或空洞，结束于实际网格时长。首段from_state=start，后段from_state等于前段to_state，最终to_state=end。例如6秒请求结束于5.875秒。机器检查状态引用，不判断文字动作是否真符合猫解剖结构；Skill需检查首帧与动作可达性。

台词项：speaker_id、mode（speech/singing/voiceover）、language、text（原文）、delivery_en、cue_en。画外角色用voiceover。无台词[]、无相应音乐／猫叫空字符串；closed与说话、唱歌、张嘴猫叫冲突，叼道具等动作可用expressive。

assets/asset_catalog.json按资产ID登记path、purpose、owner（稳定图库ID；场景null）和身份图可选view。路径须在assets内且真实存在。实际编码顺序为主要猫角度／细节、第二猫角度、所需服装和场景，最多六张、不重复占位。外貌图只管身份，服装图只管服装，场景图只管场景；H3阶段只读已审首帧。

图片缓存包含图像后端、照片内容、首帧状态、服装、场景、图像提示词和图片种子。只改时长、后续动作或声音可复用首帧。视频缓存包含首帧哈希、真实帧数、视频提示词、种子和固定后端版本；手改其他模型或采样参数需重新预检并使用新run_id。

scripts/migrate_story_v4.py <v3源文件> --output <新文件>不覆盖源文件，另写完整原文的迁移审稿报告。原175帧仍175/24秒。没有明确时间段的旧动作完整保留为一段并标记需审稿，不能静默丢台词或音乐。旧首帧审图须重新建立。

验证：Skill的scripts/validate_story.py <JSON> --project-root <目录> --prompts，执行模式可加--review-markdown <路径>。真实参考用途、提示词与时长可检查，画质需看片。

操作：粘贴story_json，同一期run_id不变；selected_shots填all或1,5,7。阶段1审图；阶段2生成选中视频。pending最多三镜验收，看片后accepted可十镜运行，rejected停止视频。十个匹配片段齐全后输出cat_vlog_h3.mp4，总时长由帧数相加。
