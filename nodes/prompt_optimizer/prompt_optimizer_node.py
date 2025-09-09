"""
PromptOptimizer node for ComfyUI
Optimizes prompts for various AI models using Ollama
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
from PIL import Image
import torch
import io
import tempfile

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    import ollama
except ImportError:
    ollama = None
    print("⚠️ Ollama not installed. Please install with: pip install ollama")


class PromptOptimizer:
    """
    Optimizes prompts for various AI models using Ollama
    """
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), "model_configs.json")
        self.model_configs = self._load_model_configs()
        self.temp_images = []  # Track temporary image files for cleanup
        logger.info(f"🚀 PromptOptimizer initialized with {len(self.model_configs)} models")
    
    def _load_model_configs(self) -> Dict:
        """Load model configurations from JSON file"""
        try:
            logger.debug(f"Loading model configs from: {self.config_file}")
            with open(self.config_file, 'r') as f:
                data = json.load(f)
                models = data.get("models", {})
                logger.info(f"✅ Loaded {len(models)} model configurations")
                return models
        except Exception as e:
            logger.error(f"❌ Failed to load model configs: {e}")
            return {}
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input types for the node"""
        # Load model names from config
        config_file = os.path.join(os.path.dirname(__file__), "model_configs.json")
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
                model_names = list(data.get("models", {}).keys())
        except:
            model_names = ["flux_dev"]  # Fallback
        
        return {
            "required": {
                "target_model": (model_names, {"default": model_names[0] if model_names else "flux_dev"}),
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter your prompt to optimize..."
                }),
            },
            "optional": {
                "image": ("IMAGE",),
                "ollama_host": ("STRING", {
                    "default": "localhost:11434",
                    "placeholder": "Ollama server host"
                }),
                "ollama_model": ("STRING", {
                    "default": "qwen2.5vl:7b",
                    "placeholder": "Ollama model to use"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider",
                    "placeholder": "Temperature (0.0-2.0)"
                }),
                "seed": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "placeholder": "Seed (-1 for random)"
                }),
                "max_tokens_override": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 4096,
                    "placeholder": "Max tokens (0 for model default)"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive_prompt", "negative_prompt", "original_prompt")
    FUNCTION = "optimize_prompt"
    CATEGORY = "gamedev/prompt"
    
    def _check_output_connected(self, output_name: str) -> bool:
        """
        Check if a specific output is connected in the workflow
        This is a simplified check - in production, you'd query ComfyUI's graph
        """
        # For now, we'll assume outputs are connected
        # In a real implementation, this would check the ComfyUI graph
        return True
    
    def _save_image_for_ollama(self, image_tensor) -> str:
        """
        Save image tensor to temporary file for Ollama to read
        
        Args:
            image_tensor: Image tensor from ComfyUI - could be torch.Tensor or numpy array
                         Format: (B, H, W, C) or (H, W, C)
        
        Returns:
            Path to temporary image file
        """
        try:
            logger.debug(f"Saving image for Ollama - Type: {type(image_tensor)}, Shape: {image_tensor.shape}")
            
            # Convert torch tensor to numpy if needed
            if torch.is_tensor(image_tensor):
                logger.debug("Converting torch tensor to numpy")
                image_array = image_tensor.cpu().numpy()
            else:
                image_array = image_tensor
            
            logger.debug(f"Array shape: {image_array.shape}, dtype: {image_array.dtype}")
            
            # Handle batch dimension - use first image if batch
            if len(image_array.shape) == 4:
                logger.debug(f"Extracting first image from batch of {image_array.shape[0]}")
                image_array = image_array[0]
            
            # Ensure we have HWC format (Height, Width, Channels)
            if len(image_array.shape) == 3:
                # Check if it's CHW format (Channels, Height, Width)
                if image_array.shape[0] in [1, 3, 4]:
                    logger.debug(f"Converting from CHW to HWC format")
                    image_array = np.transpose(image_array, (1, 2, 0))
            
            logger.debug(f"Final array shape: {image_array.shape}, dtype: {image_array.dtype}")
            
            # Convert from 0-1 float to 0-255 uint8 if needed
            if image_array.dtype != np.uint8:
                if image_array.max() <= 1.0:
                    logger.debug("Converting from 0-1 float to 0-255 uint8")
                    image_array = (image_array * 255).astype(np.uint8)
                else:
                    logger.debug("Converting to uint8")
                    image_array = image_array.astype(np.uint8)
            
            # Handle single channel images
            if image_array.shape[-1] == 1:
                logger.debug("Converting single channel to RGB")
                image_array = np.repeat(image_array, 3, axis=-1)
            
            # Create PIL image
            logger.debug(f"Creating PIL image from array shape: {image_array.shape}")
            pil_image = Image.fromarray(image_array)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix='.png', 
                delete=False,
                prefix='prompt_opt_'
            )
            pil_image.save(temp_file.name, 'PNG')
            self.temp_images.append(temp_file.name)  # Track for cleanup
            
            logger.info(f"✅ Saved image to: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            logger.error(f"❌ Failed to save image for Ollama: {e}", exc_info=True)
            return None
    
    def _cleanup_temp_images(self):
        """Clean up temporary image files"""
        logger.debug(f"Cleaning up {len(self.temp_images)} temporary images")
        for img_path in self.temp_images:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
                    logger.debug(f"Deleted temp image: {img_path}")
            except Exception as e:
                logger.warning(f"Failed to delete temp image {img_path}: {e}")
        self.temp_images = []
    
    def _clean_repetitions(self, text: str) -> str:
        """
        Clean up repetitive patterns in text
        
        Args:
            text: Text to clean
            
        Returns:
            Cleaned text with repetitions removed
        """
        if not text:
            return text
            
        # Split into items (comma or newline separated)
        items = []
        for part in text.replace('\n', ',').split(','):
            part = part.strip()
            if part:
                items.append(part)
        
        # Detect consecutive repetitions
        cleaned_items = []
        prev_item = None
        repeat_count = 0
        
        for item in items:
            if item == prev_item:
                repeat_count += 1
                # Skip if we've seen this item more than once consecutively
                if repeat_count > 1:
                    logger.debug(f"Skipping repetition: '{item}' (seen {repeat_count} times)")
                    continue
            else:
                repeat_count = 0
            
            cleaned_items.append(item)
            prev_item = item
        
        # Also check for pattern repetitions (e.g., "A, B" repeated as "A, B, A, B")
        if len(cleaned_items) > 4:
            # Check for 2-item patterns
            pattern_found = True
            while pattern_found and len(cleaned_items) > 4:
                pattern_found = False
                for pattern_len in [2, 3, 4]:
                    if len(cleaned_items) < pattern_len * 2:
                        continue
                    
                    for i in range(len(cleaned_items) - pattern_len * 2 + 1):
                        pattern = cleaned_items[i:i+pattern_len]
                        next_pattern = cleaned_items[i+pattern_len:i+pattern_len*2]
                        
                        if pattern == next_pattern:
                            # Remove the repeated pattern
                            logger.debug(f"Removing pattern repetition: {pattern}")
                            del cleaned_items[i+pattern_len:i+pattern_len*2]
                            pattern_found = True
                            break
                    
                    if pattern_found:
                        break
        
        # Rejoin with commas
        result = ', '.join(cleaned_items)
        
        # Log if we removed repetitions
        if len(items) != len(cleaned_items):
            logger.info(f"Removed {len(items) - len(cleaned_items)} repetitions from response")
        
        return result
    
    def _optimize_with_ollama(
        self, 
        messages: List[Dict],
        user_prompt: str,
        image_path: Optional[str],
        ollama_host: str,
        ollama_model: str,
        temperature: float = 0.7,
        seed: int = -1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Run optimization using Ollama
        
        Args:
            messages: Chat history for the model
            user_prompt: User's input prompt
            image_path: Optional path to image file
            ollama_host: Ollama server host
            ollama_model: Ollama model to use
            temperature: Temperature for response generation (0.0-2.0)
            seed: Random seed (-1 for random)
            max_tokens: Maximum tokens to generate (uses model default if None)
        
        Returns:
            Optimized prompt string
        """
        if not ollama:
            logger.warning("Ollama not installed, returning original prompt")
            return user_prompt  # Return original if Ollama not installed
        
        try:
            logger.info(f"🎯 Optimizing with Ollama - Host: {ollama_host}, Model: {ollama_model}")
            logger.info(f"Full user prompt: {user_prompt}")
            logger.debug(f"Image provided: {bool(image_path)}")
            
            # Set up client with custom host if provided
            client = ollama.Client(host=f"http://{ollama_host}")
            logger.debug(f"Created Ollama client for http://{ollama_host}")
            
            # Build final messages list
            final_messages = messages.copy()
            logger.debug(f"Starting with {len(messages)} messages in history")
            
            # Log the system prompt to verify correct model config
            if messages and messages[0].get("role") == "system":
                system_content = messages[0].get("content", "")
                logger.info(f"Full system prompt: {system_content}")
            
            # Add user message with optional image
            user_message = {
                "role": "user",
                "content": user_prompt
            }
            
            if image_path and os.path.exists(image_path):
                user_message["images"] = [image_path]
                logger.info(f"📸 Including image: {image_path}")
            elif image_path:
                logger.warning(f"Image path provided but file not found: {image_path}")
            
            final_messages.append(user_message)
            logger.debug(f"Total messages to send: {len(final_messages)}")
            
            # Prepare options with repetition control
            options = {
                "temperature": temperature,
                "use_mlock": False,  # Disable memory locking  
                "num_ctx": 2048,  # Set context window
                "repeat_penalty": 1.2,  # Penalize repetitions
                "repeat_last_n": 64,  # Look back this many tokens for repetitions
                "stop": ["\n\n", ".", "!", "?", "\n---", "\nUser:", "\nAssistant:"]  # Stop sequences
            }
            
            # Add seed if not using random (-1)
            if seed != -1:
                options["seed"] = seed
                logger.debug(f"Using fixed seed: {seed}")
            else:
                logger.debug("Using random seed")
            
            # Add max_tokens if specified
            if max_tokens is not None:
                options["num_predict"] = max_tokens
                logger.debug(f"Using max_tokens: {max_tokens}")
            
            logger.info(f"📡 Ollama request parameters:")
            logger.info(f"   Ollama Model: {ollama_model}")
            logger.info(f"   Temperature: {temperature}")
            logger.info(f"   Seed: {seed if seed != -1 else 'random'}")
            logger.info(f"   Max tokens: {max_tokens if max_tokens else 'model default'}")
            logger.info(f"   Host: {ollama_host}")
            logger.info(f"   Image included: {bool(image_path and os.path.exists(image_path))}")
            logger.debug(f"   Full options dict: {options}")
            
            # Make request to Ollama
            logger.info(f"📡 Sending request to Ollama...")
            import time
            start_time = time.time()
            response = client.chat(
                model=ollama_model,
                messages=final_messages,
                options=options
            )
            elapsed_time = time.time() - start_time
            
            # Extract and clean response
            optimized = response.get("message", {}).get("content", "").strip()
            
            # Log token usage and performance
            prompt_eval_count = response.get("prompt_eval_count", 0)
            eval_count = response.get("eval_count", 0)
            total_tokens = prompt_eval_count + eval_count
            
            # Calculate tokens per second if available
            prompt_eval_duration = response.get("prompt_eval_duration", 0) / 1e9  # Convert nanoseconds to seconds
            eval_duration = response.get("eval_duration", 0) / 1e9
            
            tokens_per_sec = ""
            if eval_duration > 0:
                tps = eval_count / eval_duration
                tokens_per_sec = f", Speed: {tps:.1f} tokens/sec"
            
            logger.info(f"📊 Token usage - Input: {prompt_eval_count}, Output: {eval_count}, Total: {total_tokens}{tokens_per_sec}")
            logger.info(f"⏱️ Response time: {elapsed_time:.2f}s (prompt eval: {prompt_eval_duration:.2f}s, generation: {eval_duration:.2f}s)")
            
            # Warn if approaching context limit
            if total_tokens > 1800:  # 90% of 2048
                logger.warning(f"⚠️ High token usage ({total_tokens}/2048) - approaching context limit")
            
            logger.info(f"Received response length: {len(optimized)} chars")
            logger.info(f"Full Ollama response: {optimized}")
            
            # Clean up repetitions
            optimized = self._clean_repetitions(optimized)
            logger.info(f"After cleaning repetitions: {len(optimized)} chars")
            
            # Ensure we got a response
            if not optimized:
                logger.warning("⚠️ Empty response from Ollama, using original prompt")
                return user_prompt
            
            logger.info(f"✅ Optimization successful - Output: {len(optimized)} chars")
            logger.info(f"📝 Optimized prompt: {optimized[:200]}..." if len(optimized) > 200 else f"📝 Optimized prompt: {optimized}")
            return optimized
            
        except Exception as e:
            logger.error(f"❌ Ollama optimization failed: {e}", exc_info=True)
            logger.info(f"   Falling back to original prompt")
            return user_prompt
    
    def optimize_prompt(
        self,
        target_model: str,
        prompt: str,
        image: Optional[np.ndarray] = None,
        ollama_host: str = "localhost:11434",
        ollama_model: str = "qwen2.5vl:7b",
        temperature: float = 0.7,
        seed: int = -1,
        max_tokens_override: int = 0
    ) -> Tuple[str, str, str]:
        """
        Optimize prompt for target model
        
        Args:
            target_model: Target model to optimize for
            prompt: User's input prompt
            image: Optional image tensor
            ollama_host: Ollama server host
            ollama_model: Ollama model to use
            temperature: Temperature for response generation (0.0-2.0)
            seed: Random seed (-1 for random)
            max_tokens_override: Override max tokens (0 for model default)
        
        Returns:
            Tuple of (positive_prompt, negative_prompt, original_prompt)
        """
        logger.info(f"=" * 60)
        logger.info(f"🚀 Starting prompt optimization for: {target_model}")
        logger.info(f"📊 Input Parameters (after defaults applied):")
        logger.info(f"   Target Model: {target_model}")
        logger.info(f"   User Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        logger.info(f"   image: {'provided' if image is not None else 'none'}")
        if image is not None:
            logger.debug(f"   image details - Type: {type(image)}, Shape: {getattr(image, 'shape', 'N/A')}")
        logger.info(f"   ollama_host: {ollama_host}")
        logger.info(f"   ollama_model: {ollama_model}")
        logger.info(f"   temperature: {temperature}")
        logger.info(f"   seed: {seed}")
        logger.info(f"   max_tokens_override: {max_tokens_override}")
        logger.info(f"=" * 60)
        
        # Clean up any previous temp images
        self._cleanup_temp_images()
        
        # Get model configuration
        model_config = self.model_configs.get(target_model)
        if not model_config:
            logger.warning(f"⚠️ Unknown model '{target_model}', returning original prompt")
            return (prompt, "", prompt)
        
        logger.info(f"📋 Model Configuration:")
        logger.info(f"   Model name: {model_config.get('name', target_model)}")
        logger.info(f"   Supports negative: {model_config.get('supports_negative', False)}")
        logger.info(f"   Default max_tokens: {model_config.get('max_tokens', 'not specified')}")
        
        # Determine max_tokens to use
        max_tokens = max_tokens_override if max_tokens_override > 0 else model_config.get('max_tokens', None)
        logger.info(f"   Effective max_tokens: {max_tokens if max_tokens else 'Ollama default'}{' (user override)' if max_tokens_override > 0 else ''}")
        
        # Save image if provided
        image_path = None
        if image is not None:
            logger.info("🖼️ Processing image for Ollama...")
            image_path = self._save_image_for_ollama(image)
            if not image_path:
                logger.error("Failed to save image, continuing without it")
        
        # Initialize prompts
        positive_prompt = prompt
        negative_prompt = ""
        
        # Optimize positive prompt if output is connected
        if self._check_output_connected("positive_prompt"):
            positive_messages = model_config.get("positive_messages", [])
            if positive_messages:
                logger.info(f"🎯 Optimizing positive prompt for {model_config.get('name', target_model)}...")
                positive_prompt = self._optimize_with_ollama(
                    positive_messages,
                    prompt,
                    image_path,
                    ollama_host,
                    ollama_model,
                    temperature,
                    seed,
                    max_tokens
                )
                logger.info(f"   Positive result: {len(positive_prompt)} chars")
        else:
            logger.debug("Positive prompt output not connected, skipping optimization")
        
        # Optimize negative prompt if supported and output is connected
        if model_config.get("supports_negative", False) and self._check_output_connected("negative_prompt"):
            negative_messages = model_config.get("negative_messages", [])
            if negative_messages:
                logger.info(f"🎯 Optimizing negative prompt for {model_config.get('name', target_model)}...")
                logger.info(f"   Target model: {target_model}")
                logger.info(f"   Temperature: {temperature}")
                logger.info(f"   Number of negative messages: {len(negative_messages)}")
                
                # Debug: Log the system prompt being used for negative generation
                if negative_messages and negative_messages[0].get("role") == "system":
                    system_content = negative_messages[0].get("content", "")
                    logger.info(f"   Full negative system prompt: {system_content}")
                    # Check if this is a video-related prompt
                    if "video" in system_content.lower() or "motion" in system_content.lower() or "-no" in system_content:
                        logger.warning(f"⚠️ Detected video-related negative prompt system message for image model {target_model}")
                
                # Pass only the original prompt for negative generation to avoid confusion
                # The optimized prompt might add details that shouldn't be excluded
                import time
                prompt_with_timestamp = f"{prompt}\n[Request ID: {time.time()}]"
                logger.info(f"   Full prompt for negative generation: {prompt_with_timestamp}")
                logger.info(f"   Using fixed temperature 0.2 for negative prompt generation")
                
                negative_prompt = self._optimize_with_ollama(
                    negative_messages,
                    prompt_with_timestamp,  # Use only original prompt
                    None,  # Don't include image for negative prompts
                    ollama_host,
                    ollama_model,
                    0.2,  # Lower temperature for more consistent negative prompts
                    seed,
                    max_tokens
                )
                
                # Remove any timestamp artifacts from the response
                if "[Request ID:" in negative_prompt:
                    negative_prompt = negative_prompt.split("[Request ID:")[0].strip()
                
                # Check for video-related terms in image models and filter them out
                is_image_model = target_model in ["flux_dev", "flux_krea", "flux_kontext", "chroma_hd", "ace_step", "qwen_image_edit"]
                if is_image_model:
                    video_terms = ["frame rate", "fps", "frame count", "temporal", "sound", "dialogue", "music", 
                                  "ambient sounds", "narrative", "plot", "video", "animation", "keyframe"]
                    original_negative = negative_prompt
                    
                    # Filter out video-related terms
                    negative_items = [item.strip() for item in negative_prompt.split(",")]
                    filtered_items = []
                    removed_items = []
                    
                    for item in negative_items:
                        if not any(term in item.lower() for term in video_terms):
                            filtered_items.append(item)
                        else:
                            removed_items.append(item)
                    
                    if removed_items:
                        logger.warning(f"⚠️ Filtered video-related terms from image model negative prompt: {', '.join(removed_items)}")
                        negative_prompt = ", ".join(filtered_items)
                
                # Check for excessive repetition (more than 3 occurrences of the same phrase)
                import re
                from collections import Counter
                
                # Split by comma and count occurrences
                items = [item.strip() for item in negative_prompt.split(",") if item.strip()]
                item_counts = Counter(items)
                
                # Check for any item repeated more than 2 times
                repetitive_items = {item: count for item, count in item_counts.items() if count > 2}
                if repetitive_items:
                    logger.warning(f"⚠️ Detected repetitive items in negative prompt: {repetitive_items}")
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_items = []
                    for item in items:
                        if item not in seen:
                            seen.add(item)
                            unique_items.append(item)
                    negative_prompt = ", ".join(unique_items)
                    logger.info(f"   Deduplicated negative prompt to {len(unique_items)} unique items")
                
                logger.info(f"   Negative result: {len(negative_prompt)} chars")
                logger.info(f"   Full negative prompt: {negative_prompt}")
        else:
            if not model_config.get("supports_negative", False):
                logger.debug(f"Model {target_model} doesn't support negative prompts")
            else:
                logger.debug("Negative prompt output not connected, skipping optimization")
        
        # Clean up temporary images
        self._cleanup_temp_images()
        
        logger.info(f"=" * 60)
        logger.info(f"✅ Optimization complete!")
        logger.info(f"   Positive: {len(positive_prompt)} chars")
        if positive_prompt != prompt:
            logger.info(f"   📝 Positive: {positive_prompt[:150]}..." if len(positive_prompt) > 150 else f"   📝 Positive: {positive_prompt}")
        logger.info(f"   Negative: {len(negative_prompt)} chars")
        if negative_prompt:
            logger.info(f"   📝 Negative: {negative_prompt[:150]}..." if len(negative_prompt) > 150 else f"   📝 Negative: {negative_prompt}")
        logger.info(f"=" * 60)
        
        # Log what we're returning
        result = (positive_prompt, negative_prompt, prompt)
        logger.info(f"🔄 Returning from PromptOptimizer:")
        logger.info(f"   Return type: {type(result)}")
        logger.info(f"   Return length: {len(result)} elements")
        logger.info(f"   [0] positive_prompt: type={type(result[0])}, len={len(result[0])} chars")
        logger.info(f"   [1] negative_prompt: type={type(result[1])}, len={len(result[1])} chars")
        logger.info(f"   [2] original_prompt: type={type(result[2])}, len={len(result[2])} chars")
        logger.debug(f"   Full return value: {result}")
        
        # Return optimized prompts and original
        return result
    
    def __del__(self):
        """Cleanup on deletion"""
        self._cleanup_temp_images()


# Node registration
NODE_CLASS_MAPPINGS = {
    "PromptOptimizer": PromptOptimizer
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptOptimizer": "Prompt Optimizer (Ollama)"
}