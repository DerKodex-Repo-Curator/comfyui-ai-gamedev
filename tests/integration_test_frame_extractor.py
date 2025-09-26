"""
Integration tests for VideoFrameExtractor that actually execute with real video files
These tests skip ComfyUI but test the actual frame extraction logic with real data
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path
import torch
import numpy as np
import cv2
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.frame_extractor.frame_extractor_node import VideoFrameExtractorNode
from tests.comfyui_mock import ComfyUIMockContext, MockComfyUINode


class MockVideoInputFromFile:
    """Mock VideoInput that loads from actual video file"""
    
    def __init__(self, video_path):
        self.video_path = video_path
        self._load_video()
    
    def _load_video(self):
        """Load video frames using OpenCV"""
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {self.video_path}")
        
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Normalize to [0, 1] and convert to float32
            frame_normalized = frame_rgb.astype(np.float32) / 255.0
            frames.append(frame_normalized)
        
        cap.release()
        
        if not frames:
            raise ValueError("No frames found in video")
        
        # Convert to tensor format (B, H, W, C)
        self.images = torch.from_numpy(np.stack(frames))
        self.total_frames = len(frames)
        self.height, self.width, self.channels = frames[0].shape
        
        print(f"Loaded video: {self.total_frames} frames, {self.height}x{self.width}x{self.channels}")
    
    def get_components(self):
        """Return video components"""
        return Mock(images=self.images)


class TestVideoFrameExtractorIntegration(unittest.TestCase, MockComfyUINode):
    """Integration tests with real video execution"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        cls.test_video_path = Path(__file__).parent.parent / "examples" / "ship.mp4"
        
        # Skip all tests if video file doesn't exist
        if not cls.test_video_path.exists():
            raise unittest.SkipTest(f"Test video not found: {cls.test_video_path}")
        
        # Get video info for verification
        cls.video_info = cls._get_video_info(cls.test_video_path)
        print(f"Test video info: {cls.video_info}")
    
    @staticmethod
    def _get_video_info(video_path):
        """Get video information using OpenCV"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
            
        info = {
            'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS)
        }
        cap.release()
        return info
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = VideoFrameExtractorNode()
        
        # Create mock video input from real file
        self.video_input = MockVideoInputFromFile(self.test_video_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_extract_all_frames_real_video(self):
        """Test extracting all frames from real video"""
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=self.video_input,
            frame_count=0,  # Extract all frames
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Verify frame count matches video
        self.assertEqual(total_frames, self.video_info['total_frames'])
        self.assertEqual(extracted_count, self.video_info['total_frames'])
        self.assertEqual(frames.shape[0], self.video_info['total_frames'])
        
        # Verify frame dimensions
        self.assertEqual(frames.shape[1], self.video_info['height'])  # height
        self.assertEqual(frames.shape[2], self.video_info['width'])   # width
        self.assertEqual(frames.shape[3], 3)                         # RGB channels
        
        # Verify tensor properties
        self.assertEqual(frames.dtype, torch.float32)
        self.assertTrue(torch.all(frames >= 0.0))
        self.assertTrue(torch.all(frames <= 1.0))
        
        print(f"✅ Successfully extracted {extracted_count} frames from real video")
        print(f"   Frame tensor shape: {frames.shape}")
        print(f"   Value range: [{frames.min():.3f}, {frames.max():.3f}]")
    
    def test_extract_subset_frames_even_distribution(self):
        """Test extracting subset of frames with even distribution"""
        requested_count = 5
        
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames", 
            video=self.video_input,
            frame_count=requested_count,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Verify counts
        self.assertEqual(total_frames, self.video_info['total_frames'])
        self.assertEqual(extracted_count, requested_count)
        self.assertEqual(frames.shape[0], requested_count)
        
        # Verify dimensions match original video
        self.assertEqual(frames.shape[1], self.video_info['height'])
        self.assertEqual(frames.shape[2], self.video_info['width'])
        self.assertEqual(frames.shape[3], 3)
        
        # Verify frames are different (not duplicates)
        frame_differences = []
        for i in range(1, requested_count):
            diff = torch.mean(torch.abs(frames[i] - frames[i-1])).item()
            frame_differences.append(diff)
        
        # Frames should be different (mean difference > 0.01)
        avg_difference = np.mean(frame_differences)
        self.assertGreater(avg_difference, 0.01, "Extracted frames appear to be duplicates")
        
        print(f"✅ Successfully extracted {requested_count} evenly distributed frames")
        print(f"   Average frame difference: {avg_difference:.4f}")
    
    def test_skip_frames_functionality(self):
        """Test skipping frames at start and end"""
        skip_start = 2
        skip_end = 3
        requested_count = 5
        
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=self.video_input,
            frame_count=requested_count,
            skip_start_frames=skip_start,
            skip_end_frames=skip_end
        )
        
        # Verify counts
        self.assertEqual(total_frames, self.video_info['total_frames'])
        self.assertEqual(extracted_count, requested_count)
        
        # Verify usable frame range
        usable_frames = self.video_info['total_frames'] - skip_start - skip_end
        self.assertGreater(usable_frames, 0, "No frames remaining after skipping")
        self.assertGreaterEqual(usable_frames, requested_count, "Not enough frames after skipping")
        
        # Verify frame properties
        self.assertEqual(frames.shape, (requested_count, self.video_info['height'], self.video_info['width'], 3))
        self.assertEqual(frames.dtype, torch.float32)
        
        print(f"✅ Successfully skipped {skip_start} start + {skip_end} end frames")
        print(f"   Extracted {extracted_count} from {usable_frames} usable frames")
    
    def test_frame_quality_and_content(self):
        """Test that extracted frames contain meaningful image data"""
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=self.video_input,
            frame_count=3,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        for i, frame in enumerate(frames):
            # Check frame is not blank (all zeros or ones)
            mean_value = torch.mean(frame).item()
            std_value = torch.std(frame).item()
            
            self.assertGreater(mean_value, 0.01, f"Frame {i} appears to be blank (too dark)")
            self.assertLess(mean_value, 0.99, f"Frame {i} appears to be blank (too bright)")
            self.assertGreater(std_value, 0.01, f"Frame {i} has no variation (flat color)")
            
            # Check for reasonable color distribution across channels
            r_mean = torch.mean(frame[:, :, 0]).item()
            g_mean = torch.mean(frame[:, :, 1]).item()  
            b_mean = torch.mean(frame[:, :, 2]).item()
            
            # Ensure we have actual color information, not just grayscale
            channel_variation = max(r_mean, g_mean, b_mean) - min(r_mean, g_mean, b_mean)
            
            print(f"Frame {i}: mean={mean_value:.3f}, std={std_value:.3f}, "
                  f"RGB=({r_mean:.3f}, {g_mean:.3f}, {b_mean:.3f}), var={channel_variation:.3f}")
        
        print(f"✅ All {extracted_count} frames contain meaningful image data")
    
    def test_large_frame_count_extraction(self):
        """Test extracting more frames than available (should cap to available)"""
        large_count = self.video_info['total_frames'] + 10
        
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=self.video_input,
            frame_count=large_count,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Should cap to available frame count
        self.assertEqual(extracted_count, self.video_info['total_frames'])
        self.assertEqual(frames.shape[0], self.video_info['total_frames'])
        
        print(f"✅ Correctly capped {large_count} requested frames to {extracted_count} available frames")
    
    def test_single_frame_extraction(self):
        """Test extracting exactly one frame"""
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node,
            "extract_frames",
            video=self.video_input,
            frame_count=1,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Should extract exactly one frame
        self.assertEqual(extracted_count, 1)
        self.assertEqual(frames.shape[0], 1)
        self.assertEqual(frames.shape, (1, self.video_info['height'], self.video_info['width'], 3))
        
        # Verify it's a valid frame
        mean_value = torch.mean(frames[0]).item()
        self.assertGreater(mean_value, 0.01)
        self.assertLess(mean_value, 0.99)
        
        print(f"✅ Successfully extracted single frame with mean value {mean_value:.3f}")
    
    def test_frame_extraction_consistency(self):
        """Test that repeated extractions produce identical results"""
        # Extract same configuration twice
        frames1, _, count1 = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=3, skip_start_frames=1, skip_end_frames=1
        )
        
        frames2, _, count2 = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=3, skip_start_frames=1, skip_end_frames=1
        )
        
        # Results should be identical
        self.assertEqual(count1, count2)
        self.assertEqual(frames1.shape, frames2.shape)
        
        # Frames should be very similar (allowing for minor floating point differences)
        max_diff = torch.max(torch.abs(frames1 - frames2)).item()
        self.assertLess(max_diff, 1e-6, "Repeated extractions should produce identical results")
        
        print(f"✅ Repeated extractions are consistent (max diff: {max_diff:.8f})")
    
    def test_performance_metrics(self):
        """Test extraction performance and provide metrics"""
        import time
        
        # Test with different frame counts
        test_cases = [1, 5, 10, self.video_info['total_frames']]
        
        for frame_count in test_cases:
            if frame_count > self.video_info['total_frames']:
                continue
                
            start_time = time.time()
            
            frames, total_frames, extracted_count = self.simulate_comfyui_execution(
                self.node, "extract_frames", video=self.video_input,
                frame_count=frame_count, skip_start_frames=0, skip_end_frames=0
            )
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            # Calculate metrics
            frames_per_second = extracted_count / elapsed if elapsed > 0 else float('inf')
            memory_mb = frames.element_size() * frames.nelement() / (1024 * 1024)
            
            print(f"Performance - {extracted_count} frames: {elapsed:.3f}s ({frames_per_second:.1f} fps), {memory_mb:.1f}MB")
            
            # Reasonable performance expectations
            self.assertLess(elapsed, 5.0, f"Extraction of {frame_count} frames took too long")
            self.assertEqual(extracted_count, frame_count)
        
        print(f"✅ Performance metrics within acceptable ranges")


class TestVideoFrameExtractorErrorHandling(unittest.TestCase, MockComfyUINode):
    """Integration tests for error handling with real execution"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = VideoFrameExtractorNode()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_invalid_skip_parameters_real_execution(self):
        """Test error handling with invalid skip parameters using real video"""
        test_video_path = Path(__file__).parent.parent / "examples" / "ship.mp4"
        
        if not test_video_path.exists():
            self.skipTest(f"Test video not found: {test_video_path}")
        
        video_input = MockVideoInputFromFile(test_video_path)
        video_info = TestVideoFrameExtractorIntegration._get_video_info(test_video_path)
        
        # Test skipping more frames than available
        with self.assertRaises(ValueError) as context:
            self.simulate_comfyui_execution(
                self.node, "extract_frames", video=video_input,
                frame_count=5,
                skip_start_frames=video_info['total_frames']//2 + 1,
                skip_end_frames=video_info['total_frames']//2 + 1
            )
        
        self.assertIn("No frames remaining", str(context.exception))
        print(f"✅ Correctly caught error for invalid skip parameters")
    
    def test_corrupted_video_simulation(self):
        """Test handling of corrupted video data"""
        # Create a mock video input with invalid data
        mock_video = Mock()
        mock_components = Mock()
        
        # Simulate corrupted data - wrong tensor dimensions
        mock_components.images = torch.rand(2, 2)  # Invalid 2D tensor instead of 4D
        mock_video.get_components.return_value = mock_components
        
        with self.assertRaises(ValueError) as context:
            self.simulate_comfyui_execution(
                self.node, "extract_frames", video=mock_video,
                frame_count=5, skip_start_frames=0, skip_end_frames=0
            )
        
        self.assertIn("Expected 3D or 4D tensor", str(context.exception))
        print(f"✅ Correctly caught error for corrupted video data")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)