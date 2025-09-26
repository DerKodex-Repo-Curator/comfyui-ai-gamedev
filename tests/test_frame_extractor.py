"""
Unit tests for VideoFrameExtractor node that simulate ComfyUI execution
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import torch
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.frame_extractor.frame_extractor_node import VideoFrameExtractorNode
from tests.comfyui_mock import ComfyUIMockContext, create_test_video_input, MockComfyUINode


class TestVideoFrameExtractorNode(unittest.TestCase, MockComfyUINode):
    """Test suite for VideoFrameExtractor node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = VideoFrameExtractorNode()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
        
    def test_node_class_attributes(self):
        """Test that node has correct class attributes"""
        self.assertEqual(VideoFrameExtractorNode.RETURN_TYPES, ("IMAGE", "INT", "INT"))
        self.assertEqual(VideoFrameExtractorNode.RETURN_NAMES, ("frames", "total_frames", "extracted_count"))
        self.assertEqual(VideoFrameExtractorNode.FUNCTION, "extract_frames")
        self.assertEqual(VideoFrameExtractorNode.CATEGORY, "🎮 AI GameDev/Video")
        self.assertFalse(VideoFrameExtractorNode.OUTPUT_NODE)
        
    def test_input_types(self):
        """Test INPUT_TYPES class method"""
        input_types = VideoFrameExtractorNode.INPUT_TYPES()
        
        # Check required inputs
        self.assertIn("required", input_types)
        self.assertIn("video", input_types["required"])
        self.assertIn("frame_count", input_types["required"])
        self.assertIn("skip_start_frames", input_types["required"])
        self.assertIn("skip_end_frames", input_types["required"])
        
        # Check video input type
        video_config = input_types["required"]["video"]
        self.assertEqual(video_config[0], "VIDEO")
        
        frame_count_config = input_types["required"]["frame_count"]
        self.assertEqual(frame_count_config[1]["default"], 0)
        self.assertEqual(frame_count_config[1]["min"], 0)
        self.assertEqual(frame_count_config[1]["max"], 1000)
        
    def test_extract_frames_evenly_distributed(self):
        """Test that frames are extracted evenly distributed"""
        # Create test video with 100 frames
        video_input = create_test_video_input(num_frames=100, height=240, width=320)
        
        # Test extraction - should extract 10 frames from frames 10-89 (80 usable frames)
        result = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=video_input,
            frame_count=10,
            skip_start_frames=10,
            skip_end_frames=10
        )
        
        frames, total_frames, extracted_count = result
        
        # Check return values
        self.assertIsInstance(frames, torch.Tensor)
        self.assertEqual(total_frames, 100)
        self.assertEqual(extracted_count, 10)
        
        # Check frame tensor shape
        self.assertEqual(frames.shape[0], 10)  # 10 extracted frames
        self.assertEqual(frames.shape[1], 240)  # height
        self.assertEqual(frames.shape[2], 320)  # width
        self.assertEqual(frames.shape[3], 3)  # RGB channels
        
    def test_extract_frames_error_handling(self):
        """Test error handling for invalid parameters"""
        # Create test video with 50 frames
        video_input = create_test_video_input(num_frames=50)
        
        # Test skipping too many frames
        with self.assertRaises(ValueError) as context:
            self.simulate_comfyui_execution(
                self.node,
                "extract_frames",
                video=video_input,
                frame_count=10,
                skip_start_frames=25,
                skip_end_frames=26  # Total skip = 51, more than 50 frames
            )
        self.assertIn("No frames remaining", str(context.exception))
        
        # Test invalid tensor shape
        invalid_video = Mock()
        invalid_video.get_components.return_value.images = torch.rand(2, 2)  # Invalid 2D tensor
        
        with self.assertRaises(ValueError) as context:
            self.simulate_comfyui_execution(
                self.node,
                "extract_frames",
                video=invalid_video,
                frame_count=5,
                skip_start_frames=0,
                skip_end_frames=0
            )
        self.assertIn("Expected 3D or 4D tensor", str(context.exception))
        
    def test_skip_frames_validation(self):
        """Test that skip frames are validated correctly"""
        # Create test video with 50 frames
        video_input = create_test_video_input(num_frames=50)
        
        # Test valid skipping
        result = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=video_input,
            frame_count=10,
            skip_start_frames=5,
            skip_end_frames=5
        )
        
        frames, total_frames, extracted_count = result
        self.assertEqual(total_frames, 50)
        self.assertEqual(extracted_count, 10)
        # Should extract from frames 5-44 (40 usable frames)
        
    def test_output_tensor_format(self):
        """Test that output is in correct tensor format"""
        # Create test video with specific values
        video_input = create_test_video_input(num_frames=30, height=480, width=640)
        
        result = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=video_input,
            frame_count=5,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Check output format
        frames_tensor, total_frames, extracted_count = result
        self.assertIsInstance(frames_tensor, torch.Tensor)
        self.assertEqual(frames_tensor.shape[0], 5)  # 5 frames
        self.assertEqual(frames_tensor.shape[1], 480)  # height
        self.assertEqual(frames_tensor.shape[2], 640)  # width
        self.assertEqual(frames_tensor.shape[3], 3)  # RGB channels
        self.assertEqual(frames_tensor.dtype, torch.float32)
        
        # Check value range [0, 1]
        self.assertTrue(torch.all(frames_tensor >= 0))
        self.assertTrue(torch.all(frames_tensor <= 1))
        
        # Check other return values
        self.assertEqual(total_frames, 30)
        self.assertEqual(extracted_count, 5)
    
    def test_extract_all_frames_with_zero(self):
        """Test that frame_count=0 extracts all available frames"""
        # Create test video with 30 frames
        video_input = create_test_video_input(num_frames=30)
        
        # Test with frame_count=0 (should extract all 20 frames after skipping)
        result = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=video_input,
            frame_count=0,  # Extract all frames
            skip_start_frames=5,
            skip_end_frames=5
        )
        
        # Should extract frames 5-24 (20 frames total)
        frames_tensor, total_frames, extracted_count = result
        self.assertEqual(frames_tensor.shape[0], 20)
        self.assertEqual(total_frames, 30)
        self.assertEqual(extracted_count, 20)


    def test_single_frame_video(self):
        """Test with single frame video"""
        # Create single frame video
        video_input = create_test_video_input(num_frames=1)
        
        result = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=video_input,
            frame_count=1,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        frames_tensor, total_frames, extracted_count = result
        self.assertEqual(frames_tensor.shape[0], 1)
        self.assertEqual(total_frames, 1)
        self.assertEqual(extracted_count, 1)


class TestVideoFrameExtractorIntegration(unittest.TestCase, MockComfyUINode):
    """Integration tests for VideoFrameExtractor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_node_registration(self):
        """Test node is properly registered for ComfyUI"""
        from nodes.frame_extractor import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
        
        self.assertIn("VideoFrameExtractor", NODE_CLASS_MAPPINGS)
        self.assertEqual(NODE_CLASS_MAPPINGS["VideoFrameExtractor"], VideoFrameExtractorNode)
        
        self.assertIn("VideoFrameExtractor", NODE_DISPLAY_NAME_MAPPINGS)
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["VideoFrameExtractor"], "🎮 Video Frame Extractor")
    
    def test_large_video_performance(self):
        """Test performance with larger video"""
        # Create larger test video
        video_input = create_test_video_input(num_frames=1000, height=480, width=640)
        
        node = VideoFrameExtractorNode()
        result = self.simulate_comfyui_execution(
            node,
            "extract_frames",
            video=video_input,
            frame_count=50,
            skip_start_frames=10,
            skip_end_frames=10
        )
        
        frames_tensor, total_frames, extracted_count = result
        self.assertEqual(frames_tensor.shape[0], 50)
        self.assertEqual(total_frames, 1000)
        self.assertEqual(extracted_count, 50)
        
        # Verify frames are properly distributed
        self.assertEqual(frames_tensor.dtype, torch.float32)


if __name__ == "__main__":
    unittest.main()