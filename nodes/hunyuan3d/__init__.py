"""
Hunyuan3D 2.1 ComfyUI Nodes
Two-stage pipeline: Shape generation and texture painting
"""

from .hunyuan3d_node import Hunyuan3D21Node
from .hunyuan3d_paint_node import Hunyuan3DPaintNode

NODE_CLASS_MAPPINGS = {
    "Hunyuan3D21Node": Hunyuan3D21Node,
    "Hunyuan3DPaintNode": Hunyuan3DPaintNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3D21Node": "🎮 Hunyuan3D 2.1 Shape",
    "Hunyuan3DPaintNode": "🎨 Hunyuan3D Paint Texture",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']