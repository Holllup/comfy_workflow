"""Build a painting-flight ComfyUI graph from official LTX and Qwen subgraphs."""

import copy
import json
import uuid
from pathlib import Path


REFERENCE_DIR = Path(__file__).resolve().parents[1] / "references"
QWEN_TYPE = "eba40a3a-f6c5-48ac-b58e-55525d06b373"
LTX_TYPE = "cf70afc4-5a03-47ce-8210-734b1de6c6bc"


def _reference(filename):
    return json.loads((REFERENCE_DIR / filename).read_text(encoding="utf-8"))


class Graph:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.groups = []

    def add(self, source, x, y, title=None):
        node = copy.deepcopy(source)
        node["id"] = len(self.nodes) + 1
        node["pos"] = [x, y]
        node["order"] = len(self.nodes)
        if title:
            node["title"] = title
        for entry in node.get("inputs", []):
            entry["link"] = None
        for entry in node.get("outputs", []):
            entry["links"] = []
        self.nodes.append(node)
        return node

    def custom(self, node_type, title, inputs, outputs, widgets, x, y, size=(360, 220)):
        return self.add({
            "type": node_type, "title": title, "size": list(size), "flags": {},
            "mode": 0,
            "inputs": [{"name": name, "type": kind, "link": None} for name, kind in inputs],
            "outputs": [{"name": name, "type": kind, "links": []} for name, kind in outputs],
            "properties": {"Node name for S&R": node_type},
            "widgets_values": widgets,
        }, x, y)

    def connect(self, origin, origin_slot, target, target_slot):
        output = origin["outputs"][origin_slot]
        input_ = target["inputs"][target_slot]
        kind = output["type"]
        if kind not in input_["type"].split(","):
            raise ValueError(f"Cannot connect {kind} to {target['type']}.{input_['name']}")
        if input_["link"] is not None:
            raise ValueError(f"Input already connected: {target['type']}.{input_['name']}")
        link_id = len(self.links) + 1
        self.links.append([link_id, origin["id"], origin_slot, target["id"], target_slot, kind])
        output["links"].append(link_id)
        input_["link"] = link_id

    def export(self, definitions, shot_count):
        return {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"masterpiece-flight-{shot_count}-v1")),
            "revision": 0, "last_node_id": len(self.nodes),
            "last_link_id": len(self.links), "nodes": self.nodes, "links": self.links,
            "groups": self.groups, "definitions": {"subgraphs": definitions},
            "config": {}, "extra": {"ds": {"scale": 0.7, "offset": [120, 60]}},
            "version": 0.4,
        }


def build_workflow(shot_count=4):
    """Build the 4 × 5-second production graph or a one-shot pilot."""
    if shot_count not in (1, 4):
        raise ValueError("shot_count must be 1 or 4")
    qwen = _reference("qwen2509_edit_subgraph.json")
    ltx = _reference("ltx25_flf2v_subgraph.json")
    graph = Graph()
    painting = graph.custom(
        "LoadImage", "01 · 上传原画", [], [("IMAGE", "IMAGE"), ("MASK", "MASK")],
        ["masterpiece.png", "image"], 0, 0, (360, 420))
    painting["properties"]["cnr_id"] = "comfy-core"
    canvas = graph.custom(
        "ArtFrameCanvas", "02 · 完整原画放入 1280×720",
        [("painting", "IMAGE")], [("image", "IMAGE")],
        [1280, 720], 450, 0)
    graph.connect(painting, 0, canvas, 0)
    planner = graph.custom(
        "ArtStoryPlanner", "03 · 看图编写空间穿行分镜",
        [("painting", "IMAGE")], [("story_json", "STRING")],
        ["星月夜", "文森特·梵高", "1889", "法国圣雷米；画面含想象组合",
         "受画作启发的想象重构",
         "保留夜空旋涡、柏树、村庄和教堂；低空飞行，穿过柏树遮挡后抵达原画视角",
         shot_count, True, 0],
        0, 550, (430, 470))
    graph.connect(painting, 0, planner, 0)

    frames = []
    fields = []
    for index in range(shot_count):
        y = 1200 + index * 850
        graph.groups.append({
            "id": index + 1, "title": f"镜头 {index + 1:02d} · 关键帧与飞行",
            "bounding": [410, y - 130, 2300, 760],
            "color": "#446a87" if index % 2 == 0 else "#665184",
            "font_size": 30, "flags": {},
        })
        field = graph.custom(
            "ArtShotFields", f"镜头 {index + 1} · 提示词",
            [("story_json", "STRING")],
            [("keyframe_prompt", "STRING"), ("motion_prompt", "STRING"), ("image_seed", "INT")],
            [index + 1], 450, y)
        graph.connect(planner, 0, field, 0)
        fields.append(field)
        frame = graph.add(qwen["node"], 900, y, f"镜头 {index + 1} · AI 空间关键帧")
        frame["size"] = [410, 680]
        source = canvas if index == 0 or index == shot_count - 1 else frames[-1]
        graph.connect(source, 0, frame, 0)
        if index:
            graph.connect(frames[-1] if index == shot_count - 1 else canvas, 0, frame, 1)
        graph.connect(field, 0, frame, 3)
        graph.connect(field, 2, frame, 6)
        frames.append(frame)
        preview = graph.custom(
            "PreviewImage", f"预览关键帧 {index + 1}",
            [("images", "IMAGE")], [], [], 1360, y + 340, (350, 280))
        graph.connect(frame, 0, preview, 0)

    clips = []
    for index in range(shot_count):
        y = 1200 + index * 850
        clip = graph.add(ltx["node"], 1780, y, f"镜头 {index + 1} · 5秒飞行")
        clip["size"] = [500, 680]
        clip["widgets_values"][1:7] = [False, 5, 1280, 720, 409600 + 1009 * index, 24]
        graph.connect(frames[index], 0, clip, 0)
        graph.connect(frames[index + 1] if index < shot_count - 1 else canvas, 0, clip, 1)
        graph.connect(fields[index], 1, clip, 2)
        clips.append(clip)

    y = 1200 + shot_count * 850
    hold = graph.custom(
        "ArtHoldFrames", "04 · 原画定格 1 秒",
        [("image", "IMAGE")], [("images", "IMAGE")], [24], 900, y)
    graph.connect(canvas, 0, hold, 0)
    still = graph.custom(
        "CreateVideo", "原画静帧视频",
        [("images", "IMAGE"), ("audio", "AUDIO")],
        [("VIDEO", "VIDEO")], [24], 1360, y)
    graph.connect(hold, 0, still, 0)
    joined = graph.custom(
        "ConcatenateVideo", "05 · 顺序拼接",
        [(f"video{i + 1}", "VIDEO") for i in range(shot_count + 1)],
        [("VIDEO", "VIDEO")], ["auto"], 2820, 1200 + (shot_count - 1) * 850)
    joined["properties"]["cnr_id"] = "comfy-core"
    for index, clip in enumerate(clips):
        graph.connect(clip, 0, joined, index)
    graph.connect(still, 0, joined, shot_count)
    save = graph.custom(
        "SaveVideo", "06 · 保存完整 MP4",
        [("video", "VIDEO")], [("video", "VIDEO")],
        ["masterpiece_flight/final", "auto", "auto"],
        3360, 1200 + (shot_count - 1) * 850, (600, 160))
    save["properties"]["cnr_id"] = "comfy-core"
    graph.connect(joined, 0, save, 0)
    return graph.export([qwen["definition"], ltx["definition"]], shot_count)
