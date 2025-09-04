"""
Simple text display widget for ComfyUI that actually shows text
"""

class SimpleTextDisplay:
    """
    A simple multiline text display that works with ComfyUI's built-in widgets
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text_input": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "text": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "Text will appear here..."
                })
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "show_text"
    CATEGORY = "gamedev/prompt"
    OUTPUT_NODE = True
    
    def show_text(self, text_input, text=""):
        """Simply pass through the text and update the widget"""
        # The text widget will be updated by ComfyUI when we return the value
        return {"ui": {"text": text_input}, "result": (text_input,)}
    
    @classmethod
    def IS_CHANGED(cls, text_input, **kwargs):
        # Always update when input changes
        return text_input


# Export for registration
NODE_CLASS_MAPPINGS = {
    "SimpleTextDisplay": SimpleTextDisplay
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "SimpleTextDisplay": "Simple Text Display"
}