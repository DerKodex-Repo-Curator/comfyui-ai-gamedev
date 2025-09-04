"""
PromptPreview node for ComfyUI
Exact copy of PreviewAny from ComfyUI
"""

import json

class PromptPreview():
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"source": ("STRING", {})},
        }

    RETURN_TYPES = ()
    FUNCTION = "main"
    OUTPUT_NODE = True

    CATEGORY = "gamedev/prompt"

    def main(self, source=None):
        value = 'None'
        if isinstance(source, str):
            value = source
        elif isinstance(source, (int, float, bool)):
            value = str(source)
        elif source is not None:
            try:
                value = json.dumps(source)
            except Exception:
                try:
                    value = str(source)
                except Exception:
                    value = 'source exists, but could not be serialized.'

        return {"ui": {"text": (value,)}}

NODE_CLASS_MAPPINGS = {
    "PromptPreview": PromptPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPreview": "Prompt Preview",
}