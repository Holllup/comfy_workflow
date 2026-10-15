"""Build independent ComfyUI UI graphs from official Qwen and LTX subgraphs."""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path


REFERENCE_DIR = Path(__file__).parent / "references"


def _reference(name: str) -> dict:
    return json.loads((REFERENCE_DIR / name).read_text(encoding="utf-8"))


class Graph:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.definitions = {}

    def add(self, template: dict, title: str, x: int, y: int):
        node = copy.deepcopy(template)
        node["id"] = len(self.nodes) + 1
        node["title"] = title
        node["pos"] = [x, y]
        node["order"] = len(self.nodes)
        node.setdefault("flags", {})
        node.setdefault("mode", 0)
        for item in node.get("inputs", []):
            item["link"] = None
        for item in node.get("outputs", []):
            item["links"] = []
        self.nodes.append(node)
        return node

    def custom(self, kind, title, inputs, outputs, widgets, x, y, size=(360, 220)):
        template = {
            "type": kind,
            "size": list(size),
            "inputs": [{"name": name, "type": type_, "link": None} for name, type_ in inputs],
            "outputs": [{"name": name, "type": type_, "links": []} for name, type_ in outputs],
            "properties": {"Node name for S&R": kind, "cnr_id": "comfy-core" if kind in {"LoadImage", "PreviewImage", "CreateVideo", "ConcatenateVideo", "GetVideoComponents", "SaveVideo", "UNETLoader", "CLIPLoader", "VAELoader", "MiniMaxH3ImageToVideo", "BasicGuider", "BasicScheduler", "KSamplerSelect", "RandomNoise", "SamplerCustomAdvanced", "VAEDecode"} else "masterpiece_flight2"},
            "widgets_values": widgets,
        }
        return self.add(template, title, x, y)

    def reference(self, reference: dict, title: str, x: int, y: int):
        self.definitions[reference["definition"]["id"]] = reference["definition"]
        return self.add(reference["node"], title, x, y)

    def connect(self, source, source_slot: int, target, target_slot: int):
        output = source["outputs"][source_slot]
        input_ = target["inputs"][target_slot]
        kind = output["type"]
        if kind not in input_["type"].split(","):
            raise ValueError(f"Cannot connect {kind} to {target['type']}.{input_['name']}")
        if input_["link"] is not None:
            raise ValueError(f"Input already linked: {target['title']}.{input_['name']}")
        link_id = len(self.links) + 1
        self.links.append([link_id, source["id"], source_slot, target["id"], target_slot, kind])
        output["links"].append(link_id)
        input_["link"] = link_id

    def widget_link(self, source, source_slot, target, name, kind):
        target["inputs"].append({"name": name, "type": kind, "widget": {"name": name}, "link": None})
        self.connect(source, source_slot, target, len(target["inputs"]) - 1)

    def export(self, name: str):
        return {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"masterpiece-flight2-{name}-v1")),
            "revision": 0,
            "last_node_id": len(self.nodes),
            "last_link_id": len(self.links),
            "nodes": self.nodes,
            "links": self.links,
            "groups": [],
            "definitions": {"subgraphs": list(self.definitions.values())},
            "config": {},
            "extra": {"ds": {"scale": 0.65, "offset": [120, 80]}},
            "version": 0.4,
        }


def build_keyframes(story_json: str = "", project_id: str = "starry_night") -> dict:
    qwen = _reference("qwen2509_edit_subgraph.json")
    graph = Graph()
    painting = graph.custom("LoadImage", "01 上传原画", [], [("IMAGE", "IMAGE"), ("MASK", "MASK")], ["starry_night.jpg", "image"], 0, 0, (390, 410))
    prepare = graph.custom(
        "ArtPrepare", "02 项目与已审分镜", [("painting", "IMAGE")],
        [("canvas", "IMAGE"), ("story_json", "STRING"), ("project_id", "STRING")],
        [project_id, story_json, "legacy_1280x720"], 470, 0, (450, 430),
    )
    graph.connect(painting, 0, prepare, 0)
    previous = prepare
    previous_slot = 0
    for index in (4, 3, 2, 1):
        y = (4 - index) * 850
        fields = graph.custom(
            "ArtFrameText", f"关键帧 {index:02d} 提示词", [("story_json", "STRING")],
            [("image_prompt", "STRING"), ("seed", "INT")],
            [index, 487201], 1030, y, (380, 200),
        )
        graph.connect(prepare, 1, fields, 0)
        edit = graph.reference(qwen, f"关键帧 {index:02d} Qwen 画外空间", 1510, y)
        edit["size"] = [460, 650]
        graph.connect(previous, previous_slot, edit, 0)
        if index != 4:
            graph.connect(prepare, 0, edit, 1)
        graph.connect(fields, 0, edit, 3)
        graph.connect(fields, 1, edit, 6)
        save = graph.custom(
            "ArtSaveKeyframe", f"保存草稿与选定帧 {index:02d}",
            [("image", "IMAGE"), ("project_id", "STRING")],
            [("image", "IMAGE"), ("draft_path", "STRING")],
            [index], 2080, y, (400, 220),
        )
        graph.connect(edit, 0, save, 0)
        graph.connect(prepare, 2, save, 1)
        preview = graph.custom("PreviewImage", f"预览关键帧 {index:02d}", [("images", "IMAGE")], [], [], 2540, y, (360, 300))
        graph.connect(save, 0, preview, 0)
        previous, previous_slot = save, 0
    return graph.export("keyframes")


def build_keyframes_nunchaku(
    story_json: str = "",
    project_id: str = "starry_night",
    model_name: str = "svdq-int4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors",
    canvas_mode: str = "legacy_1280x720",
    spatial_mode: bool = False,
) -> dict:
    """Use the quantized Qwen edit model already present in the AutoDL image."""
    templates = {node["id"]: node for node in _reference("nunchaku_qwen2509.json")["nodes"]}
    graph = Graph()
    painting = graph.custom(
        "LoadImage", "01 上传原画", [], [("IMAGE", "IMAGE"), ("MASK", "MASK")],
        ["starry_night.jpg", "image"], 0, 0, (390, 410),
    )
    prepare = graph.custom(
        "ArtPrepare", "02 项目与已审分镜", [("painting", "IMAGE")],
        [("canvas", "IMAGE"), ("story_json", "STRING"), ("project_id", "STRING")],
        [project_id, story_json, canvas_mode], 470, 0, (450, 430),
    )
    graph.connect(painting, 0, prepare, 0)

    style_seed = None
    if spatial_mode:
        style_seed = graph.custom(
            "ArtSpatialStyleSeed", "仅提取色彩画风，不提供原画平面构图",
            [("painting", "IMAGE")], [("style_seed", "IMAGE")], [], 480, -650, (430, 200),
        )
        graph.connect(painting, 0, style_seed, 0)

    loader = graph.add(templates[115], "已安装的 Nunchaku Qwen 2509 模型", 1020, -650)
    loader["widgets_values"][0] = model_name
    sampling = graph.add(templates[66], "Qwen 采样配置", 1410, -650)
    norm = graph.add(templates[75], "Qwen CFG 校正", 1790, -650)
    clip = graph.add(templates[38], "已安装的 Qwen 文本编码器", 1020, -380)
    vae = graph.add(templates[39], "已安装的 Qwen VAE", 1410, -380)
    graph.connect(loader, 0, sampling, 0)
    graph.connect(sampling, 0, norm, 0)

    previous = style_seed if spatial_mode else prepare
    for index in (4, 3, 2, 1):
        y = (4 - index) * 960
        fields = graph.custom(
            "ArtFrameText", f"关键帧 {index:02d} 提示词", [("story_json", "STRING")],
            [("image_prompt", "STRING"), ("seed", "INT")],
            [index, 487201, spatial_mode], 1020, y, (380, 200),
        )
        graph.connect(prepare, 1, fields, 0)
        source = previous
        positive = graph.add(templates[111], f"关键帧 {index:02d} 正向提示词", 1510, y)
        negative = graph.add(templates[110], f"关键帧 {index:02d} 反向提示词", 1510, y + 300)
        positive["widgets_values"][0] = "Use connected ArtFrameText prompt for this painting."
        negative["widgets_values"][0] = (
            "No flat painting, framed artwork, canvas border, beige sidebars, static sky plate, "
            "pasted original image, cutout foreground, modern objects, text, logos, or visible drone."
            if spatial_mode else "No modern objects, text, logos, or visible drone."
        )
        encoded = graph.add(templates[88], f"关键帧 {index:02d} 编码输入图", 1980, y + 360)
        sampler = graph.add(templates[3], f"关键帧 {index:02d} Nunchaku 采样", 2360, y)
        sampler["widgets_values"][1] = "fixed"
        decoded = graph.add(templates[8], f"关键帧 {index:02d} 图像解码", 2810, y)

        graph.connect(clip, 0, positive, 0)
        graph.connect(clip, 0, negative, 0)
        graph.connect(vae, 0, positive, 1)
        graph.connect(vae, 0, negative, 1)
        graph.connect(source, 0, positive, 2)
        graph.connect(source, 0, negative, 2)
        if index != 4 and not spatial_mode:
            graph.connect(prepare, 0, positive, 3)
            graph.connect(prepare, 0, negative, 3)
        graph.widget_link(fields, 0, positive, "prompt", "STRING")
        graph.connect(source, 0, encoded, 0)
        graph.connect(vae, 0, encoded, 1)
        graph.connect(norm, 0, sampler, 0)
        graph.connect(positive, 0, sampler, 1)
        graph.connect(negative, 0, sampler, 2)
        graph.connect(encoded, 0, sampler, 3)
        graph.widget_link(fields, 1, sampler, "seed", "INT")
        graph.connect(sampler, 0, decoded, 0)
        graph.connect(vae, 0, decoded, 1)

        save = graph.custom(
            "ArtSaveKeyframe", f"保存草稿与选定帧 {index:02d}",
            [("image", "IMAGE"), ("project_id", "STRING")],
            [("image", "IMAGE"), ("draft_path", "STRING")],
            [index], 3200, y, (400, 220),
        )
        graph.connect(decoded, 0, save, 0)
        graph.connect(prepare, 2, save, 1)
        preview = graph.custom("PreviewImage", f"预览关键帧 {index:02d}", [("images", "IMAGE")], [], [], 3650, y, (360, 300))
        graph.connect(save, 0, preview, 0)
        previous = save
    return graph.export("keyframes-nunchaku")


def build_video(pilot: bool = False, project_id: str = "starry_night") -> dict:
    ltx = _reference("ltx25_flf2v_subgraph.json")
    graph = Graph()
    load = graph.custom(
        "ArtLoadApproved", "01 读取确认后的关键帧", [],
        [(f"frame_{i:02d}", "IMAGE") for i in range(1, 5)] +
        [("ending", "IMAGE"), ("story_json", "STRING"), ("project_id", "STRING")],
        [project_id], 0, 0, (430, 380),
    )
    indexes = (4,) if pilot else (1, 2, 3, 4)
    clips = []
    previous_save = None
    for row, index in enumerate(indexes):
        y = row * 860
        motion_inputs = [("story_json", "STRING")]
        if previous_save is not None:
            motion_inputs.append(("prior_video", "VIDEO"))
        motion = graph.custom(
            "ArtMotionText", f"镜头 {index:02d} 飞行与转场", motion_inputs,
            [("motion_prompt", "STRING")], [index], 520, y, (390, 230),
        )
        graph.connect(load, 5, motion, 0)
        if previous_save is not None:
            graph.connect(previous_save, 0, motion, 1)
        clip = graph.reference(ltx, f"镜头 {index:02d} LTX 首尾帧", 990, y)
        clip["size"] = [520, 670]
        clip["widgets_values"][1:7] = [False, 5, 1280, 720, 932100 + index * 101, 24]
        graph.connect(load, index - 1, clip, 0)
        graph.connect(load, index if index < 4 else 4, clip, 1)
        graph.connect(motion, 0, clip, 2)
        components = graph.custom(
            "GetVideoComponents", f"镜头 {index:02d} 去除音轨", [("video", "VIDEO")],
            [("images", "IMAGE"), ("audio", "AUDIO"), ("fps", "FLOAT"), ("bit_depth", "COMBO"), ("color_space", "COMBO")],
            [], 1580, y, (320, 200),
        )
        graph.connect(clip, 0, components, 0)
        silent = graph.custom(
            "CreateVideo", f"无声镜头 {index:02d}", [("images", "IMAGE"), ("audio", "AUDIO")],
            [("VIDEO", "VIDEO")], [24], 1970, y, (300, 160),
        )
        graph.connect(components, 0, silent, 0)
        prefix = graph.custom(
            "ArtOutputPrefix", f"镜头 {index:02d} 输出路径", [("project_id", "STRING")],
            [("prefix", "STRING")], [f"shot_{index:02d}"], 2360, y + 200, (300, 150),
        )
        graph.connect(load, 6, prefix, 0)
        save = graph.custom(
            "SaveVideo", f"保存镜头 {index:02d}", [("video", "VIDEO")],
            [("video", "VIDEO")], ["masterpiece_flight2/shot", "mp4"], 2370, y, (420, 170),
        )
        graph.connect(silent, 0, save, 0)
        graph.widget_link(prefix, 0, save, "filename_prefix", "STRING")
        clips.append(save)
        previous_save = save
    final_y = len(indexes) * 860
    hold = graph.custom("ArtHoldFrames", "原画定格 1 秒", [("image", "IMAGE")], [("images", "IMAGE")], [24], 600, final_y, (330, 160))
    graph.connect(load, 4, hold, 0)
    still = graph.custom("CreateVideo", "原画静帧视频", [("images", "IMAGE"), ("audio", "AUDIO")], [("VIDEO", "VIDEO")], [24], 1000, final_y, (330, 150))
    graph.connect(hold, 0, still, 0)
    join = graph.custom(
        "ConcatenateVideo", "拼接飞行与原画定格",
        [(f"video{i + 1}", "VIDEO") for i in range(len(clips) + 1)],
        [("VIDEO", "VIDEO")], ["auto"], 2860, 0, (450, 300),
    )
    for slot, saved in enumerate(clips):
        graph.connect(saved, 0, join, slot)
    graph.connect(still, 0, join, len(clips))
    final_prefix = graph.custom("ArtOutputPrefix", "成片输出路径", [("project_id", "STRING")], [("prefix", "STRING")], ["pilot" if pilot else "final"], 3360, 250, (300, 150))
    graph.connect(load, 6, final_prefix, 0)
    final = graph.custom("SaveVideo", "最终 MP4 保存", [("video", "VIDEO")], [("video", "VIDEO")], ["masterpiece_flight2/final", "mp4"], 3370, 0, (460, 170))
    graph.connect(join, 0, final, 0)
    graph.widget_link(final_prefix, 0, final, "filename_prefix", "STRING")
    return graph.export("pilot" if pilot else "video")


def build_video_wan(pilot: bool = False, project_id: str = "starry_night") -> dict:
    """Run the preinstalled Wan 2.2 5B I2V model with approved-frame bridges."""
    templates = {node["id"]: node for node in _reference("wan22_5b.json")["nodes"]}
    graph = Graph()
    load = graph.custom(
        "ArtLoadApproved", "01 读取确认后的关键帧", [],
        [(f"frame_{i:02d}", "IMAGE") for i in range(1, 5)] +
        [("ending", "IMAGE"), ("story_json", "STRING"), ("project_id", "STRING")],
        [project_id, "Wan2.2 5B TI2V"], 0, 0, (430, 380),
    )
    model = graph.add(templates[37], "已安装的 Wan 2.2 5B 模型", 530, -680)
    sampling = graph.add(templates[48], "Wan 采样配置", 900, -680)
    clip = graph.add(templates[38], "已安装的 UMT5 编码器", 530, -400)
    vae = graph.add(templates[39], "已安装的 Wan VAE", 900, -400)
    negative = graph.add(templates[7], "所有镜头通用反向提示词", 1290, -400)
    negative["widgets_values"][0] = (
        "modern objects, visible drone, photorealistic live action, subtitles, text, "
        "hard cut, chaotic camera shake, flicker, low quality, distorted architecture"
    )
    graph.connect(model, 0, sampling, 0)
    graph.connect(clip, 0, negative, 0)

    indexes = (4,) if pilot else (1, 2, 3, 4)
    bridged_frames = []
    previous_bridge = None
    for row, index in enumerate(indexes):
        y = row * 930
        motion_inputs = [("story_json", "STRING")]
        if previous_bridge is not None:
            motion_inputs.append(("prior_images", "IMAGE"))
        motion = graph.custom(
            "ArtMotionText", f"镜头 {index:02d} 飞行与转场", motion_inputs,
            [("motion_prompt", "STRING")], [index], 540, y, (390, 230),
        )
        graph.connect(load, 5, motion, 0)
        if previous_bridge is not None:
            graph.connect(previous_bridge, 0, motion, 1)
        positive = graph.add(templates[6], f"镜头 {index:02d} Wan 提示词", 1000, y)
        positive["widgets_values"][0] = "Use connected ArtMotionText prompt for this painting."
        graph.connect(clip, 0, positive, 0)
        graph.widget_link(motion, 0, positive, "text", "STRING")
        latent = graph.add(templates[55], f"镜头 {index:02d} 由首帧生成 5 秒", 1440, y)
        latent["widgets_values"][:3] = [1280, 704, 121]
        graph.connect(vae, 0, latent, 0)
        graph.connect(load, index - 1, latent, 1)
        sampler = graph.add(templates[3], f"镜头 {index:02d} Wan 采样", 1870, y)
        sampler["widgets_values"][0] = 932100 + index * 101
        sampler["widgets_values"][1] = "fixed"
        graph.connect(sampling, 0, sampler, 0)
        graph.connect(positive, 0, sampler, 1)
        graph.connect(negative, 0, sampler, 2)
        graph.connect(latent, 0, sampler, 3)
        decoded = graph.add(templates[8], f"镜头 {index:02d} 解码画面", 2310, y)
        graph.connect(sampler, 0, decoded, 0)
        graph.connect(vae, 0, decoded, 1)
        bridge = graph.custom(
            "ArtBridgeFrames", f"镜头 {index:02d} 接到下一关键帧",
            [("images", "IMAGE"), ("start", "IMAGE"), ("target", "IMAGE")],
            [("images", "IMAGE")], [8], 2730, y, (420, 220),
        )
        graph.connect(decoded, 0, bridge, 0)
        graph.connect(load, index - 1, bridge, 1)
        graph.connect(load, index if index < 4 else 4, bridge, 2)
        silent = graph.custom(
            "CreateVideo", f"无声 Wan 镜头 {index:02d}",
            [("images", "IMAGE"), ("audio", "AUDIO")], [("VIDEO", "VIDEO")],
            [24], 3220, y, (330, 160),
        )
        graph.connect(bridge, 0, silent, 0)
        prefix = graph.custom(
            "ArtOutputPrefix", f"Wan 镜头 {index:02d} 输出路径",
            [("project_id", "STRING")], [("prefix", "STRING")],
            [f"wan_shot_{index:02d}"], 3600, y + 210, (330, 150),
        )
        graph.connect(load, 6, prefix, 0)
        save = graph.add(templates[58], f"保存 Wan 镜头 {index:02d}", 3600, y)
        save["widgets_values"][0] = "masterpiece_flight2/wan_shot"
        graph.connect(silent, 0, save, 0)
        graph.widget_link(prefix, 0, save, "filename_prefix", "STRING")
        bridged_frames.append(bridge)
        previous_bridge = bridge

    final_y = len(indexes) * 930
    hold = graph.custom(
        "ArtHoldFrames", "原画定格 1 秒", [("image", "IMAGE")],
        [("images", "IMAGE")], [24], 1000, final_y, (330, 160),
    )
    graph.connect(load, 4, hold, 0)
    join = graph.custom(
        "ArtJoinFrames", "拼接 Wan 飞行与原画定格",
        [("clip1", "IMAGE"), ("still", "IMAGE")] +
        [(f"clip{i + 1}", "IMAGE") for i in range(1, len(bridged_frames))],
        [("images", "IMAGE")], [], 4100, 0, (450, 300),
    )
    graph.connect(bridged_frames[0], 0, join, 0)
    graph.connect(hold, 0, join, 1)
    for slot, frames in enumerate(bridged_frames[1:], start=2):
        graph.connect(frames, 0, join, slot)
    final_video = graph.custom(
        "CreateVideo", "Wan 无声成片视频", [("images", "IMAGE"), ("audio", "AUDIO")],
        [("VIDEO", "VIDEO")], [24], 4590, 0, (330, 160),
    )
    graph.connect(join, 0, final_video, 0)
    label = "wan_pilot" if pilot else "wan_final"
    final_prefix = graph.custom(
        "ArtOutputPrefix", "Wan 成片输出路径", [("project_id", "STRING")],
        [("prefix", "STRING")], [label], 5010, 230, (330, 150),
    )
    graph.connect(load, 6, final_prefix, 0)
    final = graph.add(templates[58], "最终 Wan MP4 保存", 5010, 0)
    final["widgets_values"][0] = "masterpiece_flight2/wan_final"
    graph.connect(final_video, 0, final, 0)
    graph.widget_link(final_prefix, 0, final, "filename_prefix", "STRING")
    return graph.export("wan-pilot" if pilot else "wan-video")


def build_one_pass_wan(
    story_json: str = "",
    project_id: str = "creative_flight_01",
    model_name: str = "svdq-int4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors",
) -> dict:
    """Generate four anchors and chain four Wan clips in a single ComfyUI queue."""
    keyframe_graph = build_keyframes_nunchaku(story_json, project_id, model_name)
    graph = Graph()
    graph.nodes = keyframe_graph["nodes"]
    graph.links = keyframe_graph["links"]
    prepare = next(node for node in graph.nodes if node["type"] == "ArtPrepare")
    keyframes = {
        node["widgets_values"][0]: node
        for node in graph.nodes if node["type"] == "ArtSaveKeyframe"
    }
    templates = {node["id"]: node for node in _reference("wan22_5b.json")["nodes"]}
    model = graph.add(templates[37], "已安装的 Wan 2.2 5B 模型", 4300, -680)
    sampling = graph.add(templates[48], "Wan 采样配置", 4680, -680)
    clip = graph.add(templates[38], "已安装的 UMT5 编码器", 4300, -400)
    vae = graph.add(templates[39], "已安装的 Wan VAE", 4680, -400)
    negative = graph.add(templates[7], "所有镜头通用反向提示词", 5060, -400)
    negative["widgets_values"][0] = (
        "modern objects, visible drone, photorealistic live action, subtitles, text, "
        "hard cut, chaotic camera shake, flicker, low quality, distorted architecture"
    )
    graph.connect(model, 0, sampling, 0)
    graph.connect(clip, 0, negative, 0)

    clips = []
    previous_last = None
    for index in range(1, 5):
        y = (index - 1) * 1000
        start = keyframes[1] if index == 1 else previous_last
        target = keyframes[index + 1] if index < 4 else prepare
        motion_inputs = [("story_json", "STRING")]
        if previous_last is not None:
            motion_inputs.append(("prior_images", "IMAGE"))
        motion = graph.custom(
            "ArtMotionText", f"镜头 {index:02d} 已定稿的飞行与转场", motion_inputs,
            [("motion_prompt", "STRING")], [index], 4300, y, (390, 230),
        )
        graph.connect(prepare, 1, motion, 0)
        if previous_last is not None:
            graph.connect(previous_last, 0, motion, 1)
        positive = graph.add(templates[6], f"镜头 {index:02d} Wan 提示词", 4770, y)
        positive["widgets_values"][0] = "Use connected ArtMotionText prompt for this painting."
        graph.connect(clip, 0, positive, 0)
        graph.widget_link(motion, 0, positive, "text", "STRING")
        latent = graph.add(templates[55], f"镜头 {index:02d} 从实际首帧生成", 5180, y)
        latent["widgets_values"][:3] = [1280, 704, 121]
        graph.connect(vae, 0, latent, 0)
        graph.connect(start, 0, latent, 1)
        sampler = graph.add(templates[3], f"镜头 {index:02d} Wan 采样", 5600, y)
        sampler["widgets_values"][0] = 932100 + index * 101
        sampler["widgets_values"][1] = "fixed"
        graph.connect(sampling, 0, sampler, 0)
        graph.connect(positive, 0, sampler, 1)
        graph.connect(negative, 0, sampler, 2)
        graph.connect(latent, 0, sampler, 3)
        decoded = graph.add(templates[8], f"镜头 {index:02d} 解码画面", 6020, y)
        graph.connect(sampler, 0, decoded, 0)
        graph.connect(vae, 0, decoded, 1)
        bridge = graph.custom(
            "ArtBridgeFrames", f"镜头 {index:02d} 接到预先设计的下一首帧",
            [("images", "IMAGE"), ("start", "IMAGE"), ("target", "IMAGE")],
            [("images", "IMAGE")], [8], 6450, y, (420, 220),
        )
        graph.connect(decoded, 0, bridge, 0)
        graph.connect(start, 0, bridge, 1)
        graph.connect(target, 0, bridge, 2)
        clips.append(bridge)
        if index < 4:
            last = graph.custom(
                "ArtLastFrame", f"截取镜头 {index:02d} 的实际尾帧",
                [("images", "IMAGE")], [("image", "IMAGE")], [],
                6900, y + 240, (330, 150),
            )
            graph.connect(bridge, 0, last, 0)
            previous_last = last
        video = graph.add(templates[57], f"镜头 {index:02d} 无声视频", 6900, y)
        graph.connect(bridge, 0, video, 0)
        prefix = graph.custom(
            "ArtOutputPrefix", f"镜头 {index:02d} 输出路径", [("project_id", "STRING")],
            [("prefix", "STRING")], [f"onepass_shot_{index:02d}"],
            7280, y + 210, (330, 150),
        )
        graph.connect(prepare, 2, prefix, 0)
        save = graph.add(templates[58], f"保存镜头 {index:02d}", 7280, y)
        save["widgets_values"][0] = "masterpiece_flight2/onepass_shot"
        graph.connect(video, 0, save, 0)
        graph.widget_link(prefix, 0, save, "filename_prefix", "STRING")

    hold = graph.custom(
        "ArtHoldFrames", "原画定格 1 秒", [("image", "IMAGE")],
        [("images", "IMAGE")], [24], 4300, 4250, (330, 160),
    )
    graph.connect(prepare, 0, hold, 0)
    join = graph.custom(
        "ArtJoinFrames", "按顺序拼接四镜与原画",
        [("clip1", "IMAGE"), ("still", "IMAGE"), ("clip2", "IMAGE"),
         ("clip3", "IMAGE"), ("clip4", "IMAGE")],
        [("images", "IMAGE")], [], 7740, 0, (450, 300),
    )
    graph.connect(clips[0], 0, join, 0)
    graph.connect(hold, 0, join, 1)
    for slot, frames in enumerate(clips[1:], start=2):
        graph.connect(frames, 0, join, slot)
    final_video = graph.add(templates[57], "一次运行的无声成片", 8230, 0)
    graph.connect(join, 0, final_video, 0)
    final_prefix = graph.custom(
        "ArtOutputPrefix", "成片输出路径", [("project_id", "STRING")],
        [("prefix", "STRING")], ["onepass_final"], 8610, 240, (330, 150),
    )
    graph.connect(prepare, 2, final_prefix, 0)
    final = graph.add(templates[58], "最终单工作流 MP4", 8610, 0)
    final["widgets_values"][0] = "masterpiece_flight2/onepass_final"
    graph.connect(final_video, 0, final, 0)
    graph.widget_link(final_prefix, 0, final, "filename_prefix", "STRING")
    return graph.export("one-pass-wan5b")


def build_one_pass_h3(
    story_json: str = "",
    project_id: str = "starry_h3_01",
    model_name: str = "svdq-fp4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors",
    pilot: bool = False,
    runtime: str = "cu130",
    spatial_mode: bool = True,
) -> dict:
    """Extend the existing Qwen one-pass graph with native H3 first/last-frame sampling."""
    if runtime not in ("cu130", "cu128"):
        raise ValueError("H3 runtime must be cu130 or cu128")
    diffusion_name = (
        "minimax_h3_fl2va_pruned_int8_convrot.safetensors" if runtime == "cu130"
        else "minimax_h3_fl2va_pruned_fp8_scaled.safetensors"
    )
    video_vae_name = (
        "minimax_h3_video_vae_int8_convrot.safetensors" if runtime == "cu130"
        else "minimax_h3_video_vae_fp16.safetensors"
    )
    source = build_keyframes_nunchaku(story_json, project_id, model_name, canvas_mode="h3_1344x768", spatial_mode=spatial_mode)
    graph = Graph()
    graph.nodes, graph.links = source["nodes"], source["links"]
    prepare = next(node for node in graph.nodes if node["type"] == "ArtPrepare")
    keyframes = {node["widgets_values"][0]: node for node in graph.nodes if node["type"] == "ArtSaveKeyframe"}

    stage = graph.custom(
        "ArtH3Stage", "四张关键帧完成后释放 Qwen 显存",
        [(f"frame_{index:02d}", "IMAGE") for index in range(1, 5)] + [("ending", "IMAGE")],
        [(f"frame_{index:02d}", "IMAGE") for index in range(1, 5)] + [("ending", "IMAGE")],
        [], 4300, -700, (420, 260),
    )
    for index in range(1, 5):
        graph.connect(keyframes[index], 0, stage, index - 1)
    graph.connect(prepare, 0, stage, 4)

    model = graph.custom("UNETLoader", f"MiniMax H3 FL2VA {'INT8' if runtime == 'cu130' else 'FP8'} 模型", [], [("MODEL", "MODEL")],
                         [diffusion_name, "default"], 4790, -700)
    clip = graph.custom("CLIPLoader", "MiniMax H3 Qwen3-VL 编码器", [], [("CLIP", "CLIP")],
                        ["qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "minimax", "default"], 4790, -420)
    vae = graph.custom("VAELoader", "MiniMax H3 视频 VAE", [], [("VAE", "VAE")],
                       [video_vae_name], 5170, -420)
    schedule = graph.custom("BasicScheduler", "四镜共用 20 步 simple 调度", [("model", "MODEL")],
                            [("SIGMAS", "SIGMAS")], ["simple", 20, 1], 5170, -700)
    graph.connect(model, 0, schedule, 0)
    sampler_kind = graph.custom("KSamplerSelect", "res_multistep 采样器", [], [("SAMPLER", "SAMPLER")],
                                ["res_multistep"], 5570, -700)

    clips = []
    previous_last = None
    for index in range(1, 2 if pilot else 5):
        y = (index - 1) * 1050
        start = (stage, 0) if index == 1 else (previous_last, 0)
        target = (stage, index) if index < 4 else (stage, 4)
        motion = graph.custom("ArtMotionText", f"镜头 {index:02d} 飞行路径与接点",
                              [("story_json", "STRING")], [("motion_prompt", "STRING")], [index], 4300, y, (410, 230))
        graph.connect(prepare, 1, motion, 0)
        condition = graph.custom(
            "MiniMaxH3ImageToVideo", f"镜头 {index:02d} 原生首尾帧约束",
            [("clip", "CLIP"), ("vae", "VAE"), ("first_frame", "IMAGE"), ("last_frame", "IMAGE")],
            [("positive", "CONDITIONING"), ("LATENT", "LATENT")],
            ["Use the connected ArtMotionText prompt.", 1344, 768, 124], 4770, y, (460, 370),
        )
        graph.connect(clip, 0, condition, 0)
        graph.connect(vae, 0, condition, 1)
        graph.connect(start[0], start[1], condition, 2)
        graph.connect(target[0], target[1], condition, 3)
        graph.widget_link(motion, 0, condition, "prompt", "STRING")
        guider = graph.custom("BasicGuider", f"镜头 {index:02d} H3 引导",
                              [("model", "MODEL"), ("conditioning", "CONDITIONING")],
                              [("GUIDER", "GUIDER")], [], 5300, y)
        graph.connect(model, 0, guider, 0)
        graph.connect(condition, 0, guider, 1)
        noise = graph.custom("RandomNoise", f"镜头 {index:02d} 固定种子", [], [("NOISE", "NOISE")],
                             [932100 + index * 101, "fixed"], 5300, y + 220)
        sampler = graph.custom("SamplerCustomAdvanced", f"镜头 {index:02d} H3 20 步采样",
                               [("noise", "NOISE"), ("guider", "GUIDER"), ("sampler", "SAMPLER"),
                                ("sigmas", "SIGMAS"), ("latent_image", "LATENT")],
                               [("output", "LATENT"), ("denoised_output", "LATENT")], [], 5700, y, (400, 280))
        for source_node, source_slot, target_slot in ((noise, 0, 0), (guider, 0, 1), (sampler_kind, 0, 2),
                                                       (schedule, 0, 3), (condition, 1, 4)):
            graph.connect(source_node, source_slot, sampler, target_slot)
        decoded = graph.custom("VAEDecode", f"镜头 {index:02d} H3 原始画面",
                               [("samples", "LATENT"), ("vae", "VAE")], [("IMAGE", "IMAGE")], [], 6150, y)
        graph.connect(sampler, 0, decoded, 0)
        graph.connect(vae, 0, decoded, 1)
        raw = graph.custom("ArtLastFrame", f"镜头 {index:02d} 原始生成尾帧",
                           [("images", "IMAGE")], [("image", "IMAGE")], [], 6520, y + 250)
        graph.connect(decoded, 0, raw, 0)
        audit = graph.custom("ArtH3Audit", f"镜头 {index:02d} 原始尾帧偏差与 PNG",
                             [("raw_last", "IMAGE"), ("target", "IMAGE"), ("project_id", "STRING")],
                             [("raw_last", "IMAGE")], [index], 6890, y + 250)
        graph.connect(raw, 0, audit, 0)
        graph.connect(target[0], target[1], audit, 1)
        graph.connect(prepare, 2, audit, 2)
        bridge = graph.custom("ArtH3Bridge", f"镜头 {index:02d} 接点安全校正",
                              [("images", "IMAGE"), ("start", "IMAGE"), ("target", "IMAGE"),
                               ("audit", "IMAGE"), ("story_json", "STRING"), ("project_id", "STRING")],
                              [("images", "IMAGE")], [index, 2 if spatial_mode else 4], 7280, y, (440, 250))
        for source_node, source_slot, slot in ((decoded, 0, 0), (start[0], start[1], 1),
                                               (target[0], target[1], 2), (audit, 0, 3),
                                               (prepare, 1, 4), (prepare, 2, 5)):
            graph.connect(source_node, source_slot, bridge, slot)
        clips.append(bridge)
        if index < 4:
            previous_last = graph.custom("ArtLastFrame", f"镜头 {index:02d} 桥接后尾帧供下一镜使用",
                                         [("images", "IMAGE")], [("image", "IMAGE")], [], 7760, y + 250)
            graph.connect(bridge, 0, previous_last, 0)
        video = graph.custom("CreateVideo", f"镜头 {index:02d} 无声视频", [("images", "IMAGE")],
                             [("VIDEO", "VIDEO")], [24, 8], 7760, y)
        graph.connect(bridge, 0, video, 0)
        prefix = graph.custom("ArtOutputPrefix", f"H3 镜头 {index:02d} 路径", [("project_id", "STRING")],
                              [("prefix", "STRING")], [f"h3_shot_{index:02d}"], 8130, y + 230)
        graph.connect(prepare, 2, prefix, 0)
        save = graph.custom("SaveVideo", f"保存 H3 镜头 {index:02d}", [("video", "VIDEO")], [],
                            ["masterpiece_flight2/h3_shot", "auto", "auto"], 8140, y)
        graph.connect(video, 0, save, 0)
        graph.widget_link(prefix, 0, save, "filename_prefix", "STRING")

    if pilot:
        suffix = "-spatial" if spatial_mode else ""
        return graph.export(("h3-single-shot-pilot" if runtime == "cu130" else "h3-cu128-single-shot-pilot") + suffix)

    hold = graph.custom("ArtHoldFrames", "同一原画画布定格 24 帧", [("image", "IMAGE")],
                        [("images", "IMAGE")], [24], 4300, 4300)
    graph.connect(stage, 4, hold, 0)
    join = graph.custom("ArtJoinFrames", "镜头 1→2→3→4→原画",
                        [("clip1", "IMAGE"), ("still", "IMAGE"), ("clip2", "IMAGE"),
                         ("clip3", "IMAGE"), ("clip4", "IMAGE")], [("images", "IMAGE")], [], 8580, 0)
    graph.connect(clips[0], 0, join, 0)
    graph.connect(hold, 0, join, 1)
    for slot, item in enumerate(clips[1:], start=2):
        graph.connect(item, 0, join, slot)
    delivery = graph.custom("ArtDeliveryCanvas", "仅成片一次留边转换 1280×720",
                            [("images", "IMAGE"), ("original", "IMAGE")], [("images", "IMAGE")], [], 9010, 0)
    graph.connect(join, 0, delivery, 0)
    graph.connect(stage, 4, delivery, 1)
    video = graph.custom("CreateVideo", "H3 无声最终成片", [("images", "IMAGE")],
                         [("VIDEO", "VIDEO")], [24, 8], 9440, 0)
    graph.connect(delivery, 0, video, 0)
    prefix = graph.custom("ArtOutputPrefix", "H3 最终成片路径", [("project_id", "STRING")],
                          [("prefix", "STRING")], ["h3_final"], 9790, 230)
    graph.connect(prepare, 2, prefix, 0)
    final = graph.custom("SaveVideo", "保存 H3 最终 MP4", [("video", "VIDEO")], [],
                         ["masterpiece_flight2/h3_final", "auto", "auto"], 9800, 0)
    graph.connect(video, 0, final, 0)
    graph.widget_link(prefix, 0, final, "filename_prefix", "STRING")
    suffix = "-spatial" if spatial_mode else ""
    return graph.export(("one-pass-h3" if runtime == "cu130" else "one-pass-h3-cu128") + suffix)


def write_workflows(directory: Path, story_json: str = "") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, workflow in (
        ("00_one_pass_wan5b.json", build_one_pass_wan("")),
        ("00_one_pass_minimax_h3.json", build_one_pass_h3("")),
        ("00_one_pass_minimax_h3_cu128.json", build_one_pass_h3("", runtime="cu128")),
        ("00_one_pass_minimax_h3_spatial_cu128.json", build_one_pass_h3("", runtime="cu128", spatial_mode=True)),
        ("00_pilot_minimax_h3.json", build_one_pass_h3("", pilot=True)),
        ("00_pilot_minimax_h3_cu128.json", build_one_pass_h3("", pilot=True, runtime="cu128")),
        ("00_pilot_minimax_h3_spatial_cu128.json", build_one_pass_h3("", pilot=True, runtime="cu128", spatial_mode=True)),
        ("01_keyframes.json", build_keyframes(story_json)),
        ("01_keyframes_nunchaku.json", build_keyframes_nunchaku(story_json)),
        ("02_pilot_5s.json", build_video(pilot=True)),
        ("02_pilot_wan5b.json", build_video_wan(pilot=True)),
        ("03_full_20s.json", build_video()),
        ("03_full_wan5b.json", build_video_wan()),
    ):
        (directory / filename).write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
