"""
AI-powered visual validator using Ollama + qwen2.5vl:7b for automated frame analysis
"""

import sys
import tempfile
from pathlib import Path
from typing import List, Tuple, Optional, Union
from PIL import Image
import torch
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class AIVisualValidator:
    """AI-powered visual validator using qwen2.5vl:7b model"""
    
    def __init__(self, ollama_host: str = "localhost:11434", model: str = "qwen2.5vl:7b"):
        """Initialize the AI visual validator"""
        if not OLLAMA_AVAILABLE:
            raise ImportError("Ollama not available. Install with: pip install ollama")
        
        self.ollama_host = ollama_host
        self.model = model
        self.client = ollama.Client(host=ollama_host)
        
        # Verify model is available
        try:
            models_response = self.client.list()
            models = [model.get('model', model.get('name', '')) for model in models_response.get('models', [])]
            if self.model not in models:
                raise ValueError(f"Model {self.model} not found. Available models: {models}")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Ollama at {ollama_host}: {e}")
    
    def _tensor_to_pil_images(self, frames: torch.Tensor) -> List[Image.Image]:
        """Convert ComfyUI tensor format to PIL Images"""
        pil_images = []
        
        for i in range(frames.shape[0]):  # Iterate over batch dimension
            # Extract single frame: (H, W, C)
            frame = frames[i].cpu().numpy()
            
            # Convert from [0,1] float to [0,255] uint8
            frame_uint8 = (frame * 255).astype(np.uint8)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_uint8, mode='RGB')
            pil_images.append(pil_image)
        
        return pil_images
    
    def _save_temp_images(self, pil_images: List[Image.Image]) -> List[str]:
        """Save PIL images to temporary files and return paths"""
        temp_paths = []
        
        for i, pil_image in enumerate(pil_images):
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=f'_frame_{i:03d}.png', delete=False) as tmp_file:
                temp_path = tmp_file.name
                pil_image.save(temp_path)
                temp_paths.append(temp_path)
        
        return temp_paths
    
    def _cleanup_temp_images(self, temp_paths: List[str]):
        """Clean up temporary image files"""
        for temp_path in temp_paths:
            try:
                Path(temp_path).unlink()
            except Exception:
                pass  # Ignore cleanup errors
    
    def _parse_ai_response(self, response: str) -> Tuple[bool, str, str]:
        """Parse AI response into (passed, description, reason)"""
        lines = response.strip().split('\n')
        
        # First line should be PASS or FAIL
        if not lines:
            return False, "No response", "Empty response from AI"
        
        result_line = lines[0].strip().upper()
        passed = result_line == "PASS"
        
        # Find description and reason sections
        description = ""
        reason = ""
        
        # Look for sections separated by double newlines
        sections = response.strip().split('\n\n')
        
        if len(sections) >= 2:
            description = sections[1].strip()
        
        if len(sections) >= 3:
            reason = sections[2].strip()
        elif not passed:
            reason = "AI marked as FAIL but provided no reason"
        
        return passed, description, reason
    
    def validate_frames(self, frames: torch.Tensor, prompt: str) -> Tuple[bool, str, str]:
        """
        Validate extracted frames using AI
        
        Args:
            frames: ComfyUI tensor format (batch, height, width, channels) in [0,1] range
            prompt: Description of what the frames should contain
            
        Returns:
            Tuple of (passed, description, reason)
        """
        # Convert to PIL images
        pil_images = self._tensor_to_pil_images(frames)
        
        # Save to temporary files
        temp_paths = self._save_temp_images(pil_images)
        
        try:
            # Create system prompt
            system_prompt = (
                "You are an integration tester. You will be given images and a description of what they should contain. "
                "You must output exactly this format:\n"
                "First line: PASS or FAIL\n"
                "Empty line\n"
                "Description of what you actually see in the images\n"
                "Empty line\n"
                "Reason for failure (only if FAIL)\n\n"
                "Always provide a description of what you see, even if the result is PASS."
            )
            
            # Prepare messages for Ollama
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": prompt,
                    "images": temp_paths
                }
            ]
            
            # Debug: Print what we're sending to Ollama
            print(f"🤖 Sending to Ollama ({self.model}):")
            print(f"   System prompt: {system_prompt[:100]}...")
            print(f"   User prompt: {prompt}")
            print(f"   Images: {len(temp_paths)} image(s)")
            
            # Call Ollama API
            response = self.client.chat(
                model=self.model,
                messages=messages
            )
            
            ai_response = response['message']['content']
            
            # Debug: Print Ollama's response
            print(f"🔍 Ollama response:")
            print(f"   {ai_response}")
            print()
            
            # Parse response
            passed, description, reason = self._parse_ai_response(ai_response)
            
            return passed, description, reason
            
        finally:
            # Clean up temporary files
            self._cleanup_temp_images(temp_paths)
    
    def validate_single_frame(self, frame: torch.Tensor, prompt: str) -> Tuple[bool, str, str]:
        """Validate a single frame (convenience method)"""
        if len(frame.shape) == 3:
            # Add batch dimension if missing
            frame = frame.unsqueeze(0)
        
        return self.validate_frames(frame, prompt)


class AIValidationError(Exception):
    """Raised when AI validation fails"""
    
    def __init__(self, description: str, reason: str):
        self.description = description
        self.reason = reason
        super().__init__(f"AI Validation Failed - Saw: {description}, Reason: {reason}")