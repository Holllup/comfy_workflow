"""ComfyUI custom nodes for a six-shot cat vlog."""

from .nodes import (
    CatFinish,
    CatImageGate,
    CatReference,
    CatSaveClip,
    CatSaveFrame,
    CatShotFields,
    CatStoryPlanner,
    CatVideoGate,
)

NODE_CLASS_MAPPINGS = {
    cls.__name__: cls for cls in (
        CatStoryPlanner, CatShotFields, CatReference, CatImageGate,
        CatSaveFrame, CatVideoGate, CatSaveClip, CatFinish,
    )
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "CatStoryPlanner": "🐱 六镜随机剧情",
    "CatShotFields": "🐱 分镜提示词",
    "CatReference": "🐱 固定主角定妆照",
    "CatImageGate": "🐱 首帧顺序门",
    "CatSaveFrame": "🐱 保存分镜首帧",
    "CatVideoGate": "🐱 视频顺序门",
    "CatSaveClip": "🐱 保存五秒片段",
    "CatFinish": "🐱 合成三十秒成片",
}
