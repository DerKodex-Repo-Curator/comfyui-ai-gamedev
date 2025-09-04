"""
Prompt Optimizer nodes for ComfyUI
Optimizes prompts for various AI models using Ollama
"""

from .prompt_optimizer_node import PromptOptimizer
from .prompt_preview_node import PromptPreview

NODE_CLASS_MAPPINGS = {
    "PromptOptimizer": PromptOptimizer,
    "PromptPreview": PromptPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptOptimizer": "Prompt Optimizer (Ollama)",
    "PromptPreview": "Prompt Preview",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']