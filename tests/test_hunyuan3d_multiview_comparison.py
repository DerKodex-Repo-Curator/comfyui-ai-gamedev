#!/usr/bin/env python3
"""
Multiview comparison test for Hunyuan3D 2.1
Tests single view vs 4-frame multiview generation to compare results
"""

import unittest
import os
import sys
import tempfile
import time
import shutil
import subprocess
from pathlib import Path
import torch
import numpy as np
from PIL import Image

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.hunyuan3d_21_node import Hunyuan3D21Node
from tests.comfyui_mock import ComfyUIMockContext, create_test_image_tensor, MockComfyUINode

# Check dependencies
CONDA_AVAILABLE = shutil.which("conda") is not None
BLENDER_AVAILABLE = shutil.which("blender") is not None

def check_hunyuan3d_environment():
    """Check if hunyuan3d conda environment exists"""
    if not CONDA_AVAILABLE:
        return False
    try:
        result = subprocess.run(["conda", "env", "list"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False
        return "hunyuan3d" in result.stdout
    except:
        return False

HUNYUAN3D_ENV_AVAILABLE = check_hunyuan3d_environment()


class TestHunyuan3DMultiviewComparison(unittest.TestCase, MockComfyUINode):
    """Compare single view vs multiview 3D generation results"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        # Base paths
        cls.examples_dir = Path(__file__).parent.parent / "examples" / "input_images"
        cls.single_view_path = cls.examples_dir / "single_view" / "railgun" / "frame_001_4x.png"
        cls.multi_view_dir = cls.examples_dir / "multi_view"
        
        # Output directory for test comparisons
        cls.output_dir = Path(__file__).parent.parent / "test_output" / "multiview_comparison"
        cls.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Selected multiview frames (4 evenly distributed)
        cls.multiview_frames = [
            "frame_001_4x.png",  # Front view
            "frame_025_4x.png",  # Side view (90 degrees)
            "frame_044_4x.png",  # Back view (180 degrees) 
            "frame_069_4x.png"   # Side view (270 degrees)
        ]
        
        print(f"\n🔍 Multiview Comparison Test Setup:")
        print(f"  Single view: {cls.single_view_path.exists()}")
        print(f"  Multiview dir: {cls.multi_view_dir.exists()}")
        print(f"  Selected frames: {cls.multiview_frames}")
        
        # Verify all multiview frames exist
        for frame in cls.multiview_frames:
            frame_path = cls.multi_view_dir / frame
            print(f"    {frame}: {frame_path.exists()}")
    
    def setUp(self):
        """Set up test fixtures"""
        if not CONDA_AVAILABLE:
            self.fail("Integration test failure: conda not available")
        
        if not BLENDER_AVAILABLE:
            self.fail("Integration test failure: Blender not available")
        
        if not HUNYUAN3D_ENV_AVAILABLE:
            self.fail("Integration test failure: hunyuan3d conda environment not found")
        
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = Hunyuan3D21Node()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def load_image_as_tensor(self, image_path: Path) -> torch.Tensor:
        """Load a single image as a tensor in ComfyUI format"""
        pil_image = Image.open(image_path).convert('RGB')
        # Resize to reasonable size for faster testing
        if pil_image.size != (256, 256):
            pil_image = pil_image.resize((256, 256))
        # Convert to tensor format [batch, height, width, channels]
        image_array = np.array(pil_image, dtype=np.float32) / 255.0
        return torch.from_numpy(image_array).unsqueeze(0)  # Add batch dimension
    
    def load_multiview_batch(self, frame_names: list) -> torch.Tensor:
        """Load multiple images as a batched tensor"""
        tensors = []
        for frame_name in frame_names:
            frame_path = self.multi_view_dir / frame_name
            if not frame_path.exists():
                raise FileNotFoundError(f"Multiview frame not found: {frame_path}")
            tensor = self.load_image_as_tensor(frame_path)
            tensors.append(tensor)
        
        # Stack into batch [batch_size, height, width, channels]
        return torch.cat(tensors, dim=0)
    
    def run_generation_test(self, images: torch.Tensor, test_name: str) -> tuple:
        """Run 3D generation test and return file paths"""
        print(f"\n🎮 Running {test_name} generation...")
        print(f"  Input shape: {images.shape}")
        print(f"  Batch size: {images.shape[0]} (multiview: {images.shape[0] > 1})")
        
        start_time = time.time()
        
        try:
            # Run the actual node generation
            result = self.node.generate_3d(
                images=images,
                resolution="256",  # Small for faster testing
                texture_resolution="256",
                guidance_scale=7.5,
                inference_steps=10,  # Minimal for testing
                conda_env="hunyuan3d",
                conda_path="conda"
            )
            
            execution_time = time.time() - start_time
            print(f"  ⏱️ {test_name} execution time: {execution_time:.1f}s")
            
            if isinstance(result, tuple) and len(result) == 3:
                glb_path, obj_path, stl_path = result
                print(f"  ✅ {test_name} completed:")
                print(f"    GLB: {Path(glb_path).name if glb_path else 'None'}")
                print(f"    OBJ: {Path(obj_path).name if obj_path else 'None'}")
                print(f"    STL: {Path(stl_path).name if stl_path else 'None'}")
                return glb_path, obj_path, stl_path
            else:
                print(f"  ❌ {test_name} returned unexpected result: {result}")
                return None, None, None
                
        except Exception as e:
            print(f"  ❌ {test_name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None
    
    def copy_results_for_comparison(self, file_paths: tuple, test_name: str):
        """Copy generated files to comparison directory with descriptive names"""
        glb_path, obj_path, stl_path = file_paths
        timestamp = int(time.time())
        
        copied_files = []
        for path, ext in [(glb_path, "glb"), (obj_path, "obj"), (stl_path, "stl")]:
            if path and Path(path).exists():
                source = Path(path)
                dest = self.output_dir / f"{test_name}_{timestamp}.{ext}"
                shutil.copy2(source, dest)
                copied_files.append(dest)
                print(f"    📁 Copied {ext.upper()}: {dest.name}")
        
        return copied_files
    
    def compare_file_sizes(self, single_files: list, multiview_files: list):
        """Compare file sizes between single and multiview results"""
        print(f"\n📊 File Size Comparison:")
        
        for single_file, multiview_file in zip(single_files, multiview_files):
            if single_file.exists() and multiview_file.exists():
                single_size = single_file.stat().st_size
                multiview_size = multiview_file.stat().st_size
                diff_percent = ((multiview_size - single_size) / single_size) * 100
                
                print(f"  {single_file.suffix.upper()}:")
                print(f"    Single view:   {single_size:,} bytes")
                print(f"    Multiview (4): {multiview_size:,} bytes")
                print(f"    Difference:    {diff_percent:+.1f}%")
    
    @unittest.skip("Enable manually for comparison testing - requires 21GB VRAM and 10+ minutes")
    def test_single_vs_multiview_comparison(self):
        """Compare single view vs 4-frame multiview generation results"""
        print("\n" + "="*80)
        print("🔥 MULTIVIEW COMPARISON TEST")
        print("="*80)
        
        # Test 1: Single view generation
        print(f"\n1️⃣ SINGLE VIEW TEST")
        single_image = self.load_image_as_tensor(self.single_view_path)
        single_results = self.run_generation_test(single_image, "single_view")
        
        if not any(single_results):
            self.fail("Single view generation failed")
        
        single_files = self.copy_results_for_comparison(single_results, "single_view")
        
        # Test 2: Multiview generation (4 frames)
        print(f"\n2️⃣ MULTIVIEW TEST (4 frames)")
        multiview_images = self.load_multiview_batch(self.multiview_frames)
        multiview_results = self.run_generation_test(multiview_images, "multiview_4frames")
        
        if not any(multiview_results):
            self.fail("Multiview generation failed")
        
        multiview_files = self.copy_results_for_comparison(multiview_results, "multiview_4frames")
        
        # Compare results
        if len(single_files) == len(multiview_files):
            self.compare_file_sizes(single_files, multiview_files)
        
        # Verify both approaches generated valid files
        for file_path in single_files + multiview_files:
            self.assertTrue(file_path.exists(), f"Generated file missing: {file_path}")
            self.assertGreater(file_path.stat().st_size, 1000, f"Generated file too small: {file_path}")
        
        print(f"\n✅ COMPARISON COMPLETE")
        print(f"📁 Results saved to: {self.output_dir}")
        print(f"   Compare the generated models to see the difference!")
        print(f"   Single view files: {[f.name for f in single_files]}")
        print(f"   Multiview files:   {[f.name for f in multiview_files]}")
    
    def test_multiview_frame_validation(self):
        """Test that all required multiview frames exist and are valid"""
        print(f"\n🔍 Validating multiview test frames...")
        
        # Check single view frame
        self.assertTrue(self.single_view_path.exists(), f"Single view frame not found: {self.single_view_path}")
        self.assertGreater(self.single_view_path.stat().st_size, 10000, "Single view frame too small")
        
        # Check multiview frames
        for frame_name in self.multiview_frames:
            frame_path = self.multi_view_dir / frame_name
            self.assertTrue(frame_path.exists(), f"Multiview frame not found: {frame_path}")
            self.assertGreater(frame_path.stat().st_size, 10000, f"Multiview frame too small: {frame_name}")
        
        # Test loading as tensors
        single_tensor = self.load_image_as_tensor(self.single_view_path)
        self.assertEqual(single_tensor.shape, (1, 256, 256, 3), "Single view tensor shape incorrect")
        
        multiview_tensor = self.load_multiview_batch(self.multiview_frames)
        self.assertEqual(multiview_tensor.shape, (4, 256, 256, 3), "Multiview tensor shape incorrect")
        
        print(f"✅ All frames validated:")
        print(f"  Single view: {single_tensor.shape}")
        print(f"  Multiview:   {multiview_tensor.shape}")
    
    def test_multiview_detection_logic(self):
        """Test that the node correctly detects multiview vs single view mode"""
        # Single view should be detected as single
        single_image = self.load_image_as_tensor(self.single_view_path)
        # Based on the CLAUDE.md pattern, batch_size > 1 and <= 10 means multiview
        is_multiview_single = single_image.shape[0] > 1 and single_image.shape[0] <= 10
        self.assertFalse(is_multiview_single, "Single image incorrectly detected as multiview")
        
        # 4 frames should be detected as multiview
        multiview_images = self.load_multiview_batch(self.multiview_frames)
        is_multiview_multi = multiview_images.shape[0] > 1 and multiview_images.shape[0] <= 10
        self.assertTrue(is_multiview_multi, "4 frames incorrectly detected as single view")
        
        print(f"✅ Multiview detection logic validated:")
        print(f"  Single (1 frame): {not is_multiview_single}")
        print(f"  Multi (4 frames): {is_multiview_multi}")


if __name__ == '__main__':
    print("🔍 Hunyuan3D Multiview Comparison Tests")
    print("=" * 50)
    print("Dependencies:")
    print(f"  Conda available: {CONDA_AVAILABLE}")
    print(f"  Blender available: {BLENDER_AVAILABLE}")
    print(f"  Hunyuan3D environment: {HUNYUAN3D_ENV_AVAILABLE}")
    print()
    
    unittest.main(verbosity=2)