"""
Prompt Optimizer nodes for ComfyUI
Optimizes prompts for various AI models using Ollama
"""

from .prompt_optimizer_node import PromptOptimizer

NODE_CLASS_MAPPINGS = {
    "PromptOptimizer": PromptOptimizer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptOptimizer": "Prompt Optimizer (Ollama)",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']