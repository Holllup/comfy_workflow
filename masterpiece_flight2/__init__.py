"""Reusable painting-flight ComfyUI nodes and workflow tools."""

try:
    from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    from .realism_nodes import NODE_CLASS_MAPPINGS as V3_NODES, NODE_DISPLAY_NAME_MAPPINGS as V3_NAMES
    NODE_CLASS_MAPPINGS = {**NODE_CLASS_MAPPINGS, **V3_NODES}
    NODE_DISPLAY_NAME_MAPPINGS = {**NODE_DISPLAY_NAME_MAPPINGS, **V3_NAMES}
except ModuleNotFoundError as exc:
    if exc.name not in {"torch", "folder_paths", f"{__name__}.nodes"}:
        raise
    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
