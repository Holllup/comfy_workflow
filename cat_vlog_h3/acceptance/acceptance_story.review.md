# JoyAI/H3本地模型少量验收 · v4 分镜审稿

技术验收，使用当前两猫与真实身份照片；不是舞蹈社正式剧本。

只选择1,4,7观察身份、双猫动作、表情和固定机位。服装无实际参考，保留为未测试。

本文件供逐镜审稿。代码与素材检查通过不代表 JoyAI/H3 的样片效果通过；当前模型画质需人工验收。

## 镜头 01 · 0.000–5.167秒

请求 5.000秒；实际 124帧／5.167秒。剧情：验收案例1：身份、动作及静态机位

### 首帧图提示词（中文）

横屏真实摄影，浅木舞蹈室、柔和中性光；当前狸花白主角在居中偏左，双后爪站稳、前爪弯于下胸、闭嘴看前方。固定斜前全身画面，脸、前后爪与尾巴清楚，不新增室友、服装或文字。

### 视频生成提示词（中文审稿）

以实际首帧开始，固定斜前机位，不切镜、不换场景。动作顺序和支撑按分段，允许小幅节奏偏差，不允许身份或肢体错误。

- 0.000–2.000秒：把靠画面右边的前爪慢慢举到上胸，另一爪低放，后爪不离地。
- 2.000–5.167秒：慢慢将前爪放回下胸，耳朵与眼神略放松，闭嘴停住。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：只有柔和室内环境声和少量自然爪落地声，无对白、猫叫、演唱或未指定音乐。


### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CAMERA MODE: static.
START FRAME: Real photography, horizontal 1344x768, pale oak dance room, neutral soft indoor light. One small tabby-and-white protagonist at center-left, full feline body visible, 35mm lens at feline chest height, paws and tail clearly separated. No other foreground subject, mirror, writing or costume.
OPENING STATE: The protagonist is grounded at center-left, forepaws bent at the lower chest, eyes attentive and mouth naturally closed.
BACKGROUND: 
MUST PRESERVE: The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: Extra limbs or human fingers on the cats; Merged cat paws or swapped coat markings; Mirrored duplicate cats, text, logos or watermarks; Cuts, jumps, spins or changing the room; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, static camera locked throughout the take. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. FIRST-FRAME STATE: The protagonist is grounded at center-left, forepaws bent at the lower chest, eyes attentive and mouth naturally closed. BACKGROUND:  VIEW: fixed front oblique cat shot with readable faces and paws. CAMERA: locked tripod for the complete continuous take; no motion or cut. Maintain The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–2.000s: Slowly raise the forepaw nearest the right edge of the image to upper-chest height; keep the other paw low and both hind paws grounded. End state: One forepaw is at upper-chest height, the other lower; the cat is balanced and closed-mouthed. 2.000–5.167s: Lower that paw slowly to the lower chest, soften the ears and eyes slightly, then settle without opening the mouth. End state: Both forepaws return to the lower chest and the cat settles with a soft attentive gaze. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. No meows or other unrequested cat vocalizations. Within the scene, only the described voices, physical sounds and ambience are audible.
overall_soundscape: Quiet indoor room tone and only the small natural paw contacts described.
non_diegetic_music: N/A
```

## 镜头 02 · 5.167–12.458秒

请求 7.292秒；实际 175帧／7.292秒。剧情：新音乐一响，主角按旧节奏多跳半步后卡住，向室友求助，再小声问能否放回原来的歌。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角在蓝色地标附近，保留一个将要落下的后爪和抬起的前爪，神态刚由自信转为寻找节拍；室友在右侧远一些，前爪停在准备鼓掌的位置。构图：音响旁的低位宽景，黑色音响占左近景，空地将主角与室友分开，使错拍与尴尬可读；猫没有跌倒。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。音响侧低宽景开始，缓慢推近约30厘米并略向侧方展示室友，保持后爪可读，不绕到猫身后。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–1.800秒：陌生音乐开始；主角凭惯性按旧节奏踏一步、抬爪，忽然发现不对。
- 1.800–4.200秒：主角脚已经停住，一只前爪还悬着；它慢慢看向右侧室友。室友本要鼓掌，爪子也尴尬地停住。
- 4.200–6.600秒：镜头轻推近，主角转回面试官方向，小声说“能放回刚才那首吗？”
- 6.600–7.292秒：保留短暂安静的表情停顿，主角耳朵略向侧面转，室友用眼神安慰。

嘴部规则：狸花白主角小猫：只在自己对白或演唱时开口；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：换成原创、无演唱的约96 BPM陌生嘻哈节奏，清楚但克制的低音与拍点；主角提问时音乐放低。无额外猫叫或旁白。

- 狸花白主角小猫／speech：能放回刚才那首吗？

### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_left45]: approved left45 view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A wide low view from beside the black speaker, 35mm-equivalent lens, echoing the previous dance floor but changing the visual rhythm abruptly. The speaker is a dark near-left foreground shape; the protagonist stands on the blue marker in the middle distance with one hind paw halted a fraction off the floor and one forepaw frozen mid-gesture. Its ears tilt unevenly and its eyes search for the new beat. A broad patch of bare oak floor isolates it. The roommate remains at screen-right, half-raised paws paused before a clap, its concerned gaze directed at the protagonist. Show the missed beat and social embarrassment through body language, not a fall.
OPENING STATE: The protagonist is near the blue marker with one hind paw poised just above the floor and one forepaw raised; its ears begin to search for the unfamiliar beat. The roommate at screen-right holds a pending clap. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The protagonist stays in the same part of the room, with the roommate on its right; Awkwardness is conveyed through timing and expression, not grotesque body deformation.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; A pratfall, crying, bullying, turning instantly into an expert, or replaying the full prepared routine; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist is near the blue marker with one hind paw poised just above the floor and one forepaw raised; its ears begin to search for the unfamiliar beat. The roommate at screen-right holds a pending clap. Both mouths are closed. BACKGROUND:  VIEW: a readable full-body view that gradually becomes a medium-full two-shot. CAMERA: a slow 0.3m push toward the protagonist, with a slight lateral move revealing the roommate; never orbit behind either cat. END STATE: still on its feet, needing help; no fall or sudden change in skill. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The protagonist stays in the same part of the room, with the roommate on its right; Awkwardness is conveyed through timing and expression, not grotesque body deformation. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.800s: the protagonist makes one step at the earlier, faster pace, then notices the unfamiliar beat. End state: The protagonist has made one extra step at the old pace. 1.800–4.200s: stop its feet while one forepaw remains lifted; look to the roommate, whose intended clap freezes midway. End state: Its hind paws stop and one forepaw remains lifted; the pending clap stops. 4.200–6.600s: turn toward the offscreen interviewer and timidly deliver the assigned short line with subtle muzzle movement. End state: The protagonist faces the panel after its timid question. 6.600–7.292s: hold an embarrassed but endearing pause. End state: still on its feet, needing help; no fall or sudden change in skill. Character protagonist opens its mouth only for its own written speech or singing; other times it rests naturally. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. After its feet stop and it looks back from the roommate to the panel. Character protagonist, The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Voice: A light youthful male Mandarin voice, natural conversational pacing and restrained expression. (S1), with Quiet and slightly embarrassed, with a small pause before speaking., says: <d>[Chinese] 能放回刚才那首吗？</d> The other visible cat does not lip-sync this speaker's line. No meows or other unrequested cat vocalizations. Music audible within the scene: An unfamiliar original vocal-free hip-hop groove around 96 BPM with restrained bass, a different rhythm pattern and a clear countable pulse, played from the rehearsal speaker. It begins immediately after the change of song and becomes quieter when the protagonist speaks.
overall_soundscape: One slightly mistimed paw contact, a short paw shuffle and quiet room tone during the embarrassed pause.
non_diegetic_music: N/A
```

## 镜头 03 · 12.458–19.750秒

请求 7.292秒；实际 175帧／7.292秒。剧情：主角坦白自己只跟一首歌练过；银灰室友本想帮忙补充，最后温和地点头。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角在左近景，前爪自然放低，耳朵略低，低头后准备诚实回答；室友在右侧半步后，神态温和，项圈吊牌可辨。构图：猫眼高度的中近双猫肖像，脸与胸部为画面重点，地标只在下沿虚化出现，面试官和桌子不遮挡。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。猫眼高度的中近双猫采访画面，只做不超过15厘米的缓慢轻推，避免猫张大嘴。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–2.000秒：主角收低前爪，认真听面试官问“平时怎么练的？”室友在右后方等待。
- 2.000–3.500秒：主角先瞟一眼室友，再看回面试官，出现一个不好意思但诚实的停顿。
- 3.500–6.000秒：主角小声回答“就……跟着这首练的。”室友微微张口想帮忙，最后只是点头。
- 6.000–7.292秒：主角露出一点不好意思的笑意，室友靠近半步，给它支持而不抢话。

嘴部规则：狸花白主角小猫：只在自己对白或演唱时开口；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：没有音乐，保留安静室内环境声。面试官画外提问，主角犹豫回答；室友不替主角张嘴。

- 画外面试官／voiceover：平时怎么练的？
- 狸花白主角小猫／speech：就……跟着这首练的。

### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A quiet feline-eye-level medium portrait two-shot, 55mm-equivalent lens. The protagonist occupies the left foreground, shoulders and face prominent; ears slightly lowered, whiskers forward, eyes dropping briefly toward the floor as it prepares to admit it practiced only one song. The roommate stands half a step behind on the right, collar and round pendant visible, expression gentle rather than pitying. The panel stays outside the frame. The blue marker is a small soft shape at the bottom edge; warm window highlights separate the two faces from the cream wall.
OPENING STATE: The protagonist is screen-left in a medium portrait, forepaws lowered and ears slightly lowered while listening. The roommate stands screen-right half a step behind, attentive. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The protagonist remains collarless; the visible black collar belongs only to the roommate; The interviewer remains offscreen and uses the same voice throughout the episode.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; Human lips or teeth, exaggerated talking mouth animation, hostile judging or an invented third visible character; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist is screen-left in a medium portrait, forepaws lowered and ears slightly lowered while listening. The roommate stands screen-right half a step behind, attentive. Both mouths are closed. BACKGROUND:  VIEW: quiet eye-level medium two-shot during the audition interview. CAMERA: almost stationary, with a very slow natural push no more than 0.15m. END STATE: honest vulnerability and a friendly alliance, with no hostile reaction. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The protagonist remains collarless; the visible black collar belongs only to the roommate; The interviewer remains offscreen and uses the same voice throughout the episode. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–2.000s: the protagonist listens to the interviewer. End state: The protagonist has listened to the question. 2.000–3.500s: glance briefly at the roommate and return attention to the panel. End state: It has glanced at the roommate and returned attention to the panel. 3.500–6.000s: give the hesitant Mandarin answer; use restrained jaw and muzzle movement without human lips. The roommate starts to react, then offers a small supportive nod. End state: The answer has been delivered; the roommate gives a supportive nod. 6.000–7.292s: the roommate steps only half a paw-length closer; the protagonist settles. End state: honest vulnerability and a friendly alliance, with no hostile reaction. Character protagonist opens its mouth only for its own written speech or singing; other times it rests naturally. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. At the start while both cats wait for the next instruction. Character interviewer, An unseen university dance-club interviewer located near the camera; never a visible third cat. Voice: A calm adult female Mandarin voice, friendly and matter-of-fact, mild indoor reverberation. (S2), with Curious and nonjudgmental., says in an off-screen voiceover: <d>[Chinese] 平时怎么练的？</d> The speaker remains offscreen; the visible cats do not lip-sync this voiceover. After glancing toward the roommate and returning attention to the panel. Character protagonist, The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Voice: A light youthful male Mandarin voice, natural conversational pacing and restrained expression. (S1), with Hesitant but honest; preserve the brief hesitation., says: <d>[Chinese] 就……跟着这首练的。</d> The other visible cat does not lip-sync this speaker's line. No meows or other unrequested cat vocalizations. Within the scene, only the described voices, physical sounds and ambience are audible.
overall_soundscape: Quiet rehearsal-room tone, faint indistinct campus ambience, soft breathing and one paw shuffle.
non_diegetic_music: N/A
```

## 镜头 04 · 19.750–25.625秒

请求 6.000秒；实际 141帧／5.875秒。剧情：验收案例4：身份、动作及静态机位

### 首帧图提示词（中文）

当前狸花白主角在左，银灰室友在右并领先半个身位；后爪站稳、前爪自然屈于下胸，两猫分开。固定正面略斜全身镜头，看见脸和前后爪；真实浅木舞蹈室、中性柔光。背景可有两个虚化人类社员，不遮猫，没有镜面复制、文字或新增服装。

### 视频生成提示词（中文审稿）

以实际首帧开始，固定斜前机位，不切镜、不换场景。动作顺序和支撑按分段，允许小幅节奏偏差，不允许身份或肢体错误。

- 0.000–1.800秒：室友双前爪由下胸抬到上胸，爪尖略朝前、肘部弯曲。主角先看再迟约0.3秒跟随；爪不交叉不碰脸，后爪不离地。
- 1.800–3.800秒：两猫把靠画面右边的前爪斜向右上举，最高到耳尖；另一爪在胸前偏下，上身只轻倾，分段结束前收回。
- 3.800–5.375秒：室友双爪向两侧适度展开，略低于肩；主角这次及时跟上。只小幅转移重心，不侧移、不跳。
- 5.375–5.875秒：两猫将前爪收回下胸稳定停住。主角抬眼看室友，略开心，仍闭嘴。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：只有柔和室内环境声和少量自然爪落地声，无对白、猫叫、演唱或未指定音乐。


### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: static.
START FRAME: Real photography, horizontal 1344x768, pale wood dance room, neutral soft light. Current protagonist screen-left and silver roommate screen-right slightly ahead, full bodies visible with space between. Their forepaws are bent separately at lower-chest height. Static front oblique 40mm lens; no reflections or readable writing.
OPENING STATE: The protagonist is screen-left and the silver roommate screen-right half a body ahead. Both hind paws are grounded and forepaws separated at the lower chest; mouths closed.
BACKGROUND: Two softly out-of-focus human students stand far behind the cats, with natural human bodies and hands; they do not block the foreground cats or draw focus.
MUST PRESERVE: The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: Extra limbs or human fingers on the cats; Merged cat paws or swapped coat markings; Mirrored duplicate cats, text, logos or watermarks; Cuts, jumps, spins or changing the room; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, static camera locked throughout the take. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist is screen-left and the silver roommate screen-right half a body ahead. Both hind paws are grounded and forepaws separated at the lower chest; mouths closed. BACKGROUND: Two softly out-of-focus human students stand far behind the cats, with natural human bodies and hands; they do not block the foreground cats or draw focus. VIEW: fixed front oblique cat shot with readable faces and paws. CAMERA: locked tripod for the complete continuous take; no motion or cut. Maintain The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.800s: The roommate lifts both forepaws from the lower to the upper chest, tips slightly forward and elbows bent. The protagonist watches, then follows about 0.3 seconds later. Paws stay apart, never cross or touch the face; hind paws stay grounded. End state: Both cats hold separated forepaws near the upper chest with grounded hind paws. 1.800–3.800s: Both cats raise the forepaw nearest the image right edge diagonally toward that edge, no higher than ear tips; the other forepaw stays lower at the chest. Lean only slightly and return the raised paw before this segment ends. End state: The diagonal raised forepaws have returned near the chest; both cats remain balanced. 3.800–5.375s: The roommate opens both forepaws moderately to the sides below shoulder height. The protagonist now follows without the earlier delay. Make only tiny weight transfers, no lateral steps or jumping. End state: Both cats hold their forepaws moderately open below shoulder height, tails and bodies separate. 5.375–5.875s: Return the paws to the lower chest and settle. The protagonist lifts its eyes toward the roommate and looks slightly pleased, still closed-mouthed. End state: Both cats have returned their forepaws to the lower chest and settled; the protagonist looks toward its friend with slight happiness, mouths closed. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. No meows or other unrequested cat vocalizations. Within the scene, only the described voices, physical sounds and ambience are audible.
overall_soundscape: Quiet indoor room tone and only the small natural paw contacts described.
non_diegetic_music: N/A
```

## 镜头 05 · 25.625–32.917秒

请求 7.292秒；实际 175帧／7.292秒。剧情：主角尝试模仿，前爪和脚步一时配合不上；室友发现它越想记越乱，提醒它先只顾脚步。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角靠近地标，一只白后爪准备落在地标边缘，前爪轻举，脸上专注而有些迟疑；错误动作尚未完成。室友在右后方耐心看着，前爪自然放低。构图：贴近地面的中全身镜头，近处白后爪、主角脸和室友反应均清楚；前后景有层次，不将脚或耳朵裁掉。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。贴近地面的中全身镜头保持稳定，只稍推近，同时读到后爪、困惑脸和室友反应，不截脚。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–2.100秒：主角先把前爪动作做出来，脚却踏向反方向，动作很小，不摔倒。
- 2.100–4.100秒：它低头改脚步，前爪又停在半空，耳朵微微侧转，显出努力记动作的慌张。
- 4.100–5.700秒：室友温和示意它先放低前爪，说“先跟脚，别急。”
- 5.700–7.292秒：主角把前爪放低，重新站稳，只尝试一次很小的踏步。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：只在自己对白或演唱时开口

音效与音乐：同风格约96 BPM练习节奏轻放，室友安抚话语清楚；细小爪声配合协调错误和重置，不增加摔倒音效。

- 银灰室友／speech：先跟脚，别急。

### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_side]: approved side view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A floor-level medium-full view with the white hind paw nearest the lens poised at the edge of the blue marker before the coordination error. The protagonist is still visible from paws to ears above it, forepaws out of sync, brows and ear angle showing concentrated confusion rather than slapstick panic. The roommate is a distinct silver-gray figure behind on screen-right, lowering its own forepaws as a calm cue. Use a 30mm-equivalent lens and enough depth of field to read the poised paw, the protagonist face and the roommate reaction in one glance.
OPENING STATE: The protagonist is grounded near the marker with one hind paw poised at its edge and forepaws low, concentrating before the coordination error. The roommate watches patiently from screen-right behind it. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The roommate's help is patient and sincere; it does not mock or shove the protagonist; The dance error remains physically small and recoverable.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; Crossing legs into impossible knots, breaking joints, slipping across the floor or expressing distress through tears; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist is grounded near the marker with one hind paw poised at its edge and forepaws low, concentrating before the coordination error. The roommate watches patiently from screen-right behind it. Both mouths are closed. BACKGROUND:  VIEW: floor-level medium-full view emphasizing the misplaced hind paw, with the whole cat still readable. CAMERA: hold a low stable angle and make only a slight push; keep both hind paws and the confused face in frame. END STATE: a simpler, steadier starting position. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The roommate's help is patient and sincere; it does not mock or shove the protagonist; The dance error remains physically small and recoverable. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–2.100s: raise a forepaw while taking one small step in the wrong direction. End state: One forepaw and one hind paw have moved out of coordination. 2.100–4.100s: look down and correct the hind paw, inadvertently pausing the forepaw; depict one simple coordination error, not a cascade of falls. End state: The hind paw is corrected and the forepaw briefly pauses. 4.100–5.700s: the roommate lowers its own forepaws as a calm visual cue and speaks briefly. End state: The roommate has lowered its own forepaws and delivered the calm cue. 5.700–7.292s: the protagonist copies the reset, relaxes its forepaws and attempts a single small side step. End state: a simpler, steadier starting position. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate opens its mouth only for its own written speech or singing; other times it rests naturally. When the protagonist gets its paws and feet mixed up and the roommate lowers its own forepaws. Character roommate, A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. Voice: A warm, slightly husky youthful male Mandarin voice, patient and sincere, clearly distinguishable from the protagonist. (S3), with Warm, patient and reassuring., says: <d>[Chinese] 先跟脚，别急。</d> The other visible cat does not lip-sync this speaker's line. No meows or other unrequested cat vocalizations. Music audible within the scene: An unfamiliar original vocal-free hip-hop groove around 96 BPM with restrained bass, a different rhythm pattern and a clear countable pulse, played from the rehearsal speaker. The pulse stays quiet beneath the roommate's reassurance.
overall_soundscape: Two uneven paw taps followed by a small paw scrape as the protagonist resets; quiet room tone.
non_diegetic_music: N/A
```

## 镜头 06 · 32.917–40.208秒

请求 7.292秒；实际 175帧／7.292秒。剧情：主角先听拍子、轻点头，再让脚步跟上，最后才加一点摆爪；它第一次真正找到新音乐的节奏。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角位于受光的中央，双后爪稳落地，前爪放低，头微侧向音响，神态转为认真听拍，耳缘带柔和窗光。室友在右后景适度虚化。构图：左侧略斜的全身观察镜头，留出步伐空间，地标和尾巴可见，不提前画成成功舞姿。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。全身观察镜头缓慢由小斜角滑向近正面，转角不超过约15度，不用夸张绕拍。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–1.800秒：主角保持站稳，认真听新音乐，只轻轻点头两次。
- 1.800–4.600秒：它开始左右小踏步，速度比开场更从容，脚步逐渐与节奏贴合。
- 4.600–6.300秒：在稳定脚步上加两次幅度很小的前爪摆动，眼睛不再一直盯着地板。
- 6.300–7.292秒：它抬头看向室友，嘴角和耳朵放松，露出“这次跟上了”的小表情。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：无对白、无猫叫；约96 BPM练习节奏由清楚拍点渐稍丰满，对应主角找到节奏，保留自然爪落地声。


### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_side]: approved side view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A stiller three-quarter full-body profile from screen-left, 45mm-equivalent lens. The protagonist stands alone in the lit center of the rehearsal floor with both hind paws planted, forepaws relaxed, head slightly angled toward the unseen speaker. One ear rim catches warm light; its expression has shifted from frustrated to carefully listening. The roommate is only a soft silver-gray presence farther back on the right. Keep generous open floor around the body so the coming first in-time step can be seen clearly.
OPENING STATE: The protagonist stands alone in the lit central space with hind paws planted, forepaws relaxed and head angled toward the speaker. The roommate remains behind to its right. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The recognizable basic step from the demonstration; improvement is in timing and ease; The roommate stays behind and to the protagonist's right.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; A sudden professional solo, advanced footwork, costume changes, glowing effects or a victory pose; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist stands alone in the lit central space with hind paws planted, forepaws relaxed and head angled toward the speaker. The roommate remains behind to its right. Both mouths are closed. BACKGROUND:  VIEW: a clean full-body observation of a small genuine improvement. CAMERA: slowly slide from a slight three-quarter view toward a near-frontal view, within a 15-degree arc; no dramatic orbit. END STATE: still a beginner, but noticeably steadier and able to continue on the unfamiliar music. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The recognizable basic step from the demonstration; improvement is in timing and ease; The roommate stays behind and to the protagonist's right. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.800s: listen and make two tiny head nods. End state: The protagonist has heard the beat and made two small head nods. 1.800–4.600s: begin unhurried left-close-right-close steps in time with the clear pulse. End state: Its hind paws now follow the basic left-close-right-close pattern. 4.600–6.300s: add two restrained forepaw pulses while maintaining balance with the tail. End state: Two restrained forepaw pulses accompany the steadier footwork. 6.300–7.292s: lift the gaze toward the roommate and soften the expression. End state: still a beginner, but noticeably steadier and able to continue on the unfamiliar music. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. No meows or other unrequested cat vocalizations. Music audible within the scene: An unfamiliar original vocal-free hip-hop groove around 96 BPM with restrained bass, a different rhythm pattern and a clear countable pulse, played from the rehearsal speaker. The pulse becomes clearer and slightly fuller as the protagonist begins to find the rhythm.
overall_soundscape: Gradually more evenly spaced paw contacts, a quiet pleased breath and subtle rehearsal-room ambience.
non_diegetic_music: N/A
```

## 镜头 07 · 40.208–48.208秒

请求 8.000秒；实际 192帧／8.000秒。剧情：验收案例7：身份、动作及静态机位

### 首帧图提示词（中文）

固定猫眼高度中全身双猫镜头，主角在左略低耳看自己的爪，银灰室友在右耐心看它；身体、尾巴和爪彼此分离，闭嘴，柔和中性窗光，不增加服装、文字或背景角色。

### 视频生成提示词（中文审稿）

以实际首帧开始，固定斜前机位，不切镜、不换场景。动作顺序和支撑按分段，允许小幅节奏偏差，不允许身份或肢体错误。

- 0.000–3.000秒：室友轻轻点头鼓励；主角停顿后抬眼看它，不举爪、不开口。
- 3.000–8.000秒：主角眼神与耳朵角度慢慢放松为轻微开心，尾巴小幅自然动一下；两猫后爪稳落地，安静停住。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：只有柔和室内环境声和少量自然爪落地声，无对白、猫叫、演唱或未指定音乐。


### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: static.
START FRAME: Quiet photorealistic medium-full two-cat scene in the same pale dance room, neutral window fill. Protagonist screen-left with ears a little lowered and eyes down; roommate screen-right with a patient expression. Fixed 50mm view at cat eye height, forepaws and body outlines separate, clean background with no additional subject.
OPENING STATE: Both cats are grounded in a quiet medium-full two-shot; the protagonist screen-left looks down at its paws and the roommate screen-right watches patiently, both mouths closed.
BACKGROUND: 
MUST PRESERVE: The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: Extra limbs or human fingers on the cats; Merged cat paws or swapped coat markings; Mirrored duplicate cats, text, logos or watermarks; Cuts, jumps, spins or changing the room; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, static camera locked throughout the take. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: Both cats are grounded in a quiet medium-full two-shot; the protagonist screen-left looks down at its paws and the roommate screen-right watches patiently, both mouths closed. BACKGROUND:  VIEW: fixed front oblique cat shot with readable faces and paws. CAMERA: locked tripod for the complete continuous take; no motion or cut. Maintain The named cats' individual face and coat markings; Feline paws, compact bodies, grounded hind paws and separate tails; The first-frame room, lighting and left-right positions. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–3.000s: The roommate makes one small encouraging head nod. The protagonist pauses, then lifts its eyes toward the roommate without lifting its paws or opening its mouth. End state: The protagonist is looking up toward the roommate; both cats stay grounded and closed-mouthed. 3.000–8.000s: The protagonist softens its eyes and ear angle into slight relieved happiness; its tail makes one small relaxed movement. Both cats stay grounded and settle naturally. End state: The protagonist is looking toward the roommate with a small relieved expression; both are grounded with paws low and mouths closed. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. No meows or other unrequested cat vocalizations. Within the scene, only the described voices, physical sounds and ambience are audible.
overall_soundscape: Quiet indoor room tone and only the small natural paw contacts described.
non_diegetic_music: N/A
```

## 镜头 08 · 48.208–55.500秒

请求 7.292秒；实际 175帧／7.292秒。剧情：室友退到旁边，主角再次独自面对陌生音乐；它先听两拍，再接上简单动作，回应开场卡住的局面。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角独立站在地标中央，后爪稳落地，前爪放低，抬头但仍有一点紧张，准备先听拍；室友已退到右边缘观察。构图：回应第二镜的宽景与音响侧轴线，空地突出独立面对面试的主角，完整猫身与尾巴可见。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。宽景回应第二镜的失败构图，先静稳再缓慢推近约35厘米，始终保留主角全身。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–1.800秒：主角站在蓝色圆点附近，室友已退到右侧。主角短暂看向室友，再把注意力转回音乐。
- 1.800–3.300秒：它先轻点头听两拍，没有急着重复旧歌的动作。
- 3.300–6.100秒：它独自接上刚学会的左右踏步与轻摆爪，动作不复杂，但能持续。
- 6.100–7.292秒：主角稳稳收住，抬头看面试官；室友在侧面轻轻点头，不抢镜。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：无对白、无猫叫；继续约96 BPM陌生练习节奏，脚步和低位摆爪自然，不突然变熟歌或舞台演出。


### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A deliberately wide callback to the lonely floor composition of shot 2, same blue marker and speaker-side axis, but now with steadier visual balance. The protagonist is centered on the marker, hind paws grounded, chin slightly lifted and ears attentive; it waits to hear the unfamiliar beat instead of freezing. The roommate has stepped back to the far right edge, small but visibly encouraging. The empty floor now reads as space the protagonist can use, with a calm band of daylight across it. 35mm-equivalent lens, complete feline body and tail visible.
OPENING STATE: The protagonist stands independently over the blue marker, grounded and attentive with forepaws lowered. The roommate is at the far right edge. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The spatial composition recalls shot 2, making the improvement easy to compare; The roommate remains at the right edge while the protagonist completes the movement independently.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; Repeating the earlier freeze, abandoning the unfamiliar rhythm, crowd celebration or advanced acrobatics; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: The protagonist stands independently over the blue marker, grounded and attentive with forepaws lowered. The roommate is at the far right edge. Both mouths are closed. BACKGROUND:  VIEW: a visual callback to the earlier solo failure, now with quieter confidence. CAMERA: begin steady, then make a gentle 0.35m push while retaining the full body. END STATE: a believable beginner who can continue without the familiar song, not a sudden virtuoso. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The spatial composition recalls shot 2, making the improvement easy to compare; The roommate remains at the right edge while the protagonist completes the movement independently. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.800s: glance once at the roommate, then face the panel. End state: The protagonist has glanced at its friend and turned to the panel. 1.800–3.300s: listen for two beats with restrained head nods. End state: It has listened for two beats with small head nods. 3.300–6.100s: independently perform a small left-close-right-close sequence and two low forepaw pulses on the unfamiliar music. End state: It has performed the basic step independently and is finishing. 6.100–7.292s: finish in a balanced stance and look up; the roommate gives one understated nod. End state: a believable beginner who can continue without the familiar song, not a sudden virtuoso. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. No meows or other unrequested cat vocalizations. Music audible within the scene: An unfamiliar original vocal-free hip-hop groove around 96 BPM with restrained bass, a different rhythm pattern and a clear countable pulse, played from the rehearsal speaker. Remain on the unfamiliar rehearsal groove while the protagonist independently follows it.
overall_soundscape: Quiet room ambience during the initial listening pause, then a few steady paw contacts.
non_diegetic_music: N/A
```

## 镜头 09 · 55.500–62.792秒

请求 7.292秒；实际 175帧／7.292秒。剧情：面试官给出试训机会；主角先确认自己没听错，再与银灰室友轻轻碰爪。

### 首帧图提示词（中文）

横屏16:9，真实摄影质感。晴日下午的大学舞蹈社排练室，浅橡木地板、奶油色墙面、左侧高窗、右后方灰门、左墙附近黑色小音响和蓝色圆形地标。柔和窗光与室内补光一致，没有清晰镜面复制或可读文字，面试官不出镜。主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。起始状态：主角在左近处听面试官，神态期待而尚未庆祝；室友在右侧，前爪仍放低，碰爪动作尚未发生。构图：靠灰门方向的中全身双猫反应镜头，双方脸部清楚，灰门提供离开的方向；没有奖杯、证书或结果文字。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。靠门方向的中全身反应镜头，克制轻推后停住，碰爪只一次，立即分开。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–1.800秒：音乐停下，两只猫并排面对面试官，主角努力站得规矩，尾巴却轻轻摆动。
- 1.800–4.700秒：面试官画外说“下周来试训，记得多听几首歌。”主角先愣一下，再露出确认后的开心。
- 4.700–6.300秒：主角转向室友，两只猫各抬一只前爪，轻碰一下，随即放下。
- 6.300–7.292秒：两只猫朝右后方出口转身，克制着兴奋，准备离开。

嘴部规则：狸花白主角小猫：全程自然闭嘴，无喘气、牙齿或舌头；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：无音乐，面试官以固定画外声线给出试训邀请；轻微环境声和一次碰爪声，无欢呼人群或猫叫。

- 画外面试官／voiceover：下周来试训，记得多听几首歌。

### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_right45]: approved right45 view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: Photorealistic horizontal 1344x768 still in the same university dance-club audition studio: pale oak floor, cream walls, tall windows on screen-left, gray door at rear-right, a small black speaker near the left wall, and one blue circular floor marker. Warm late-afternoon daylight with soft ceiling fill; no readable signs, mirrors, extra animals or visible interviewer. A warmer medium-full reaction shot from near the rear-right door, 45mm-equivalent lens. The protagonist stands closer to the lens on screen-left, listening to the unseen interviewer, eyes attentive but still uncertain before the invitation is heard. The silver-gray roommate is beside it on the right, forepaws still lowered before a later congratulatory tap; keep a visible gap before contact. The gray door and a slice of sunlit floor give a clear exit direction. No trophy, certificate, readable text or crowd.
OPENING STATE: Both cats stand by the exit side facing the unseen panel, the protagonist screen-left and roommate screen-right, forepaws lowered, attentive and not yet celebrating. Both mouths are closed.
BACKGROUND: 
MUST PRESERVE: The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The result is a trial-practice invitation; no invented championship or award; The gray rear-right door gives the departure direction; A single gentle paw tap with separate, anatomically normal paws.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; Trophies, diplomas, readable acceptance text, a large celebration or turning the roommate into an interviewer; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: Both cats stand by the exit side facing the unseen panel, the protagonist screen-left and roommate screen-right, forepaws lowered, attentive and not yet celebrating. Both mouths are closed. BACKGROUND:  VIEW: medium-full two-shot capturing a small, credible audition result. CAMERA: a restrained slow push, then remain still for the reaction. END STATE: pleased beginners accepted for a trial practice, not competition champions. Maintain The protagonist's brown tabby crown and back, white facial blaze, chest and four white paws; The protagonist's compact feline body, pink nose, hazel eyes and fluffy ringed tail; no costume changes; The roommate's silver-gray coat, round face, black collar and round pendant whenever visible; Warm afternoon light, pale oak floor, screen-left windows and the room's spatial layout; The result is a trial-practice invitation; no invented championship or award; The gray rear-right door gives the departure direction; A single gentle paw tap with separate, anatomically normal paws. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.800s: both listen, with a tiny nervous tail movement from the protagonist. End state: Both cats wait attentively, with a small nervous tail motion. 1.800–4.700s: the offscreen invitation is heard; the protagonist registers it with a brief pause and a soft brightening expression. End state: The protagonist has registered the trial-practice invitation and brightens gently. 4.700–6.300s: turn toward each other and make one gentle forepaw tap, immediately separating; no grasping fingers. End state: One gentle paw tap is complete; the paws are separate again. 6.300–7.292s: turn toward the rear-right exit. End state: pleased beginners accepted for a trial practice, not competition champions. Character protagonist acts silently: its lips remain closed, no panting, teeth or tongue. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. When the music has stopped and both cats listen to the result. Character interviewer, An unseen university dance-club interviewer located near the camera; never a visible third cat. Voice: A calm adult female Mandarin voice, friendly and matter-of-fact, mild indoor reverberation. (S2), with Friendly, concise and matter-of-fact., says in an off-screen voiceover: <d>[Chinese] 下周来试训，记得多听几首歌。</d> The speaker remains offscreen; the visible cats do not lip-sync this voiceover. No meows or other unrequested cat vocalizations. Within the scene, only the described voices, physical sounds and ambience are audible.
overall_soundscape: Quiet room tone, small foot movements and one very soft contact when the cats tap paws.
non_diegetic_music: N/A
```

## 镜头 10 · 62.792–70.083秒

请求 7.292秒；实际 175帧／7.292秒。剧情：两只猫离开面试区后终于放松；主角问现在能否放回熟悉的歌，熟歌一响它立刻跳起来，室友笑着跟上。

### 首帧图提示词（中文）

主角为参考图中的棕灰虎斑加白小猫，白额鼻、白胸腹、四只白爪、粉鼻、榛色眼睛与环纹尾巴保持一致；不穿衣服、不戴项圈。室友为稍大、圆脸的银灰虎斑猫，黑项圈与圆吊牌只属于室友。两猫均保持猫的身体和爪型。横屏16:9，真实摄影质感。同层灰门外的走廊，左侧日光在地板形成条带，门里只露柔和虚化的排练室。主角在左，室友在右，两猫放松看向彼此，前爪低放、后爪稳站，熟歌后的舞步尚未开始。构图：温暖的双猫全身宽景，留出地面动作空间，两尾巴与猫爪分开，无路人、文字或可见播放器。 所有猫在静态首帧自然闭嘴，不露牙不伸舌；禁止字幕、水印、额外猫肢、猫爪融合、身份花纹交换及镜面复制。

### 视频生成提示词（中文审稿）

以本镜已审首帧为起点，保持身份、服装配置、场景、左右关系和光线。灰门外走廊的放松双猫全身镜头，缓慢后退约40厘米，保留门、双猫、后爪与尾巴，不切到新地点。 动作按下方分段连续完成，保留猫的体型和正常爪结构，结束状态必须稳定可读，不增加无意切镜、字幕或额外肢体。

- 0.000–1.500秒：两只猫在门外停下，主角终于放松，转头看向银灰室友。
- 1.500–3.800秒：主角带一点不好意思的笑意问“现在能放回我那首了吗？”室友看它一眼，笑着点头。
- 3.800–6.300秒：熟悉的音乐再次响起；主角立即用第一镜的小组合跳起来，动作轻松，室友跟着做一两个简单动作。
- 6.300–7.292秒：两只猫在同一拍自然停住，交换一个笑意；以轻松的小定点结束，不接字幕或片尾标志。

嘴部规则：狸花白主角小猫：只在自己对白或演唱时开口；银灰室友：全程自然闭嘴，无喘气、牙齿或舌头

音效与音乐：主角说完回收台词后，恢复原创、无演唱的约112 BPM熟悉明亮风格；爪声配合小舞步，最后一个轻重音收束。原生生成只保持风格目标，不保证跨镜同一旋律。

- 狸花白主角小猫／speech：现在能放回我那首了吗？

### 实际首帧正向／负向及 H3 提示词

```text
STYLE: Photorealistic feline fur, real photography, horizontal 16:9.
Create one static first frame. Each input photo has only its assigned role; source labels are not scene content.
INPUT IMAGE 1 [protagonist_front]: approved front view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 2 [protagonist_face]: approved face view of character protagonist for identity reference; face, coat and body only.
INPUT IMAGE 3 [roommate_front]: approved front view of character roommate for identity reference; face, coat and body only.
CHARACTER protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure.
IDENTITY TO PRESERVE: Match the protagonist references: brown-gray tabby crown and back, broad white facial blaze, white muzzle, chest, belly and all four paws; Keep the same warm hazel eyes, pink nose, small body size, ear shape and fluffy dark-ringed tail; Keep a compact feline torso, cat paws, fur-covered feline joints and exactly four limbs, even during brief upright dance poses; The protagonist has no collar, clothing, shoes or human hands; Keep the same face, coat distribution, compact body proportions and tail markings across shots.
CHARACTER roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar.
IDENTITY TO PRESERVE: silver-gray tabby coat and round face; black collar and small round pendant; solid rounded build, normal feline paws and thick ringed tail.
CAMERA MODE: follow.
START FRAME: A wide but affectionate corridor ending outside the gray rehearsal-room door, 35mm-equivalent lens. Warm daylight enters from screen-left and makes alternating bands on the hallway floor. The tabby-and-white protagonist stands on the left, shoulders relaxed after the audition, turned toward the silver-gray roommate on the right; both are poised to restart a tiny familiar dance but have not begun. Through the open doorway only a soft glimpse of the pale studio is visible. Their faces are distinct and lightly amused, with clean floor space for the callback steps, no bystanders, writing or visible music player.
OPENING STATE: Outside the gray door, the protagonist stands screen-left and the roommate screen-right, relaxed and facing one another with forepaws low. Both are grounded, not yet dancing, mouths closed.
BACKGROUND: 
MUST PRESERVE: The same protagonist, same roommate, same black collar and round pendant only on the roommate; The protagonist's prepared dance vocabulary recalls shot 1; Sunny afternoon lighting and the familiar gray doorway connect this corridor to the audition room; A lighthearted ending following a genuine trial-practice invitation.
The named cats retain compact feline bodies and normal feline paws. Their mouths are naturally closed in this opening still unless the opening state explicitly describes otherwise.

NEGATIVE:
On the named cats only: human hands replacing the cats' paws, fingers, human torsos, stretched legs, extra limbs or additional tails; Swapping the two cats' identities, transferring the roommate's collar to the protagonist, or merging their bodies; Captions, subtitles, readable signs, logos, watermarks or visible reference-sheet labels; Cuts inside this shot, teleportation, acrobatics, fast spins, falling injuries or aggressive camera shake; A new costume, a time jump to a stage show, visible phone text, end-card lettering or erasing the protagonist's improvement by making it fail again; wrong cat coat markings; human hands replacing feline paws; extra limbs on the cats; blurry fur; text; captions; logos; visible camera

For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Live-action-style photorealistic cat vlog, follow camera perspective. Fully preserve the characters, clothes and opening composition in <Picture 1>. Visible character protagonist: The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Visible character roommate: A silver-gray tabby cat with a round face, pale chest, gray-green eyes, a black collar and a small round pendant bearing a simple mountain-shaped emblem. Solid rounded feline build, ordinary cat paws and a thick ringed tail. No clothing beyond its fixed collar. FIRST-FRAME STATE: Outside the gray door, the protagonist stands screen-left and the roommate screen-right, relaxed and facing one another with forepaws low. Both are grounded, not yet dancing, mouths closed. BACKGROUND:  VIEW: a relaxed full-body two-cat ending outside the audition room. CAMERA: gently dolly backward about 0.4m, keeping the gray doorway behind them and both bodies fully visible. END STATE: happy relief and friendship; the progress from the audition remains real. Maintain The same protagonist, same roommate, same black collar and round pendant only on the roommate; The protagonist's prepared dance vocabulary recalls shot 1; Sunny afternoon lighting and the familiar gray doorway connect this corridor to the audition room; A lighthearted ending following a genuine trial-practice invitation. Only the approved first frame is supplied to this video model. Preserve appearance established there; external identity photos and motion videos are not additional video inputs. The named cats retain compact feline bodies, four normal paws each and their distinct coat markings. The camera records one continuous take. 0.000–1.500s: settle after leaving and exchange a look. End state: Both cats settle after leaving and exchange a look. 1.500–3.800s: the protagonist asks its callback line with a small bashful expression; the roommate smiles through a softened feline expression and nods once. End state: The callback question and the roommate nod have finished. 3.800–6.300s: when the familiar music returns, the protagonist performs the same small prepared steps from shot 1; the roommate joins with one or two simple matching moves. End state: The familiar small steps have been danced together. 6.300–7.292s: finish in a relaxed shared pose. End state: happy relief and friendship; the progress from the audition remains real. Character protagonist opens its mouth only for its own written speech or singing; other times it rests naturally. Character roommate acts silently: its lips remain closed, no panting, teeth or tongue. After the cats settle in the corridor and before they begin their celebration dance. Character protagonist, The same small brown-gray tabby-and-white kitten as the supplied protagonist references: broad white facial blaze, white muzzle, chest, belly and all four paws, warm hazel eyes, pink nose, tabby crown and back, fluffy dark-ringed tail. No collar, clothing or shoes. It may stand on its hind paws and make simple dance steps while retaining a compact feline torso, real cat paws and feline joint structure. Voice: A light youthful male Mandarin voice, natural conversational pacing and restrained expression. (S1), with A relieved, slightly bashful playful request., says: <d>[Chinese] 现在能放回我那首了吗？</d> The other visible cat does not lip-sync this speaker's line. No meows or other unrequested cat vocalizations. Music audible within the scene: An original vocal-free pop-funk groove around 112 BPM, clear percussion and a short bright bass motif, played from a rehearsal speaker. Return to the familiar bright style only after the protagonist finishes its request; end on a modest accent.
overall_soundscape: Quiet corridor ambience, faint indistinct campus sounds and soft paw taps with less reverberation than the rehearsal room.
non_diegetic_music: N/A
```

总长：1682帧／70.083秒。前十五秒钩子须按上方真实累计时间审查。
