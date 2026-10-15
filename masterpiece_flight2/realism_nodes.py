"""Small native-compatible nodes for the four-stage FLUX/H3 workflow."""

import json
import numpy as np

from . import core, realism
from .nodes import _root, _numpy_image, _tensor_image


def _store(project_id):
    return realism.ProjectStore(_root(), project_id)


def _release_models():
    try:
        import comfy.model_management as management
    except ModuleNotFoundError:
        return
    management.unload_all_models()
    management.soft_empty_cache()


def _batch(array):
    value = np.asarray(array, dtype=np.float32) / 255.0
    try:
        import torch
    except ModuleNotFoundError:
        return value
    return torch.from_numpy(value.copy())


class ProjectNode:
    CATEGORY = 'masterpiece_flight2/FLUX H3 v3'
    FUNCTION = 'run'

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Approval/file changes happen between queues, outside Comfy's graph cache.
        return float('nan')


class ArtV3Prepare(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'painting': ('IMAGE',),
                'project_id': ('STRING', {'default': 'starry_realism_01'}),
                'story_json': ('STRING', {'default': '', 'multiline': True})}}

    RETURN_TYPES = ('IMAGE', 'STRING', 'STRING')
    RETURN_NAMES = ('source_canvas', 'project_id', 'project_token')

    def run(self, painting, project_id, story_json):
        store = _store(project_id)
        token = store.initialize(story_json, _numpy_image(painting))
        _release_models()
        return _tensor_image(store.source_canvas()), project_id, token


class ArtV3Prompt(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'project_id': ('STRING', {'forceInput': True}),
                'project_token': ('STRING', {'forceInput': True}),
                'kind': (['extension', 'endpoint', 'frame4', 'frame3', 'frame2', 'frame1',
                          'morph', 'flight1', 'flight2', 'flight3', 'flight4'],),
                'seed_base': ('INT', {'default': 487201, 'min': 0, 'max': 2**53 - 1000}),
                'variation': ('INT', {'default': 0, 'min': 0, 'max': 100})},
                'optional': {'prior': ('STRING', {'forceInput': True})}}

    RETURN_TYPES = ('STRING', 'INT')
    RETURN_NAMES = ('prompt', 'seed')

    def run(self, project_id, project_token, kind, seed_base, variation, prior=None):
        store = _store(project_id)
        if store.state()['signature'] != project_token:
            raise ValueError('Project token is stale')
        plan = store.story()
        scene = 'SCENE LANDMARKS: ' + '; '.join(plan['visual_anchors'])
        realism_rule = ('Cinematic photorealism with physically solid architecture, terrain and vegetation. '
                        'Dreamlike lighting is allowed. No painted texture, picture frame, floating picture, '
                        'flat backdrop, visible drone, text or modern objects. ')
        if kind == 'extension':
            box = store.state()['original_box']
            text = (f'Extend the scene into the surrounding canvas. The intact source painting occupies '
                    f'x,y,width,height={box}. Keep its position and scale; fill outside it seamlessly '
                    'in the same artistic medium. Do not add a frame or border.\n' + plan['artwork_extension']['prompt_en'])
            offset = 0
        elif kind == 'morph':
            text = ('The first frame is a photoreal scene; the last frame is the same composition as an artwork. '
                    'The camera is locked and all landmarks remain aligned. Transform materials into pigment '
                    'and brushstrokes progressively across the five seconds, including both extended sides. '
                    'Do not reveal a separate painting panel or dissolve between two transparent pictures.\n' +
                    plan['morph']['material_progression_en'] + '\n' + plan['morph']['motion_prompt_en'])
            offset = 500
        elif kind.startswith('flight'):
            index = int(kind[-1])
            text = realism_rule + scene + '\n' + core.compose_motion_prompt(plan['shots'][index - 1])
            if index == 4:
                text += '\nFinish the flight at R5 and smoothly stop. Stay photoreal until the final frame.'
            offset = 300 + index
        else:
            index = 5 if kind == 'endpoint' else int(kind[-1])
            frame = plan['keyframes'][index - 1]
            role = ('The reference is the extended artwork. Reconstruct it as a photograph of a real place, '
                    'keeping the same landmark positions, silhouette sizes and camera framing.' if index == 5
                    else f'The only reference is photoreal keyframe R{index + 1}. Move to the earlier camera '
                    'position below, reconstructing newly visible surfaces in one continuous environment.')
            fields = [('CAMERA POSITION', frame['camera_position']), ('CAMERA DIRECTION', frame['camera_direction']),
                      ('REVERSE MOVE', frame['camera_path_from_next_frame']),
                      ('OCCLUDER', frame['transition_object']), ('SCREEN COVERAGE', frame['transition_object_screen_position']),
                      ('SHARED LANDMARKS', '; '.join(frame['shared_landmarks'])),
                      ('INTERFACE ENTRY STATE', frame['entry_state']), ('INTERFACE EXIT STATE', frame['exit_state']),
                      ('END FRAME CONSTRAINTS', '; '.join(frame['end_frame_constraints'])),
                      ('PRESERVE', '; '.join(frame['must_preserve'])),
                      ('AVOID', '; '.join(frame['must_not_generate'])), ('VISUAL BRIEF', frame['image_prompt_en'])]
            text = realism_rule + role + '\n' + scene + '\n' + '\n'.join(f'{a}: {b}' for a, b in fields)
            offset = 100 if index == 5 else 200 + index
        return text, seed_base + offset + variation


class ArtV3SaveImage(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'image': ('IMAGE',), 'project_id': ('STRING', {'forceInput': True}),
                'project_token': ('STRING', {'forceInput': True}),
                'slot': (['art', 'r5_candidate_1', 'r5_candidate_2', 'r5_candidate_3', 'r4', 'r3', 'r2', 'r1'],)}}

    RETURN_TYPES = ('IMAGE', 'STRING')
    RETURN_NAMES = ('saved_image', 'review_report')

    def run(self, image, project_id, project_token, slot):
        store = _store(project_id)
        pixels = _numpy_image(image)
        if slot == 'art': pixels = store.restore_original(pixels)
        record = store.save_draft(slot, pixels, project_token)
        report = f'{project_id}\n{record["path"]}'
        if slot.startswith('r5_candidate_'):
            candidate = int(slot[-1])
            report += f'\ncandidate={candidate}\napproval_code={store.review_code("endpoints", candidate)}'
        if slot == 'r1':
            report += f'\nframes_approval_code={store.review_code("frames")}'
        return _tensor_image(core._rgb_uint8(pixels)), report


class ArtV3LoadEndpoints(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'project_id': ('STRING', {'default': 'starry_realism_01'}),
                'candidate': ('INT', {'default': 1, 'min': 1, 'max': 3}),
                'approval_code': ('STRING', {'default': ''})}}

    RETURN_TYPES = ('IMAGE', 'IMAGE', 'STRING', 'STRING')
    RETURN_NAMES = ('realistic_R5', 'extended_artwork', 'project_id', 'project_token')

    def run(self, project_id, candidate, approval_code):
        store = _store(project_id)
        if approval_code:
            if approval_code.strip() != store.review_code('endpoints', candidate):
                raise ValueError('approval_code does not match the currently displayed endpoint candidate')
            store.approve_endpoints(candidate)
        _release_models()
        return (_tensor_image(store.load_approved('r5')), _tensor_image(store.load_approved('art')),
                project_id, store.state()['signature'])


class ArtV3KeyframeStart(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'project_id': ('STRING', {'default': 'starry_realism_01'}),
                'morph_approval_code': ('STRING', {'default': ''})}}

    RETURN_TYPES = ('IMAGE', 'STRING', 'STRING')
    RETURN_NAMES = ('realistic_R5', 'project_id', 'project_token')

    def run(self, project_id, morph_approval_code):
        store = _store(project_id)
        if morph_approval_code:
            if morph_approval_code.strip() != store.review_code('morph'):
                raise ValueError('morph_approval_code is stale; review the current morph pilot')
            store.approve_morph()
        store.load_morph()
        _release_models()
        return _tensor_image(store.load_approved('r5')), project_id, store.state()['signature']


class ArtV3LoadFrames(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'project_id': ('STRING', {'default': 'starry_realism_01'}),
                'frames_approval_code': ('STRING', {'default': ''})}}

    RETURN_TYPES = ('IMAGE',) * 6 + ('STRING', 'STRING')
    RETURN_NAMES = ('R1', 'R2', 'R3', 'R4', 'R5', 'extended_artwork', 'project_id', 'project_token')

    def run(self, project_id, frames_approval_code):
        store = _store(project_id)
        if frames_approval_code:
            if frames_approval_code.strip() != store.review_code('frames'):
                raise ValueError('frames_approval_code is stale; review all five current frames')
            store.approve_frames()
        store.load_morph()
        _release_models()
        return tuple(_tensor_image(store.load_approved(f'r{i}')) for i in range(1, 6)) + (
            _tensor_image(store.load_approved('art')), project_id, store.state()['signature'])


class ArtV3SaveClip(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'images': ('IMAGE',), 'project_id': ('STRING', {'forceInput': True}),
                'project_token': ('STRING', {'forceInput': True}),
                'clip_name': (['morph', 'flight1', 'flight2', 'flight3', 'flight4'],),
                'seed': ('INT', {'default': 932600, 'min': 0, 'max': 2**53 - 1})}}

    RETURN_TYPES = ('IMAGE', 'IMAGE', 'STRING', 'STRING')
    RETURN_NAMES = ('corrected_frames', 'last_frame', 'cache_receipt', 'review_report')

    def run(self, images, project_id, project_token, clip_name, seed):
        store = _store(project_id)
        data = images.detach().cpu().numpy() if hasattr(images, 'detach') else np.asarray(images)
        corrected = store.save_clip(clip_name, data, project_token, {'seed': seed})
        record = store.state()['clips'][clip_name]
        receipt = json.dumps({'clip': clip_name, 'sha256': record['sha256'], 'project_token': project_token})
        report = f'{project_id}: {clip_name}\nRaw 0/25/50/75/100% frames are in diagnostics/.'
        if clip_name == 'morph': report += '\nmorph_approval_code=' + store.review_code('morph')
        return _batch(corrected), _tensor_image(corrected[-1]), receipt, report


class ArtV3Finish(ProjectNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {'required': {'project_id': ('STRING', {'forceInput': True}),
                **{f'flight{i}': ('STRING', {'forceInput': True}) for i in range(1, 5)}}}

    RETURN_TYPES = ('VIDEO', 'STRING')
    RETURN_NAMES = ('video', 'final_report')

    def run(self, project_id, flight1, flight2, flight3, flight4):
        store = _store(project_id)
        state = store.state()
        for index, raw in enumerate((flight1, flight2, flight3, flight4), 1):
            receipt = json.loads(raw)
            clip = store._clip(state, f'flight{index}')
            if (receipt.get('clip') != f'flight{index}' or receipt.get('sha256') != clip['sha256']
                    or receipt.get('project_token') != state['signature']):
                raise ValueError('Flight receipt is stale; rerun the affected shot')
        clips = [store.load_clip(f'flight{i}') for i in range(1, 5)] + [store.load_morph()]
        ending = store.load_approved('art')
        output = store.path / 'final_720p.mp4'
        count = realism.encode_frames(realism.iter_joined_frames(clips, ending), output)
        realism._write(store.path / 'final_native.png', core._png_bytes(ending))
        from comfy_api.latest import InputImpl
        return InputImpl.VideoFromFile(str(output)), f'{output}\n{count} frames / 24fps = {count / 24:.3f}s'


NODE_CLASS_MAPPINGS = {cls.__name__: cls for cls in (
    ArtV3Prepare, ArtV3Prompt, ArtV3SaveImage, ArtV3LoadEndpoints,
    ArtV3KeyframeStart, ArtV3LoadFrames, ArtV3SaveClip, ArtV3Finish)}
NODE_DISPLAY_NAME_MAPPINGS = {name: name.replace('ArtV3', '名画写实 · ') for name in NODE_CLASS_MAPPINGS}
