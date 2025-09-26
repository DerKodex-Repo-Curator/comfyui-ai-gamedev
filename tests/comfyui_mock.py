"""
ComfyUI Mock Framework
Simulates ComfyUI environment for unit testing nodes
"""

import torch
import numpy as np
from typing import Any, Dict, List, Tuple, Optional
from unittest.mock import Mock, MagicMock
import tempfile
import os
from pathlib import Path


class MockFolderPaths:
    """Mock ComfyUI folder_paths module"""
    
    @staticmethod
    def get_output_directory() -> str:
        """Return a temporary directory for test outputs"""
        return str(Path(__file__).parent.parent / "test_output")


class MockVideoInput:
    """Mock ComfyUI VideoInput object"""
    
    def __init__(self, frames: torch.Tensor, audio: Optional[torch.Tensor] = None, metadata: Optional[Dict] = None):
        """
        Initialize mock video input
        
        Args:
            frames: Tensor of video frames (B, H, W, C) in float32 format [0, 1]
            audio: Optional audio tensor
            metadata: Optional metadata dict
        """
        self.images = frames  # ComfyUI uses .images for frame data
        self.audio = audio
        self.metadata = metadata or {}
    
    def get_components(self):
        """Return video components (mimics ComfyUI VideoInput.get_components())"""
        return MockVideoComponents(self.images, self.audio, self.metadata)


class MockVideoComponents:
    """Mock ComfyUI VideoComponents object returned by VideoInput.get_components()"""
    
    def __init__(self, images: torch.Tensor, audio: Optional[torch.Tensor] = None, metadata: Optional[Dict] = None):
        self.images = images
        self.audio = audio
        self.metadata = metadata or {}


class ComfyUIMockContext:
    """Context manager that sets up ComfyUI simulation environment"""
    
    def __init__(self):
        self.original_modules = {}
        self.temp_dirs = []
    
    def __enter__(self):
        # Mock folder_paths if not already available
        import sys
        if 'folder_paths' not in sys.modules:
            sys.modules['folder_paths'] = MockFolderPaths()
        
        # Create test output directory
        test_output = Path(__file__).parent.parent / "test_output"
        test_output.mkdir(exist_ok=True)
        (test_output / "mesh").mkdir(exist_ok=True)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup temporary directories
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)


def create_test_image_tensor(batch_size: int = 1, height: int = 128, width: int = 128, channels: int = 3) -> torch.Tensor:
    """
    Create a test image tensor in ComfyUI format
    
    Args:
        batch_size: Number of images in batch
        height: Image height
        width: Image width
        channels: Number of channels (3 for RGB)
    
    Returns:
        Tensor in format (B, H, W, C) with values in range [0, 1]
    """
    # Create random image data
    image_data = torch.rand(batch_size, height, width, channels, dtype=torch.float32)
    return image_data


def create_test_video_input(num_frames: int = 10, height: int = 128, width: int = 128, channels: int = 3) -> MockVideoInput:
    """
    Create a test video input object
    
    Args:
        num_frames: Number of frames in video
        height: Frame height
        width: Frame width
        channels: Number of channels (3 for RGB)
    
    Returns:
        MockVideoInput object with test frames
    """
    frames = create_test_image_tensor(num_frames, height, width, channels)
    return MockVideoInput(frames)


def numpy_to_comfyui_tensor(array: np.ndarray) -> torch.Tensor:
    """
    Convert numpy array to ComfyUI tensor format
    
    Args:
        array: Numpy array in various formats
    
    Returns:
        Tensor in ComfyUI format (B, H, W, C) with float32 values [0, 1]
    """
    # Convert to torch tensor
    if not isinstance(array, torch.Tensor):
        tensor = torch.from_numpy(array)
    else:
        tensor = array
    
    # Ensure float32
    if tensor.dtype != torch.float32:
        tensor = tensor.float()
    
    # Normalize to [0, 1] if needed
    if tensor.dtype == torch.uint8 or tensor.max() > 1:
        tensor = tensor / 255.0
    
    # Ensure 4D tensor (B, H, W, C)
    if len(tensor.shape) == 3:  # (H, W, C)
        tensor = tensor.unsqueeze(0)  # Add batch dimension
    elif len(tensor.shape) == 2:  # (H, W) grayscale
        tensor = tensor.unsqueeze(0).unsqueeze(-1)  # Add batch and channel
        tensor = tensor.repeat(1, 1, 1, 3)  # Convert to RGB
    
    return tensor


class MockComfyUINode:
    """Base class for testing ComfyUI nodes"""
    
    @classmethod
    def setup_test_environment(cls):
        """Set up test environment for ComfyUI nodes"""
        return ComfyUIMockContext()
    
    def simulate_comfyui_execution(self, node_instance, method_name: str, **kwargs) -> Any:
        """
        Simulate ComfyUI calling a node method
        
        Args:
            node_instance: Instance of the node to test
            method_name: Name of the method to call (usually the FUNCTION attribute)
            **kwargs: Arguments to pass to the method
        
        Returns:
            Result of the method call
        """
        method = getattr(node_instance, method_name)
        return method(**kwargs)


# Specific mock classes for different node types

class MockOllama:
    """Mock Ollama client for testing PromptOptimizer"""
    
    def __init__(self, responses: Optional[List[Dict]] = None):
        self.responses = responses or []
        self.call_count = 0
    
    def Client(self, host: str = None):
        """Create mock client"""
        return MockOllamaClient(self.responses)


class MockOllamaClient:
    """Mock Ollama client instance"""
    
    def __init__(self, responses: List[Dict]):
        self.responses = responses
        self.call_count = 0
    
    def chat(self, model: str, messages: List[Dict], options: Optional[Dict] = None):
        """Mock chat method"""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        else:
            # Default response if no more responses provided
            response = {
                "message": {"content": "Default test response"},
                "prompt_eval_count": 100,
                "eval_count": 50,
                "prompt_eval_duration": 1000000000,  # 1 second in nanoseconds
                "eval_duration": 500000000  # 0.5 seconds in nanoseconds
            }
        
        self.call_count += 1
        return response


def create_mock_subprocess_result(stdout: str = "", stderr: str = "", returncode: int = 0):
    """Create a mock subprocess result"""
    result = Mock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result