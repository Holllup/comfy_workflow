"""Build standalone ComfyUI UI graphs for a reviewed first-frame MiniMax H3 cat vlog."""

from __future__ import annotations

import copy
import json
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parent
JOYAI_REFERENCE = ROOT / "references" / "joyai_edit_plus_official.json"
JOYAI_MODEL = "joyai_image_edit_plus_bf16.safetensors"
JOYAI_CLIP = "qwen3vl_8b_joyimage_edit_plus_bf16.safetensors"
JOYAI_VAE = "wan_2.1_vae.safetensors"
H3_MODEL = "minimax_h3_fl2va_pruned_fp8_scaled.safetensors"
H3_CLIP = "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
H3_VIDEO_VAE = "minimax_h3_video_vae_fp16.safetensors"
H3_AUDIO_VAE = "minimax_h3_audio_vae_fp32.safetensors"


class Graph:
    def __init__(self):
        self.nodes = []
        self.links = []

    def add(self, template: dict, title: str, x: int, y: int) -> dict:
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

    def custom(self, kind: str, title: str, inputs, outputs, widgets, x: int, y: int, size=(360, 200)) -> dict:
        builtin = {
            "UNETLoader", "CLIPLoader", "VAELoader", "MiniMaxH3ImageToVideo",
            "BasicScheduler", "KSamplerSelect", "RandomNoise", "BasicGuider",
            "SamplerCustomAdvanced", "VAEDecode", "VAEDecodeAudio", "PreviewImage",
        }
        template = {
            "type": kind,
            "size": list(size),
            "inputs": [{"name": name, "type": type_, "link": None} for name, type_ in inputs],
            "outputs": [{"name": name, "type": type_, "links": []} for name, type_ in outputs],
            "properties": {"Node name for S&R": kind, "cnr_id": "comfy-core" if kind in builtin else "cat_vlog_h3"},
            "widgets_values": list(widgets),
        }
        return self.add(template, title, x, y)

    def connect(self, source: dict, source_slot: int, target: dict, target_slot: int):
        output = source["outputs"][source_slot]
        input_ = target["inputs"][target_slot]
        if output["type"] not in input_["type"].split(","):
            raise ValueError(f"Cannot connect {output['type']} to {target['type']}.{input_['name']}")
        if input_["link"] is not None:
            raise ValueError(f"Input already linked: {target['title']}.{input_['name']}")
        link_id = len(self.links) + 1
        self.links.append([link_id, source["id"], source_slot, target["id"], target_slot, output["type"]])
        output["links"].append(link_id)
        input_["link"] = link_id

    def widget_link(self, source: dict, source_slot: int, target: dict, name: str, type_: str):
        for index, port in enumerate(target["inputs"]):
            if port["name"] == name:
                if port["type"] != type_:
                    raise ValueError(f"Widget input type changed: {target['title']}.{name}")
                self.connect(source, source_slot, target, index)
                return
        target["inputs"].append({"name": name, "type": type_, "widget": {"name": name}, "link": None})
        self.connect(source, source_slot, target, len(target["inputs"]) - 1)

    def export(self) -> dict:
        label = "reviewed-first-frames-joyai-bf16-v4"
        return {
            "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"cat-vlog-h3-{label}-cu128-v4")),
            "revision": 0,
            "last_node_id": len(self.nodes),
            "last_link_id": len(self.links),
            "nodes": self.nodes,
            "links": self.links,
            "groups": [],
            "config": {},
            "extra": {"ds": {"scale": 0.45, "offset": [120, 80]}},
            "version": 0.4,
        }


def _connect_joyai_text(graph, template, clip, vae, image_sources, fields, prompt_slot, title, x, y, negative=False):
    node = graph.custom('CatH3JoyEncode', title, [('clip', 'CLIP'), ('vae', 'VAE'), ('prompt', 'STRING'), ('references', 'CAT_SHOT_REFERENCES')],
                        [('CONDITIONING', 'CONDITIONING')], [], x, y, (430, 220))
    graph.connect(clip, 0, node, 0)
    graph.connect(vae, 0, node, 1)
    source, slot = image_sources[0]
    graph.connect(source, slot, node, 3)
    graph.connect(fields, 5 if negative else prompt_slot, node, 2)
    return node


def build_workflow(story_json: str = "", run_id: str = "cat_vlog_joyai_01") -> dict:
    from .nodes import REVIEW
    official = json.loads(JOYAI_REFERENCE.read_text(encoding="utf-8"))
    templates = {node["id"]: node for node in official["definitions"]["subgraphs"][0]["nodes"]}
    graph = Graph()

    def wire(source, slot, target, name):
        graph.connect(source, slot, target, next(i for i, p in enumerate(target["inputs"]) if p["name"] == name))

    story = graph.custom(
        "CatH3Story", "01 通用剧本与阶段：先选1审图，通过后选2再点Run", [("references", "CAT_REFERENCES")],
        [("story_json", "STRING"), ("run_id", "STRING"), ("seed_base", "INT"), ("phase", "STRING"), ("context", "STRING"), ('selected_shots', 'STRING')],
        [story_json, run_id, 482701, REVIEW, 'all', 'pending'], 0, -650, (600, 750),
    )
    references = graph.custom(
        "CatH3References", "02 通用参考库：身份／服装／场景", [],
        [("references", "CAT_REFERENCES")],
        [], 0, 100, (600, 670),
    )
    wire(references, 0, story, "references")
    joy_model = graph.add(templates[3], "JoyAI Plus BF16（仅阶段1）", 1050, -650)
    joy_model["widgets_values"] = [JOYAI_MODEL, "default"]
    norm = graph.add(templates[12], "JoyAI CFG 校正", 1440, -650)
    graph.connect(joy_model, 0, norm, 0)
    joy_clip = graph.add(templates[4], "JoyAI 专用文本编码器", 1050, -400)
    joy_clip["widgets_values"] = [JOYAI_CLIP, "joyimage", "default"]
    joy_vae = graph.add(templates[5], "JoyAI Wan VAE", 1440, -400)
    joy_vae["widgets_values"] = [JOYAI_VAE]
    fields, saved = {}, {}
    for index in range(1, 11):
        y = (index - 1) * 850
        field = graph.custom(
            "CatH3ShotFields", f"镜头 {index:02d} 提示词；增加 variation 重画本镜",
            [("story_json", "STRING"), ("seed_base", "INT")],
            [("start_prompt", "STRING"), ("video_prompt", "STRING"), ("start_seed", "INT"), ("video_seed", "INT"), ("frame_key", "STRING"), ("negative_prompt", "STRING"), ('frame_count', 'INT'), ('video_key', 'STRING')],
            [index, 0], 680, y, (430, 260),
        )
        graph.connect(story, 0, field, 0)
        graph.connect(story, 2, field, 1)
        fields[index] = field
        select = graph.custom(
            "CatH3SelectReferences", f"镜头 {index:02d} 选择实际参考图与用途",
            [("story_json", "STRING"), ("references", "CAT_REFERENCES")],
            [('selected_photos', 'CAT_SHOT_REFERENCES')], [index], 1150, y, (440, 310),
        )
        graph.connect(story, 0, select, 0)
        wire(references, 0, select, "references")
        positive = _connect_joyai_text(graph, templates[6], joy_clip, joy_vae, [(select, 0)], field, 0,
                                      f"镜头 {index:02d} 首帧正向", 1630, y)
        negative = _connect_joyai_text(graph, templates[7], joy_clip, joy_vae, [(select, 0)], field, 0,
                                      f"镜头 {index:02d} 首帧负向", 1630, y + 280, negative=True)
        latent = graph.add(templates[8], f"镜头 {index:02d} 空白首帧画布", 2060, y + 300)
        latent["widgets_values"] = [1344, 768, 1]
        sample = graph.add(templates[10], f"镜头 {index:02d} 生成首帧（40步）", 2450, y)
        sample["widgets_values"] = [42, "fixed", 40, 4.0, "euler", "normal", 1]
        for source, source_slot, target_slot in ((norm, 0, 0), (positive, 0, 1), (negative, 0, 2), (latent, 0, 3)):
            graph.connect(source, source_slot, sample, target_slot)
        graph.widget_link(field, 2, sample, "seed", "INT")
        decode = graph.add(templates[11], f"镜头 {index:02d} 解码首帧", 2840, y)
        graph.connect(sample, 0, decode, 0)
        graph.connect(joy_vae, 0, decode, 1)
        save = graph.custom(
            "CatH3SaveFrame", f"镜头 {index:02d} 首帧预览：阶段2读取这张已保存图片",
            [("run_id", "STRING"), ("phase", "STRING"), ("context", "STRING"), ("frame_key", "STRING"), ("image", "IMAGE"), ('selected_shots', 'STRING')],
            [("image", "IMAGE"), ("path", "STRING")], [index], 3230, y, (480, 510),
        )
        for slot, name in ((1, "run_id"), (3, "phase"), (4, "context")):
            wire(story, slot, save, name)
        wire(field, 4, save, "frame_key")
        wire(story, 5, save, 'selected_shots')
        wire(decode, 0, save, "image")
        saved[index] = save

    stage = graph.custom(
        "CatH3Stage", "03 审查所选首帧：看图后到01选择阶段2，再点Run",
        [("run_id", "STRING"), ("phase", "STRING"), ("context", "STRING"), ('selected_shots', 'STRING')] + [(f"frame_{i:02d}", "STRING") for i in range(1, 11)],
        [("ready", "STRING")], [], 0, 880, (600, 850),
    )
    for slot, name in ((1, "run_id"), (3, "phase"), (4, "context")):
        wire(story, slot, stage, name)
    wire(story, 5, stage, 'selected_shots')
    for index in range(1, 11):
        wire(saved[index], 1, stage, f"frame_{index:02d}")

    h3_model = graph.custom("UNETLoader", "H3 模型（审图阶段不加载）", [], [("MODEL", "MODEL")], [H3_MODEL, "default"], 3890, -650)
    h3_clip = graph.custom("CLIPLoader", "H3 文本编码器", [], [("CLIP", "CLIP")], [H3_CLIP, "minimax", "default"], 3890, -390)
    video_vae = graph.custom("VAELoader", "H3 视频 VAE", [], [("VAE", "VAE")], [H3_VIDEO_VAE], 4280, -390)
    audio_vae = graph.custom("VAELoader", "H3 音频 VAE", [], [("VAE", "VAE")], [H3_AUDIO_VAE], 4280, -170)
    scheduler = graph.custom("BasicScheduler", "20 步 simple", [("model", "MODEL")], [("SIGMAS", "SIGMAS")], ["simple", 20, 1], 4280, -650)
    graph.connect(h3_model, 0, scheduler, 0)
    sampler_kind = graph.custom("KSamplerSelect", "res_multistep", [], [("SAMPLER", "SAMPLER")], ["res_multistep"], 4670, -650)
    clips, previous = [], stage
    for index in range(1, 11):
        y = (index - 1) * 850
        gate = graph.custom("CatH3VideoGate", f"镜头 {index:02d} 审查与顺序关卡",
                            [("start", "IMAGE"), ("ready", "STRING"), ("prior_done", "STRING"), ('clip', 'CLIP'), ('prompt', 'STRING')],
                            [("start", "IMAGE"), ('checked_prompt', 'STRING')], [index], 3890, y)
        wire(saved[index], 0, gate, "start")
        wire(stage, 0, gate, "ready")
        wire(previous, 0, gate, "prior_done")
        wire(h3_clip, 0, gate, 'clip')
        wire(fields[index], 1, gate, 'prompt')
        condition = graph.custom(
            "MiniMaxH3ImageToVideo", f"镜头 {index:02d} 仅首帧生视频（不接尾帧）",
            [("clip", "CLIP"), ("vae", "VAE"), ("first_frame", "IMAGE"), ("last_frame", "IMAGE")],
            [("positive", "CONDITIONING"), ("LATENT", "LATENT")], ["Use connected reviewed motion prompt.", 1344, 768, 175],
            4330, y, (450, 370),
        )
        wire(h3_clip, 0, condition, "clip")
        wire(video_vae, 0, condition, "vae")
        wire(gate, 0, condition, "first_frame")
        graph.widget_link(gate, 1, condition, "prompt", "STRING")
        graph.widget_link(fields[index], 6, condition, 'length', 'INT')
        guider = graph.custom("BasicGuider", f"镜头 {index:02d} 引导", [("model", "MODEL"), ("conditioning", "CONDITIONING")], [("GUIDER", "GUIDER")], [], 4820, y)
        graph.connect(h3_model, 0, guider, 0)
        graph.connect(condition, 0, guider, 1)
        noise = graph.custom("RandomNoise", f"镜头 {index:02d} 视频种子", [], [("NOISE", "NOISE")], [932100 + index * 101, "fixed"], 4820, y + 220)
        graph.widget_link(fields[index], 3, noise, "noise_seed", "INT")
        sample = graph.custom("SamplerCustomAdvanced", f"镜头 {index:02d} 视频采样",
                              [("noise", "NOISE"), ("guider", "GUIDER"), ("sampler", "SAMPLER"), ("sigmas", "SIGMAS"), ("latent_image", "LATENT")],
                              [("output", "LATENT"), ("denoised_output", "LATENT")], [], 5240, y, (400, 270))
        for src, src_slot, dst_slot in ((noise, 0, 0), (guider, 0, 1), (sampler_kind, 0, 2), (scheduler, 0, 3), (condition, 1, 4)):
            graph.connect(src, src_slot, sample, dst_slot)
        decode_video = graph.custom("VAEDecode", f"镜头 {index:02d} 解码视频", [("samples", "LATENT"), ("vae", "VAE")], [("IMAGE", "IMAGE")], [], 5680, y)
        graph.connect(sample, 0, decode_video, 0)
        graph.connect(video_vae, 0, decode_video, 1)
        decode_audio = graph.custom("VAEDecodeAudio", f"镜头 {index:02d} 解码原生声音", [("samples", "LATENT"), ("vae", "VAE")], [("AUDIO", "AUDIO")], [], 5680, y + 230)
        graph.connect(sample, 0, decode_audio, 0)
        graph.connect(audio_vae, 0, decode_audio, 1)
        save = graph.custom("CatH3SaveAV", f"镜头 {index:02d} 仅阶段2保存视频",
                            [("phase", "STRING"), ("run_id", "STRING"), ("ready", "STRING"), ("images", "IMAGE"), ("audio", "AUDIO"),
                             ('selected_shots', 'STRING'), ('video_key', 'STRING'), ('frame_count', 'INT')],
                            [("done", "STRING")], [index], 6120, y, (430, 270))
        wire(story, 3, save, "phase")
        wire(story, 1, save, "run_id")
        wire(stage, 0, save, "ready")
        wire(decode_video, 0, save, "images")
        wire(decode_audio, 0, save, "audio")
        wire(story, 5, save, 'selected_shots')
        wire(fields[index], 7, save, 'video_key')
        wire(fields[index], 6, save, 'frame_count')
        clips.append(save)
        previous = save
    finish = graph.custom("CatH3Finish", "04 阶段2合成十镜带声音 Vlog",
                          [("phase", "STRING"), ("run_id", "STRING"), ("story_json", "STRING"), ("ready", "STRING"), ('context', 'STRING'), ('selected_shots', 'STRING')]
                          + [(f"clip_{i:02d}", "STRING") for i in range(1, 11)]
                          + [(f'{kind}_{i:02d}', 'STRING') for i in range(1, 11) for kind in ('frame_key', 'video_key')],
                          [("final_path", "STRING")], [], 6600, 0, (460, 450))
    for slot, name in ((3, "phase"), (1, "run_id"), (0, "story_json")):
        wire(story, slot, finish, name)
    wire(stage, 0, finish, "ready")
    wire(story, 4, finish, 'context')
    wire(story, 5, finish, 'selected_shots')
    for i, clip in enumerate(clips, 1):
        wire(clip, 0, finish, f"clip_{i:02d}")
        wire(fields[i], 4, finish, f'frame_key_{i:02d}')
        wire(fields[i], 7, finish, f'video_key_{i:02d}')
    return graph.export()


def write_workflows(directory: Path, story_json: str = "") -> list[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "01_one_pass_10x7s_h3_cu128.json"
    path.write_text(json.dumps(build_workflow(story_json), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return [path]
