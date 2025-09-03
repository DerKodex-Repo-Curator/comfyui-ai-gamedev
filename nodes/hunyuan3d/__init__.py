"""
Hunyuan3D 2.1 ComfyUI Node
Single node for complete image-to-3D generation with texture painting
"""

from .hunyuan3d_node import Hunyuan3D21Node

NODE_CLASS_MAPPINGS = {
    "Hunyuan3D21Node": Hunyuan3D21Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3D21Node": "Hunyuan3D 2.1 (Image to Textured 3D)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']