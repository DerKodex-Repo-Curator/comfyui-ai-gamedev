"""
Visual verification test for VideoFrameExtractor that saves extracted frames to disk
This allows manual inspection of extracted frames to verify quality and distribution
"""

import unittest
import os
import sys
import tempfile
from pathlib import Path
import torch
import numpy as np
from PIL import Image
import cv2

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.frame_extractor.frame_extractor_node import VideoFrameExtractorNode
from tests.comfyui_mock import ComfyUIMockContext, MockComfyUINode
from tests.integration_test_frame_extractor import MockVideoInputFromFile


class TestVideoFrameExtractorVisualVerification(unittest.TestCase, MockComfyUINode):
    """Visual verification tests that save extracted frames"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        cls.test_video_path = Path(__file__).parent.parent / "examples" / "ship.mp4"
        
        # Skip if video doesn't exist
        if not cls.test_video_path.exists():
            raise unittest.SkipTest(f"Test video not found: {cls.test_video_path}")
        
        # Create output directory for visual verification
        cls.output_dir = Path(__file__).parent.parent / "test_output" / "frame_extraction_visual"
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Visual verification frames will be saved to: {cls.output_dir}")
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = VideoFrameExtractorNode()
        self.video_input = MockVideoInputFromFile(self.test_video_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def _save_frames_to_disk(self, frames: torch.Tensor, test_name: str, frame_info: str = ""):
        """Save extracted frames to disk for visual verification"""
        test_output_dir = self.output_dir / test_name
        test_output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        for i, frame in enumerate(frames):
            # Convert from tensor to numpy (H, W, C) in [0, 1] range
            frame_np = frame.cpu().numpy()
            
            # Convert to uint8 [0, 255] range
            frame_uint8 = (frame_np * 255).astype(np.uint8)
            
            # Convert to PIL Image
            pil_image = Image.fromarray(frame_uint8, mode='RGB')
            
            # Save with descriptive filename
            filename = f"frame_{i:03d}_{frame_info}.png" if frame_info else f"frame_{i:03d}.png"
            filepath = test_output_dir / filename
            pil_image.save(filepath)
            saved_files.append(filepath)
        
        return saved_files
    
    def test_extract_evenly_distributed_frames_visual(self):
        """Extract evenly distributed frames and save for visual inspection"""
        frame_counts = [5, 10, 20]
        
        for count in frame_counts:
            with self.subTest(frame_count=count):
                frames, total_frames, extracted_count = self.simulate_comfyui_execution(
                    self.node, "extract_frames", video=self.video_input,
                    frame_count=count, skip_start_frames=0, skip_end_frames=0
                )
                
                # Save frames to disk
                saved_files = self._save_frames_to_disk(
                    frames, 
                    f"evenly_distributed_{count}frames",
                    f"of_{total_frames}total"
                )
                
                # Verify files were created
                self.assertEqual(len(saved_files), count)
                for filepath in saved_files:
                    self.assertTrue(filepath.exists())
                    # Verify file has reasonable size (not empty or corrupted)
                    self.assertGreater(filepath.stat().st_size, 1000)
                
                print(f"✅ Saved {count} evenly distributed frames to {saved_files[0].parent}")
    
    def test_skip_frames_visual_comparison(self):
        """Compare extraction with and without skipping frames"""
        # Extract without skipping
        frames_no_skip, _, count_no_skip = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=8, skip_start_frames=0, skip_end_frames=0
        )
        
        # Extract with skipping
        frames_with_skip, _, count_with_skip = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=8, skip_start_frames=5, skip_end_frames=5
        )
        
        # Save both sets for comparison
        saved_no_skip = self._save_frames_to_disk(
            frames_no_skip, "skip_comparison", "no_skip"
        )
        saved_with_skip = self._save_frames_to_disk(
            frames_with_skip, "skip_comparison", "skip_5start_5end"
        )
        
        # Verify both sets have the same count
        self.assertEqual(count_no_skip, count_with_skip)
        self.assertEqual(len(saved_no_skip), len(saved_with_skip))
        
        print(f"✅ Saved skip comparison frames:")
        print(f"   No skip: {saved_no_skip[0].parent}")
        print(f"   With skip: {saved_with_skip[0].parent}")
    
    def test_frame_sequence_continuity_visual(self):
        """Extract frames to verify sequence continuity"""
        # Extract many frames to see motion continuity
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=16, skip_start_frames=0, skip_end_frames=0
        )
        
        # Save frames with frame numbers to check sequence
        saved_files = []
        for i, frame in enumerate(frames):
            frame_np = (frame.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(frame_np, mode='RGB')
            
            # Calculate approximate source frame index
            step = (total_frames - 1) / (extracted_count - 1) if extracted_count > 1 else 0
            source_frame_idx = int(i * step)
            
            filename = f"frame_{i:02d}_from_source_{source_frame_idx:02d}.png"
            filepath = self.output_dir / "sequence_continuity" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            pil_image.save(filepath)
            saved_files.append(filepath)
        
        print(f"✅ Saved {len(saved_files)} frames for sequence continuity check")
        print(f"   Location: {saved_files[0].parent}")
    
    def test_resolution_verification_visual(self):
        """Verify extracted frames maintain correct resolution"""
        # Get original video info
        cap = cv2.VideoCapture(str(self.test_video_path))
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        
        # Extract a few frames
        frames, _, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames", video=self.video_input,
            frame_count=3, skip_start_frames=0, skip_end_frames=0
        )
        
        # Verify and save frames with resolution info
        for i, frame in enumerate(frames):
            # Check tensor dimensions
            tensor_height, tensor_width, channels = frame.shape
            self.assertEqual(tensor_height, original_height)
            self.assertEqual(tensor_width, original_width)
            self.assertEqual(channels, 3)
            
            # Save frame with resolution info in filename
            frame_np = (frame.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(frame_np, mode='RGB')
            
            filename = f"frame_{i}_resolution_{tensor_width}x{tensor_height}.png"
            filepath = self.output_dir / "resolution_verification" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            pil_image.save(filepath)
            
            # Double-check saved image resolution
            saved_image = Image.open(filepath)
            self.assertEqual(saved_image.size, (tensor_width, tensor_height))
        
        print(f"✅ Verified resolution {original_width}x{original_height} maintained in extracted frames")
        print(f"   Saved to: {filepath.parent}")
    
    def test_edge_cases_visual(self):
        """Test edge cases and save results"""
        edge_cases = [
            ("first_frame_only", {"frame_count": 1, "skip_start_frames": 0, "skip_end_frames": 0}),
            ("last_frame_only", {"frame_count": 1, "skip_start_frames": 80, "skip_end_frames": 0}),
            ("middle_frames", {"frame_count": 3, "skip_start_frames": 39, "skip_end_frames": 39}),
        ]
        
        for case_name, params in edge_cases:
            with self.subTest(case=case_name):
                frames, total_frames, extracted_count = self.simulate_comfyui_execution(
                    self.node, "extract_frames", video=self.video_input, **params
                )
                
                saved_files = self._save_frames_to_disk(
                    frames, "edge_cases", case_name
                )
                
                self.assertEqual(len(saved_files), extracted_count)
                
                print(f"✅ Edge case '{case_name}': extracted {extracted_count} frames")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up and provide summary"""
        if hasattr(cls, 'output_dir') and cls.output_dir.exists():
            # Count total files created
            total_files = sum(1 for _ in cls.output_dir.rglob("*.png"))
            print(f"\n🎯 Visual Verification Summary:")
            print(f"   Total frames saved: {total_files}")
            print(f"   Output directory: {cls.output_dir}")
            print(f"   Inspect frames manually to verify:")
            print(f"   - Frame quality and clarity")
            print(f"   - Even distribution across video timeline") 
            print(f"   - Correct resolutions maintained")
            print(f"   - Sequence continuity")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)