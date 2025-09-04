"""
ComfyUI AI GameDev custom nodes
"""

# Import all node mappings
from .prompt_optimizer import NODE_CLASS_MAPPINGS as PROMPT_MAPPINGS
from .prompt_optimizer import NODE_DISPLAY_NAME_MAPPINGS as PROMPT_DISPLAY_MAPPINGS

# Combine all mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Add prompt optimizer nodes
NODE_CLASS_MAPPINGS.update(PROMPT_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(PROMPT_DISPLAY_MAPPINGS)

# Export for ComfyUI
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']