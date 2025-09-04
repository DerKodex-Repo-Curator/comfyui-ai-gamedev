"""
Hunyuan3D 2.1 ComfyUI Nodes
Unified node for shape generation and texture painting
"""

from .hunyuan3d_unified_node import Hunyuan3D21UnifiedNode

NODE_CLASS_MAPPINGS = {
    "Hunyuan3D21": Hunyuan3D21UnifiedNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3D21": "🎮 Hunyuan3D 2.1",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']