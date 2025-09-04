"""
Prompt Optimizer nodes for ComfyUI
Optimizes prompts for various AI models using Ollama
"""

from .prompt_optimizer_node import PromptOptimizer
from .prompt_display_node import PromptDisplay, PromptDisplayLarge

NODE_CLASS_MAPPINGS = {
    "PromptOptimizer": PromptOptimizer,
    "PromptDisplay": PromptDisplay,
    "PromptDisplayLarge": PromptDisplayLarge
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptOptimizer": "Prompt Optimizer (Ollama)",
    "PromptDisplay": "Prompt Display",
    "PromptDisplayLarge": "Prompt Display (Large)"
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']