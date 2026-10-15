"""Independent MiniMax H3 cat vlog custom nodes for ComfyUI."""

from .nodes import (
    CatH3References, CatH3Story, CatH3SelectReferences, CatH3JoyEncode, CatH3ShotFields,
    CatH3SaveFrame, CatH3Stage, CatH3VideoGate, CatH3SaveAV, CatH3Finish,
)


NODE_CLASS_MAPPINGS = {
    cls.__name__: cls for cls in (
        CatH3References, CatH3Story, CatH3SelectReferences, CatH3JoyEncode, CatH3ShotFields,
        CatH3SaveFrame, CatH3Stage, CatH3VideoGate, CatH3SaveAV, CatH3Finish,
    )
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CatH3References": "小猫十镜 · 固定角色照片与预览",
    "CatH3Story": "小猫十镜 · 导入分镜与选择阶段",
    "CatH3SelectReferences": "小猫十镜 · 选择本镜角色视角",
    "CatH3JoyEncode": "小猫十镜 · 按用途编码实际参考图",
    "CatH3ShotFields": "小猫十镜 · 首帧、运动与音频提示词",
    "CatH3SaveFrame": "小猫十镜 · 生成／读取已审首帧",
    "CatH3Stage": "小猫十镜 · 十张首帧审查关卡",
    "CatH3VideoGate": "小猫十镜 · 顺序运行视频",
    "CatH3SaveAV": "小猫十镜 · 保存同步声画 MP4",
    "CatH3Finish": "小猫十镜 · 合成完整 Vlog",
}
