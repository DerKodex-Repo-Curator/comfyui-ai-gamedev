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
from tests.test_frame_extractor_integration import MockVideoInputFromFile


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
                
                # QUANTITATIVE VALIDATION
                # Verify extracted frame count matches requested
                self.assertEqual(extracted_count, count, f"Should extract exactly {count} frames")
                self.assertEqual(frames.shape[0], count, f"Tensor should have {count} frames in batch dimension")
                
                # Verify tensor format is correct ComfyUI format
                self.assertEqual(len(frames.shape), 4, "Should be 4D tensor (batch, height, width, channels)")
                self.assertEqual(frames.shape[1:], (640, 640, 3), "Frames should be 640x640 RGB")
                self.assertEqual(frames.dtype, torch.float32, "Should be float32 tensor")
                self.assertTrue(torch.all(frames >= 0.0), "All values should be >= 0.0")
                self.assertTrue(torch.all(frames <= 1.0), "All values should be <= 1.0")
                
                # Verify files were created
                self.assertEqual(len(saved_files), count)
                for filepath in saved_files:
                    self.assertTrue(filepath.exists())
                    # Verify file has reasonable size (not empty or corrupted)
                    self.assertGreater(filepath.stat().st_size, 1000)
                    
                    # Verify saved image can be loaded and has correct properties
                    with Image.open(filepath) as img:
                        self.assertEqual(img.size, (640, 640), f"Saved image should be 640x640: {filepath}")
                        self.assertEqual(img.mode, 'RGB', f"Saved image should be RGB: {filepath}")
                
                # Verify frame variance (frames should be different from each other)
                if count > 1:
                    frame_variances = []
                    for i in range(count - 1):
                        frame_diff = torch.abs(frames[i] - frames[i + 1])
                        variance = torch.mean(frame_diff).item()
                        frame_variances.append(variance)
                    
                    avg_variance = sum(frame_variances) / len(frame_variances)
                    self.assertGreater(avg_variance, 0.001, "Frames should be visually different from each other")
                
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
        
        # QUANTITATIVE VALIDATION
        # Verify both sets have the same count
        self.assertEqual(count_no_skip, count_with_skip, "Both extractions should yield same frame count")
        self.assertEqual(count_no_skip, 8, "Should extract exactly 8 frames")
        self.assertEqual(len(saved_no_skip), len(saved_with_skip), "Should save same number of files")
        
        # Verify tensor formats
        for frames, name in [(frames_no_skip, "no_skip"), (frames_with_skip, "with_skip")]:
            self.assertEqual(frames.shape, (8, 640, 640, 3), f"{name} should have correct shape")
            self.assertEqual(frames.dtype, torch.float32, f"{name} should be float32")
            self.assertTrue(torch.all(frames >= 0.0) and torch.all(frames <= 1.0), 
                           f"{name} values should be in [0,1] range")
        
        # Verify the extracted frames are actually different between skip/no-skip
        # (they should be, since skipping changes which frames are selected)
        frames_diff = torch.abs(frames_no_skip - frames_with_skip)
        avg_difference = torch.mean(frames_diff).item()
        self.assertGreater(avg_difference, 0.001, 
                          "Skip vs no-skip should produce different frame selections")
        
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
        
        # QUANTITATIVE VALIDATION
        # Verify frame count and tensor format
        self.assertEqual(extracted_count, 16, "Should extract exactly 16 frames")
        self.assertEqual(frames.shape, (16, 640, 640, 3), "Should have correct tensor shape")
        self.assertEqual(frames.dtype, torch.float32, "Should be float32 tensor")
        self.assertTrue(torch.all(frames >= 0.0) and torch.all(frames <= 1.0), 
                       "Values should be in [0,1] range")
        
        # Verify files were saved correctly
        self.assertEqual(len(saved_files), 16, "Should save 16 image files")
        for filepath in saved_files:
            self.assertTrue(filepath.exists(), f"File should exist: {filepath}")
            self.assertGreater(filepath.stat().st_size, 1000, f"File should not be empty: {filepath}")
        
        # Verify sequence has smooth progression (adjacent frames should be similar but not identical)
        frame_similarities = []
        for i in range(15):  # Compare each frame with the next
            frame_diff = torch.abs(frames[i] - frames[i + 1])
            similarity = 1.0 - torch.mean(frame_diff).item()  # Higher = more similar
            frame_similarities.append(similarity)
        
        avg_similarity = sum(frame_similarities) / len(frame_similarities)
        # Adjacent frames should be quite similar (smooth motion) but not identical
        self.assertGreater(avg_similarity, 0.8, "Adjacent frames should be similar (smooth motion)")
        self.assertLess(avg_similarity, 0.99, "Adjacent frames should not be identical")
        
        print(f"✅ Saved {len(saved_files)} frames for sequence continuity check")
        print(f"   Location: {saved_files[0].parent}")
        print(f"   Average frame similarity: {avg_similarity:.3f}")
    
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
                
                # QUANTITATIVE VALIDATION
                expected_count = params["frame_count"]
                self.assertEqual(extracted_count, expected_count, f"{case_name} should extract {expected_count} frames")
                self.assertEqual(len(saved_files), extracted_count, f"{case_name} should save {extracted_count} files")
                self.assertEqual(frames.shape[0], extracted_count, f"{case_name} tensor should have {extracted_count} frames")
                
                # Verify tensor format
                self.assertEqual(frames.shape[1:], (640, 640, 3), f"{case_name} should have correct frame dimensions")
                self.assertEqual(frames.dtype, torch.float32, f"{case_name} should be float32 tensor")
                self.assertTrue(torch.all(frames >= 0.0) and torch.all(frames <= 1.0), 
                               f"{case_name} values should be in [0,1] range")
                
                # Verify saved files
                for filepath in saved_files:
                    self.assertTrue(filepath.exists(), f"{case_name} file should exist: {filepath}")
                    self.assertGreater(filepath.stat().st_size, 1000, f"{case_name} file should not be empty: {filepath}")
                    
                    # Verify saved image properties
                    with Image.open(filepath) as img:
                        self.assertEqual(img.size, (640, 640), f"{case_name} saved image should be 640x640: {filepath}")
                        self.assertEqual(img.mode, 'RGB', f"{case_name} saved image should be RGB: {filepath}")
                
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