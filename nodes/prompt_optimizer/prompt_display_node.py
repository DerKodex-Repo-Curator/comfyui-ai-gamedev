"""
PromptDisplay node for ComfyUI
A dedicated multiline text display node for viewing prompt outputs
"""

from typing import Tuple, Any, Dict


class PromptDisplay:
    """
    Display prompts in a multiline text widget with proper formatting
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the node"""
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            },
            "optional": {
                "title": ("STRING", {
                    "default": "Prompt",
                    "multiline": False
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "display_text"
    CATEGORY = "gamedev/prompt"
    OUTPUT_NODE = True  # This marks it as an output node that displays in UI
    
    def display_text(self, text: str, title: str = "Prompt") -> Tuple[str]:
        """
        Display the text and pass it through
        
        Args:
            text: The text to display
            title: Optional title for the display
            
        Returns:
            Tuple containing the input text (pass-through)
        """
        # The actual display happens in the UI via the widget
        # We just pass through the text here
        return (text,)
    
    @classmethod
    def IS_CHANGED(cls, text: str, title: str = "Prompt") -> str:
        """
        Indicate when the node output has changed
        This ensures the UI updates when text changes
        """
        # Return the text itself as the change indicator
        # This ensures UI updates whenever text changes
        return text


class PromptDisplayLarge:
    """
    Display prompts in a larger multiline text widget
    Perfect for longer prompts or detailed outputs
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the node"""
        return {
            "required": {
                "text": ("STRING", {"forceInput": True}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "display_text"
    CATEGORY = "gamedev/prompt"
    OUTPUT_NODE = True
    
    def display_text(self, text: str) -> Dict:
        """
        Display the text in the UI and pass it through
        
        Args:
            text: The input text to display
            
        Returns:
            Dict with UI update and result
        """
        # Count lines and words for info
        lines = text.count('\n') + 1
        words = len(text.split())
        chars = len(text)
        
        # Log the text being displayed
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"PromptDisplayLarge showing text: {text[:100]}..." if len(text) > 100 else f"PromptDisplayLarge showing text: {text}")
        
        # Return with UI data for display
        return {
            "ui": {
                "text": [text],
                "info": f"{lines} lines, {words} words, {chars} chars"
            }, 
            "result": (text,)
        }
    
    @classmethod
    def IS_CHANGED(cls, text: str, **kwargs) -> str:
        """Indicate when the node output has changed"""
        return text


# Node registration
NODE_CLASS_MAPPINGS = {
    "PromptDisplay": PromptDisplay,
    "PromptDisplayLarge": PromptDisplayLarge
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptDisplay": "Prompt Display",
    "PromptDisplayLarge": "Prompt Display (Large)"
}