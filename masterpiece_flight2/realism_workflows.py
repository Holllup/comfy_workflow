"""Flat, inspectable FLUX.2 editing and H3 first/last-frame graphs (schema v3)."""

import json
from pathlib import Path

from .workflow_builder import Graph

FLUX_MODELS = {
    'diffusion_models': 'flux2_dev_fp8mixed.safetensors',
    'text_encoders': 'mistral_3_small_flux2_bf16.safetensors',
    'vae': 'flux2-vae.safetensors',
}


class Builder(Graph):
    def node(self, kind, title, inputs=(), outputs=(), widgets=(), x=0, y=0):
        node = self.custom(kind, title, inputs, outputs, list(widgets), x, y, (350, 200))
        if not kind.startswith('Art'):
            node['properties']['cnr_id'] = 'comfy-core'
        return node

    def prompt(self, project, token, kind, y, variation=0, prior=None):
        node = self.node('ArtV3Prompt', kind + ' · 已确认分镜提示词',
                         [('project_id', 'STRING'), ('project_token', 'STRING')],
                         [('prompt', 'STRING'), ('seed', 'INT')],
                         [kind, 932100 if kind.startswith('flight') or kind == 'morph' else 487201, variation], 700, y)
        self.connect(*project, node, 0); self.connect(*token, node, 1)
        if prior:
            node['inputs'].append({'name': 'prior', 'type': 'STRING', 'link': None})
            self.connect(*prior, node, 2)
        return node

    def preview(self, source, report, y):
        preview = self.node('PreviewImage', '检查关键帧', [('images', 'IMAGE')], x=4150, y=y)
        preview['size'] = [420, 300]
        self.connect(*source, preview, 0)
        text = self.node('PreviewAny', '复制下一阶段确认码', [('source', 'STRING')], widgets=[], x=4620, y=y)
        text['size'] = [440, 250]
        self.connect(*report, text, 0)

    def flux_loaders(self):
        model = self.node('UNETLoader', 'FLUX.2 dev FP8 mixed', outputs=[('MODEL', 'MODEL')],
                          widgets=[FLUX_MODELS['diffusion_models'], 'default'], x=700, y=-620)
        clip = self.node('CLIPLoader', 'FLUX Mistral BF16', outputs=[('CLIP', 'CLIP')],
                         widgets=[FLUX_MODELS['text_encoders'], 'flux2', 'default'], x=1100, y=-620)
        vae = self.node('VAELoader', 'FLUX.2 VAE', outputs=[('VAE', 'VAE')],
                        widgets=[FLUX_MODELS['vae']], x=1500, y=-620)
        for node, directory in ((model, 'diffusion_models'), (clip, 'text_encoders'), (vae, 'vae')):
            filename = FLUX_MODELS[directory]
            node['properties']['models'] = [{'name': filename, 'directory': directory,
                'url': f'https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/{directory}/{filename}'}]
        return model, clip, vae

    def flux_edit(self, loaders, reference, fields, project, token, slot, y):
        model, clip, vae = loaders
        text = self.node('CLIPTextEncode', slot + ' · FLUX 提示词', [('clip', 'CLIP')],
                         [('CONDITIONING', 'CONDITIONING')], [''], 1100, y)
        self.connect(clip, 0, text, 0); self.widget_link(fields, 0, text, 'text', 'STRING')
        guidance = self.node('FluxGuidance', 'FLUX guidance 4', [('conditioning', 'CONDITIONING')],
                             [('CONDITIONING', 'CONDITIONING')], [4], 1500, y)
        self.connect(text, 0, guidance, 0)
        encoded = self.node('VAEEncode', slot + ' · 唯一图像参考', [('pixels', 'IMAGE'), ('vae', 'VAE')],
                            [('LATENT', 'LATENT')], x=1100, y=y + 230)
        self.connect(*reference, encoded, 0); self.connect(vae, 0, encoded, 1)
        ref = self.node('ReferenceLatent', 'FLUX 单参考条件', [('conditioning', 'CONDITIONING'), ('latent', 'LATENT')],
                        [('CONDITIONING', 'CONDITIONING')], x=1500, y=y + 230)
        self.connect(guidance, 0, ref, 0); self.connect(encoded, 0, ref, 1)
        guider = self.node('BasicGuider', 'FLUX 引导', [('model', 'MODEL'), ('conditioning', 'CONDITIONING')],
                           [('GUIDER', 'GUIDER')], x=1900, y=y)
        self.connect(model, 0, guider, 0); self.connect(ref, 0, guider, 1)
        noise = self.node('RandomNoise', '可复现种子', outputs=[('NOISE', 'NOISE')], widgets=[0, 'fixed'], x=1900, y=y + 220)
        self.widget_link(fields, 1, noise, 'noise_seed', 'INT')
        sampler = self.node('KSamplerSelect', 'euler', outputs=[('SAMPLER', 'SAMPLER')], widgets=['euler'], x=2300, y=y + 220)
        schedule = self.node('Flux2Scheduler', 'FLUX 原生 20 步', outputs=[('SIGMAS', 'SIGMAS')],
                             widgets=[20, 1344, 768], x=2300, y=y)
        latent = self.node('EmptyFlux2LatentImage', '1344×768', outputs=[('LATENT', 'LATENT')],
                           widgets=[1344, 768, 1], x=2300, y=y + 440)
        sample = self.node('SamplerCustomAdvanced', slot + ' · FLUX 采样',
                           [('noise', 'NOISE'), ('guider', 'GUIDER'), ('sampler', 'SAMPLER'), ('sigmas', 'SIGMAS'), ('latent_image', 'LATENT')],
                           [('output', 'LATENT'), ('denoised_output', 'LATENT')], x=2750, y=y)
        for node, index in ((noise, 0), (guider, 1), (sampler, 2), (schedule, 3), (latent, 4)):
            self.connect(node, 0, sample, index)
        decode = self.node('VAEDecode', 'FLUX 解码', [('samples', 'LATENT'), ('vae', 'VAE')], [('IMAGE', 'IMAGE')], x=3200, y=y)
        self.connect(sample, 0, decode, 0); self.connect(vae, 0, decode, 1)
        save = self.node('ArtV3SaveImage', slot + ' · 保存待审素材',
                         [('image', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                         [('saved_image', 'IMAGE'), ('review_report', 'STRING')], [slot], 3650, y)
        self.connect(decode, 0, save, 0); self.connect(*project, save, 1); self.connect(*token, save, 2)
        self.preview((save, 0), (save, 1), y)
        return save

    def h3_loaders(self):
        model = self.node('UNETLoader', 'H3 FL2VA FP8 · cu128/cu130', outputs=[('MODEL', 'MODEL')],
                          widgets=['minimax_h3_fl2va_pruned_fp8_scaled.safetensors', 'default'], x=700, y=-650)
        clip = self.node('CLIPLoader', 'H3 编码器（并非图片生成模型）', outputs=[('CLIP', 'CLIP')],
                         widgets=['qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 'minimax', 'default'], x=1100, y=-650)
        vae = self.node('VAELoader', 'H3 FP16 VAE', outputs=[('VAE', 'VAE')],
                        widgets=['minimax_h3_video_vae_fp16.safetensors'], x=1500, y=-650)
        schedule = self.node('BasicScheduler', 'H3 20 步 simple', [('model', 'MODEL')], [('SIGMAS', 'SIGMAS')], [ 'simple', 20, 1], 1900, -650)
        self.connect(model, 0, schedule, 0)
        sampler = self.node('KSamplerSelect', 'res_multistep', outputs=[('SAMPLER', 'SAMPLER')], widgets=['res_multistep'], x=2300, y=-650)
        return model, clip, vae, schedule, sampler

    def video_save(self, source, project, name, y, x=3800):
        prefix = self.node('ArtOutputPrefix', '项目输出路径', [('project_id', 'STRING')], [('prefix', 'STRING')], [name], x, y + 220)
        self.connect(*project, prefix, 0)
        save = self.node('SaveVideo', name + ' · 视频预览', [('video', 'VIDEO')], [('video', 'VIDEO')],
                         ['masterpiece_flight2/v3', 'auto', 'auto'], x, y)
        self.connect(*source, save, 0); self.widget_link(prefix, 0, save, 'filename_prefix', 'STRING')

    def h3_clip(self, loaders, start, end, fields, project, token, name, y):
        model, clip, vae, schedule, sampler = loaders
        condition = self.node('MiniMaxH3ImageToVideo', name + ' · 首尾帧条件',
            [('clip', 'CLIP'), ('vae', 'VAE'), ('first_frame', 'IMAGE'), ('last_frame', 'IMAGE')],
            [('positive', 'CONDITIONING'), ('LATENT', 'LATENT')], ['', 1344, 768, 124], 1100, y)
        for source, slot in (((clip, 0), 0), ((vae, 0), 1), (start, 2), (end, 3)):
            self.connect(*source, condition, slot)
        self.widget_link(fields, 0, condition, 'prompt', 'STRING')
        guider = self.node('BasicGuider', 'H3 引导', [('model', 'MODEL'), ('conditioning', 'CONDITIONING')], [('GUIDER', 'GUIDER')], x=1550, y=y)
        self.connect(model, 0, guider, 0); self.connect(condition, 0, guider, 1)
        noise = self.node('RandomNoise', 'H3 固定种子', outputs=[('NOISE', 'NOISE')], widgets=[0, 'fixed'], x=1550, y=y + 240)
        self.widget_link(fields, 1, noise, 'noise_seed', 'INT')
        sample = self.node('SamplerCustomAdvanced', name + ' · H3 采样',
                           [('noise', 'NOISE'), ('guider', 'GUIDER'), ('sampler', 'SAMPLER'), ('sigmas', 'SIGMAS'), ('latent_image', 'LATENT')],
                           [('output', 'LATENT'), ('denoised_output', 'LATENT')], x=1950, y=y)
        for node, output, slot in ((noise, 0, 0), (guider, 0, 1), (sampler, 0, 2), (schedule, 0, 3), (condition, 1, 4)):
            self.connect(node, output, sample, slot)
        decode = self.node('VAEDecode', 'H3 原始帧', [('samples', 'LATENT'), ('vae', 'VAE')], [('IMAGE', 'IMAGE')], x=2380, y=y)
        self.connect(sample, 0, decode, 0); self.connect(vae, 0, decode, 1)
        cache = self.node('ArtV3SaveClip', name + ' · 无损缓存与两帧校正',
                          [('images', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                          [('corrected_frames', 'IMAGE'), ('last_frame', 'IMAGE'), ('cache_receipt', 'STRING'), ('review_report', 'STRING')],
                          [name, 0], 2780, y)
        self.connect(decode, 0, cache, 0); self.connect(*project, cache, 1); self.connect(*token, cache, 2)
        self.widget_link(fields, 1, cache, 'seed', 'INT')
        video = self.node('CreateVideo', name + ' · 无声预览', [('images', 'IMAGE')], [('VIDEO', 'VIDEO')], [24, 8], 3300, y)
        self.connect(cache, 0, video, 0); self.video_save((video, 0), project, 'v3_' + name, y)
        report = self.node('PreviewAny', '检查后复制确认码', [('source', 'STRING')], x=4280, y=y)
        self.connect(cache, 3, report, 0)
        return cache

    def finish_graph(self, stage, note):
        self.node('MarkdownNote', '使用步骤', widgets=[note], x=0, y=-600)['size'] = [620, 500]
        return self.export('realism-v3-' + stage)


def build_stages():
    result = {}
    g = Builder()
    source = g.node('LoadImage', '上传完整原画', outputs=[('IMAGE', 'IMAGE'), ('MASK', 'MASK')], widgets=['starry_night.jpg', 'image'])
    prepare = g.node('ArtV3Prepare', '首次粘贴 v3 JSON', [('painting', 'IMAGE')],
                     [('source_canvas', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                     ['starry_realism_01', ''], 0, 500)
    g.connect(source, 0, prepare, 0)
    project, token = (prepare, 1), (prepare, 2)
    loaders = g.flux_loaders()
    prompt = g.prompt(project, token, 'extension', 0)
    art = g.flux_edit(loaders, (prepare, 0), prompt, project, token, 'art', 0)
    previous = art
    for i in range(1, 4):
        y = i * 950
        prompt = g.prompt(project, token, 'endpoint', y, i, (previous, 1))
        previous = g.flux_edit(loaders, (art, 0), prompt, project, token, f'r5_candidate_{i}', y)
    result['01_flux_endpoints.json'] = g.finish_graph('endpoints',
        '先上传原画与已确认的 v3 JSON。生成扩展原画与三个写实终点。\n检查原画边缘接缝、写实感与地标位置，选择候选编号并复制它的 approval_code 到第二阶段。')

    g = Builder()
    load = g.node('ArtV3LoadEndpoints', '确认终点候选', outputs=[('R5', 'IMAGE'), ('art', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                  widgets=['starry_realism_01', 1, ''])
    project, token = (load, 2), (load, 3)
    prompt = g.prompt(project, token, 'morph', 0)
    g.h3_clip(g.h3_loaders(), (load, 0), (load, 1), prompt, project, token, 'morph', 0)
    result['02_h3_morph_pilot.json'] = g.finish_graph('morph',
        '填入项目 ID、候选编号和刚检查过的 approval_code。\n生成锁定机位的约五秒 AI 画作化。检查中间帧，满意后复制 morph_approval_code 到第三阶段。')

    g = Builder()
    load = g.node('ArtV3KeyframeStart', '确认渐变试片并读取 R5', outputs=[('R5', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                  widgets=['starry_realism_01', ''])
    project, token = (load, 1), (load, 2)
    loaders = g.flux_loaders(); previous = load
    for row, i in enumerate((4, 3, 2, 1)):
        y = row * 950
        prompt = g.prompt(project, token, f'frame{i}', y)
        previous = g.flux_edit(loaders, (previous, 0), prompt, project, token, f'r{i}', y)
    result['03_flux_flight_keyframes.json'] = g.finish_graph('frames',
        '填入项目 ID 与已检查渐变试片的 morph_approval_code。\n逆向生成 R4→R3→R2→R1。检查五个视角与地形遮挡接点，复制最后显示的 frames_approval_code 到第四阶段。')

    g = Builder()
    load = g.node('ArtV3LoadFrames', '确认五张写实关键帧', outputs=[(f'R{i}', 'IMAGE') for i in range(1, 6)] + [('art', 'IMAGE'), ('project_id', 'STRING'), ('project_token', 'STRING')],
                  widgets=['starry_realism_01', ''])
    project, token = (load, 6), (load, 7)
    loaders = g.h3_loaders(); clips = []
    for i in range(1, 5):
        y = (i - 1) * 850
        prompt = g.prompt(project, token, f'flight{i}', y)
        start = (load, 0) if i == 1 else (clips[-1], 1)
        clips.append(g.h3_clip(loaders, start, (load, i), prompt, project, token, f'flight{i}', y))
    finish = g.node('ArtV3Finish', '复用已确认渐变并流式合成 640 帧',
                    [('project_id', 'STRING')] + [(f'flight{i}', 'STRING') for i in range(1, 5)],
                    [('video', 'VIDEO'), ('final_report', 'STRING')], x=4800, y=0)
    g.connect(*project, finish, 0)
    for i, clip in enumerate(clips, 1): g.connect(clip, 2, finish, i)
    g.video_save((finish, 0), project, 'v3_final', 0, x=5250)
    report = g.node('PreviewAny', '最终路径与帧数', [('source', 'STRING')], x=5700, y=0)
    g.connect(finish, 1, report, 0)
    result['04_h3_full_flight.json'] = g.finish_graph('full',
        '填入项目 ID 和已检查全部关键帧的 frames_approval_code。\n只生成四段写实飞行，复用第二阶段的渐变缓存，再追加一秒扩展原画定格。原画不会进入四段飞行条件。')
    return result


def write_stages(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    for name, graph in build_stages().items():
        (directory / name).write_text(json.dumps(graph, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
