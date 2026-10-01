"""Build a ComfyUI UI workflow from the templates installed in AutoDL v22."""

import copy
import json
import uuid
from pathlib import Path


REFERENCE_DIR = Path(__file__).resolve().parent.parent / "references"


class Graph:
    def __init__(self):
        self.nodes = []
        self.links = []
        self.groups = []
        self.node_id = 0
        self.link_id = 0

    def add_node(self, node):
        self.node_id += 1
        node = copy.deepcopy(node)
        node["id"] = self.node_id
        self.nodes.append(node)
        return node

    def add_template(self, filename, x, y, excluded=(), reuse=None):
        source = json.loads((REFERENCE_DIR / filename).read_text())
        reuse = reuse or {}
        mapping = dict(reuse)
        for old in source["nodes"]:
            if old["type"] in excluded or old["id"] in reuse:
                continue
            node = self.add_node(old)
            node["pos"] = [old["pos"][0] + x, old["pos"][1] + y]
            for item in node.get("inputs", []):
                item["link"] = None
            for item in node.get("outputs", []):
                item["links"] = [] if item.get("links") is not None else None
            mapping[old["id"]] = node
        for _, origin, origin_slot, target, target_slot, kind in source["links"]:
            if origin in mapping and target in mapping and not (origin in reuse and target in reuse):
                self.connect(mapping[origin], origin_slot, mapping[target], target_slot, kind)
        return mapping

    def connect(self, origin, origin_slot, target, target_slot, kind):
        self.link_id += 1
        link = self.link_id
        self.links.append([link, origin["id"], origin_slot, target["id"], target_slot, kind])
        output = origin["outputs"][origin_slot]
        if output.get("links") is None:
            output["links"] = []
        output["links"].append(link)
        target["inputs"][target_slot]["link"] = link

    def custom(self, node_type, title, inputs, outputs, widgets, x, y):
        return self.add_node({
            "id": 0, "type": node_type, "title": title, "pos": [x, y],
            "size": [330, 180], "flags": {}, "order": 0, "mode": 0,
            "inputs": [{"name": name, "type": kind, "link": None} for name, kind in inputs],
            "outputs": [{"name": name, "type": kind, "links": []} for name, kind in outputs],
            "properties": {"Node name for S&R": node_type},
            "widgets_values": widgets,
        })

    def widget_link(self, origin, origin_slot, target, name, kind):
        target["inputs"].append({"name": name, "type": kind, "widget": {"name": name}, "link": None})
        self.connect(origin, origin_slot, target, len(target["inputs"]) - 1, kind)

    def as_dict(self):
        return {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "cat-vlog-six-shot-v1")),
            "last_node_id": self.node_id, "last_link_id": self.link_id,
            "nodes": self.nodes, "links": self.links, "groups": self.groups,
            "config": {}, "extra": {}, "version": 0.4,
        }


def build_workflow():
    graph = Graph()
    planner = graph.custom(
        "CatStoryPlanner", "01 · 随机生成六镜剧情", [],
        [("story_json", "STRING"), ("run_id", "STRING"), ("run_seed", "INT")],
        ["小猫的一天", True, 0], 0, -600,
    )
    z_nodes = graph.add_template("z_image.json", 0, 0, excluded=("MarkdownNote", "SaveImage"))
    z_nodes[45]["widgets_values"][0] = (
        "Photorealistic portrait of one small orange-and-white short-haired kitten, "
        "clear green eyes, narrow blue collar, recognizable white blaze on the nose "
        "and white front paws. The cat looks into a handheld selfie camera, natural "
        "feline anatomy, exactly four legs, one tail, soft daylight, no text."
    )
    z_nodes[41]["widgets_values"] = [704, 1280, 1]
    z_nodes[44]["widgets_values"][:2] = [8675309, "fixed"]
    reference = graph.custom(
        "CatReference", "02 · 首次生成并锁定小猫定妆照",
        [("generated", "IMAGE")], [("image", "IMAGE")], [], 850, 0,
    )
    graph.connect(z_nodes[43], 0, reference, 0, "IMAGE")
    reference_preview = graph.custom(
        "PreviewImage", "主角定妆照预览",
        [("images", "IMAGE")], [], [], 1180, 300,
    )
    reference_preview["size"] = [360, 280]
    graph.connect(reference, 0, reference_preview, 0, "IMAGE")
    qwen_reuse = {}
    wan_reuse = {}
    saved_frames = []
    saved_clips = []
    video_gates = []
    for index in range(1, 7):
        y = index * 1100
        graph.groups.append({
            "id": index, "title": f"分镜 {index:02}",
            "bounding": [950, y - 330, 5100, 980],
            "color": "#446a87" if index % 2 else "#655787",
            "font_size": 30, "flags": {},
        })
        fields = graph.custom(
            "CatShotFields", f"分镜 {index} · 剧情与提示词",
            [("story_json", "STRING"), ("run_seed", "INT")],
            [("image_prompt", "STRING"), ("motion_prompt", "STRING"),
             ("image_seed", "INT"), ("video_seed", "INT")],
            [index], 1050, y,
        )
        graph.connect(planner, 0, fields, 0, "STRING")
        graph.connect(planner, 2, fields, 1, "INT")
        image_gate = graph.custom(
            "CatImageGate", f"分镜 {index} · 首帧顺序门",
            [("prompt", "STRING"), ("seed", "INT"), ("prior", "STRING")],
            [("prompt", "STRING"), ("seed", "INT")], [index], 1700, y,
        )
        graph.connect(fields, 0, image_gate, 0, "STRING")
        graph.connect(fields, 2, image_gate, 1, "INT")
        if saved_frames:
            graph.connect(saved_frames[-1], 1, image_gate, 2, "STRING")
        else:
            graph.connect(planner, 1, image_gate, 2, "STRING")
        image_nodes = graph.add_template(
            "qwen_edit.json", 1300, y,
            excluded=("MarkdownNote", "LoadImage", "SaveImage", "EmptySD3LatentImage"),
            reuse=qwen_reuse,
        )
        if not qwen_reuse:
            qwen_reuse = {old: image_nodes[old] for old in (115, 66, 75, 38, 39, 93, 88)}
            graph.connect(reference, 0, image_nodes[93], 0, "IMAGE")
            image_nodes[115]["widgets_values"][0] = (
                "svdq-int4_r128-qwen-image-edit-2509-lightning-4steps-251115.safetensors"
            )
        graph.widget_link(image_gate, 0, image_nodes[111], "prompt", "STRING")
        graph.widget_link(image_gate, 1, image_nodes[3], "seed", "INT")
        save_frame = graph.custom(
            "CatSaveFrame", f"分镜 {index} · 保存首帧",
            [("image", "IMAGE"), ("run_id", "STRING")],
            [("image", "IMAGE"), ("done", "STRING")], [index], 2800, y,
        )
        graph.connect(image_nodes[8], 0, save_frame, 0, "IMAGE")
        graph.connect(planner, 1, save_frame, 1, "STRING")
        frame_preview = graph.custom(
            "PreviewImage", f"分镜 {index} · 首帧预览",
            [("images", "IMAGE")], [], [], 3100, y + 180,
        )
        frame_preview["size"] = [360, 280]
        graph.connect(save_frame, 0, frame_preview, 0, "IMAGE")
        saved_frames.append(save_frame)
        video_gate = graph.custom(
            "CatVideoGate", f"分镜 {index} · 视频顺序门",
            [("prompt", "STRING"), ("seed", "INT"), ("prior", "STRING")],
            [("prompt", "STRING"), ("seed", "INT")], [index], 3500, y,
        )
        graph.connect(fields, 1, video_gate, 0, "STRING")
        graph.connect(fields, 3, video_gate, 1, "INT")
        if saved_clips:
            graph.connect(saved_clips[-1], 0, video_gate, 2, "STRING")
        video_gates.append(video_gate)
        video_nodes = graph.add_template(
            "wan5b.json", 3800, y,
            excluded=("MarkdownNote", "LoadImage", "CreateVideo", "SaveVideo"),
            reuse=wan_reuse,
        )
        if not wan_reuse:
            wan_reuse = {old: video_nodes[old] for old in (37, 38, 39, 48, 7)}
        video_nodes[55]["widgets_values"][:3] = [704, 1280, 121]
        graph.connect(save_frame, 0, video_nodes[55], 1, "IMAGE")
        graph.widget_link(video_gate, 0, video_nodes[6], "text", "STRING")
        graph.widget_link(video_gate, 1, video_nodes[3], "seed", "INT")
        save_clip = graph.custom(
            "CatSaveClip", f"分镜 {index} · 保存视频",
            [("images", "IMAGE"), ("run_id", "STRING")],
            [("done", "STRING")], [index], 5400, y,
        )
        graph.connect(video_nodes[8], 0, save_clip, 0, "IMAGE")
        graph.connect(planner, 1, save_clip, 1, "STRING")
        saved_clips.append(save_clip)
    graph.connect(saved_frames[-1], 1, video_gates[0], 2, "STRING")
    finish = graph.custom(
        "CatFinish", "07 · 合成三十秒成片",
        [(f"clip_{index}", "STRING") for index in range(1, 7)]
        + [("story_json", "STRING"), ("run_id", "STRING")],
        [("final_path", "STRING")], [], 6500, 3500,
    )
    for slot, clip in enumerate(saved_clips):
        graph.connect(clip, 0, finish, slot, "STRING")
    graph.connect(planner, 0, finish, 6, "STRING")
    graph.connect(planner, 1, finish, 7, "STRING")
    return graph.as_dict()
