"""
Unit tests for Frame Extractor node
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import torch
import numpy as np
from pathlib import Path
import sys
import cv2

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.frame_extractor.frame_extractor_node import FrameExtractorNode


class TestFrameExtractorNode(unittest.TestCase):
    """Test suite for Frame Extractor node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.node = FrameExtractorNode()
        
    def test_node_class_attributes(self):
        """Test that node has correct class attributes"""
        self.assertEqual(FrameExtractorNode.RETURN_TYPES, ("IMAGE",))
        self.assertEqual(FrameExtractorNode.RETURN_NAMES, ("frames",))
        self.assertEqual(FrameExtractorNode.FUNCTION, "extract_frames")
        self.assertEqual(FrameExtractorNode.CATEGORY, "gamedev/video")
        self.assertFalse(FrameExtractorNode.OUTPUT_NODE)
        
    def test_input_types(self):
        """Test INPUT_TYPES class method"""
        input_types = FrameExtractorNode.INPUT_TYPES()
        
        # Check required inputs
        self.assertIn("required", input_types)
        self.assertIn("video", input_types["required"])
        self.assertIn("frame_count", input_types["required"])
        self.assertIn("skip_start_frames", input_types["required"])
        self.assertIn("skip_end_frames", input_types["required"])
        
        # Check default values
        video_config = input_types["required"]["video"]
        self.assertEqual(video_config[1]["default"], "")
        
        frame_count_config = input_types["required"]["frame_count"]
        self.assertEqual(frame_count_config[1]["default"], 0)
        self.assertEqual(frame_count_config[1]["min"], 0)
        self.assertEqual(frame_count_config[1]["max"], 1000)
        
    @patch('os.path.exists')
    @patch('cv2.VideoCapture')
    def test_extract_frames_evenly_distributed(self, mock_video_capture, mock_exists):
        """Test that frames are extracted evenly distributed"""
        mock_exists.return_value = True
        # Mock video capture
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        
        # Configure mock
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 100,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        # Mock frame reading
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)
        
        # Test extraction
        result = self.node.extract_frames(
            video="test.mp4",
            frame_count=10,
            skip_start_frames=10,
            skip_end_frames=10
        )
        
        # Verify video was opened
        mock_video_capture.assert_called_once_with("test.mp4")
        
        # Calculate expected frame indices
        # Usable range: frames 10-89 (80 frames)
        # Step size: 80/10 = 8
        # Expected indices: 10, 18, 26, 34, 42, 50, 58, 66, 74, 82
        
        # Check that set was called with correct frame positions
        set_calls = [call for call in mock_cap.mock_calls if 'set' in str(call)]
        self.assertEqual(len(set_calls), 10)
        
    @patch('os.path.exists')
    @patch('cv2.VideoCapture')
    def test_extract_frames_error_handling(self, mock_video_capture, mock_exists):
        """Test error handling for invalid video"""
        # Test with non-existent file
        mock_exists.return_value = False
        with self.assertRaises(ValueError) as context:
            self.node.extract_frames(
                video="/nonexistent/video.mp4",
                frame_count=10,
                skip_start_frames=0,
                skip_end_frames=0
            )
        self.assertIn("Video file not found", str(context.exception))
        
        # Test with video that can't be opened
        mock_exists.return_value = True
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False
        
        with self.assertRaises(ValueError) as context:
            self.node.extract_frames(
                video="test.mp4",
                frame_count=10,
                skip_start_frames=0,
                skip_end_frames=0
            )
        self.assertIn("Could not open video file", str(context.exception))
        
    @patch('os.path.exists')
    @patch('cv2.VideoCapture')
    def test_skip_frames_validation(self, mock_video_capture, mock_exists):
        """Test that skip frames are validated correctly"""
        mock_exists.return_value = True
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 50,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        # Test skipping too many frames
        with self.assertRaises(ValueError) as context:
            self.node.extract_frames(
                video="test.mp4",
                frame_count=10,
                skip_start_frames=25,
                skip_end_frames=26  # Total skip = 51, more than 50 frames
            )
        self.assertIn("No frames remaining", str(context.exception))
        
    @patch('os.path.exists')
    @patch('cv2.VideoCapture')
    def test_output_tensor_format(self, mock_video_capture, mock_exists):
        """Test that output is in correct tensor format"""
        mock_exists.return_value = True
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 30,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        # Create test frames
        test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 127
        mock_cap.read.return_value = (True, test_frame)
        
        result = self.node.extract_frames(
            video="test.mp4",
            frame_count=5,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Check output format
        frames_tensor = result[0]
        self.assertIsInstance(frames_tensor, torch.Tensor)
        self.assertEqual(frames_tensor.shape[0], 5)  # 5 frames
        self.assertEqual(frames_tensor.shape[3], 3)  # RGB channels
        self.assertEqual(frames_tensor.dtype, torch.float32)
        
        # Check value range [0, 1]
        self.assertTrue(torch.all(frames_tensor >= 0))
        self.assertTrue(torch.all(frames_tensor <= 1))
    
    @patch('os.path.exists')
    @patch('cv2.VideoCapture')
    def test_extract_all_frames_with_zero(self, mock_video_capture, mock_exists):
        """Test that frame_count=0 extracts all available frames"""
        mock_exists.return_value = True
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 30,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        test_frame = np.ones((480, 640, 3), dtype=np.uint8) * 127
        mock_cap.read.return_value = (True, test_frame)
        
        # Test with frame_count=0 (should extract all 20 frames after skipping)
        result = self.node.extract_frames(
            video="test.mp4",
            frame_count=0,
            skip_start_frames=5,
            skip_end_frames=5
        )
        
        # Should extract frames 5-24 (20 frames total)
        frames_tensor = result[0]
        self.assertEqual(frames_tensor.shape[0], 20)


class TestFrameExtractorIntegration(unittest.TestCase):
    """Integration tests for Frame Extractor"""
    
    @unittest.skipUnless(
        Path("/home/matt/src/comfyui-ai-gamedev/examples/ship.mp4").exists(),
        "Test video not found"
    )
    def test_with_real_video(self):
        """Test with real video file (if available)"""
        node = FrameExtractorNode()
        
        try:
            result = node.extract_frames(
                video="/home/matt/src/comfyui-ai-gamedev/examples/ship.mp4",
                frame_count=5,
                skip_start_frames=5,
                skip_end_frames=5
            )
            
            frames = result[0]
            # Verify we got frames
            self.assertEqual(frames.shape[0], 5)
            self.assertEqual(len(frames.shape), 4)  # batch, height, width, channels
            self.assertEqual(frames.shape[3], 3)  # RGB
            
        except Exception as e:
            # If OpenCV is not installed, skip
            if "cv2" in str(e):
                self.skipTest("OpenCV not installed")
            raise


if __name__ == "__main__":
    unittest.main()