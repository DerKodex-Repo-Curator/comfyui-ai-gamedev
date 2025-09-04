"""
PromptPreview node for ComfyUI
Based on ComfyUI's PreviewAny node pattern
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class PromptPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"text": ("STRING", {"forceInput": True})},
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "preview"
    OUTPUT_NODE = True
    CATEGORY = "gamedev/prompt"

    def preview(self, text):
        """Preview the text and pass it through"""
        logger.info(f"=" * 60)
        logger.info(f"📝 PromptPreview received input")
        logger.info(f"   Input type: {type(text)}")
        logger.info(f"   Input length: {len(text) if text else 0} chars")
        
        if text:
            # Log first 500 chars of the text
            preview_text = text[:500] + "..." if len(text) > 500 else text
            logger.info(f"   Input text: {preview_text}")
            
            # Also log some stats
            lines = text.count('\n') + 1
            words = len(text.split())
            logger.info(f"   Stats: {lines} lines, {words} words, {len(text)} chars")
        else:
            logger.warning(f"   ⚠️ Received empty or None text input!")
            
        logger.info(f"=" * 60)
        
        # Exactly like PreviewAny but for strings
        result = {"ui": {"text": (text,)}, "result": (text,)}
        
        logger.debug(f"Returning result: {result}")
        return result


NODE_CLASS_MAPPINGS = {
    "PromptPreview": PromptPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptPreview": "Prompt Preview",
}