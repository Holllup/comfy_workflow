# 可换画的画中空间飞行提示词 · 空间版

把原画上传到 ChatGPT，然后发送下面的文字。先审创意路线；定稿后的 JSON 用于 `00_one_pass_minimax_h3_cu128.json` 的 `ArtPrepare.story_json`。

```text
你是艺术史研究者、空间导演和四镜头连续飞行设计师。请根据我上传的画作，设计四段各约五秒的第一人称低空到高空飞行，最后抵达完整原画并静止一秒。先核对馆藏与史实，给纯 HTTPS 来源；把画面之外的街道、人物与空间连接明确列为想象。先给三条显著不同、针对这幅画自身母题的路线，等我选定后再输出 JSON。

本工作流有一个关键限制，请严格遵守：系统不会把完整原画作为图像背景送入早期关键帧。它先从原画提取、打乱并模糊色彩，得到没有地标、没有构图、也没有原笔触几何的抽象色彩种子。逆向生成顺序仍是 KF4→KF3→KF2→KF1。KF4 的输入图 A 只是抽象色彩种子，须从文字重新构造接近最终视角的可进入空间；KF3、KF2、KF1 的唯一输入图 A 是下一张更靠近原画的 AI 关键帧。所有关键帧都没有输入图 B。完整原画只用于第四镜的最终尾帧约束和随后一秒定格。

不要把画作画成框、墙画、幕布、静止天空贴图、平面背景或透明贴纸。没有米色或其他纯色留边。画面必须铺满 16:9 画布。笔触是建筑、山体、植物、空气和光的表面材质；所有景物属于同一连续、可穿行的空间。设计明确的近中远景遮挡、大小变化和视差：相机掠过近景时，近处结构移动快，远处地貌与天空移动慢；视角变化时地标重新投影，不能让完整原画固定在后面。无人机本体不可见。

四张关键帧都是接口帧：KF1 是第一镜入口；KF2 是第一镜出口与第二镜入口；KF3 是第二镜出口与第三镜入口；KF4 是第三镜出口与第四镜入口。KF2/3/4 的接点物体在相邻镜头须保持同一侧、大小、朝向和运动方向。镜头1 KF1→KF2；镜头2 上一镜实际尾帧→KF3；镜头3 上一镜实际尾帧→KF4；镜头4 上一镜实际尾帧→完整原画。每段最后25%集中逼近目标尾帧。最后一镜允许原画的完整构图逐步出现，但直至末段不能让整幅原画作为背板出现。

我确认路线后，输出一个严格合法的 JSON 对象，不要 Markdown 围栏、解释或图片。请按同目录的 `examples/starry_night_story_spatial.json` 的完整字段结构编写，但所有地点、物件、色彩和路径都要根据当前这幅画重新设计。顶层必须有 `"schema_version": 2` 和 `"conditioning_mode": "spatial_style_seed"`，并包含 `artwork`、`source_links`、`verified_context`、`imagined_context`、`visual_anchors`、四个按 1–4 排序的 `keyframes` 和四个按 1–4 排序的 `shots`。

每个关键帧都要写 `beat_zh`、`camera_position`、`camera_direction`、`camera_path_from_next_frame`、`shared_landmarks`、`transition_object`、`transition_object_screen_position`、`entry_state`、`exit_state`、`end_frame_constraints`、`must_preserve`、`must_not_generate`、`image_prompt_en`。每镜都要写 `beat_zh`、`start_state`、`camera_path`、`speed_profile`、`parallax`、`environment_motion`、`transition_approach`、`final_quarter_target_state`、`transition_type`、`motion_prompt_en`、`transition_zh`。镜头 4 只有最后 25% 逐渐对齐原画。

每个 image_prompt_en 用英文写清：唯一输入图 A 是什么、相机从它逆向移动到何处、画中母题如何成为空间实体、共享地标与接点的屏幕方位和占比、必须禁止的平面背景/画框/留边。KF4 的图 A 是抽象色彩种子，不得称它为原画。每个 motion_prompt_en 用英文写 START STATE、CAMERA PATH、SPEED PROFILE、PARALLAX、ENVIRONMENT MOTION、TRANSITION APPROACH、FINAL 25% TARGET STATE。禁止使用 Markdown 格式的 URL；url 字段必须以 https:// 直接开头。输出前自行检查四张关键帧、四镜顺序和全部字段。
```

《星月夜》的空间版示例见 [`examples/starry_night_story_spatial.json`](examples/starry_night_story_spatial.json)。
