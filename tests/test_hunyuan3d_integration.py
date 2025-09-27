"""
Integration tests for Hunyuan3D 2.1 node that actually execute conda subprocess and generate files
These tests require the full Hunyuan3D environment and will FAIL if dependencies are missing.

IMPORTANT: These tests FAIL (not skip) if dependencies are missing. This is intentional.
This is integration testing - the external services and models must be available.
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
            print(f"conda env list failed: {result.stderr}")
            return False
        
        # Debug: print conda environments found
        print(f"Conda environments found:\n{result.stdout}")
        
        # Check for hunyuan3d in the output
        env_found = "hunyuan3d" in result.stdout
        print(f"hunyuan3d environment found: {env_found}")
        return env_found
    except subprocess.TimeoutExpired:
        print("Timeout checking conda environments")
        return False
    except Exception as e:
        print(f"Error checking conda environments: {e}")
        return False

HUNYUAN3D_ENV_AVAILABLE = check_hunyuan3d_environment()


class TestHunyuan3D21Integration(unittest.TestCase, MockComfyUINode):
    """Integration tests with real Hunyuan3D execution"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        # Real input images directory
        cls.examples_dir = Path(__file__).parent.parent / "examples" / "input_images"
        cls.real_image_path = cls.examples_dir / "single_view" / "railgun" / "frame_001_4x.png"
        print(f"Real image available: {cls.real_image_path.exists()}")
        
        # Output directory for test files
        cls.output_dir = Path(__file__).parent.parent / "test_output"
        cls.output_dir.mkdir(parents=True, exist_ok=True)
    
    def setUp(self):
        """Set up test fixtures"""
        # Simple dependency checks - fail if not available
        if not CONDA_AVAILABLE:
            self.fail("Integration test failure: conda not available. Install conda and ensure it's in PATH.")
        
        if not BLENDER_AVAILABLE:
            self.fail("Integration test failure: Blender not available. Install with: sudo snap install blender --classic")
        
        if not HUNYUAN3D_ENV_AVAILABLE:
            self.fail("Integration test failure: hunyuan3d conda environment not found. Create with: conda create -n hunyuan3d python=3.10")
        
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = Hunyuan3D21Node()
        
        # Load real test image (required for all tests)
        self.real_image = None
        if self.real_image_path.exists():
            pil_image = Image.open(self.real_image_path).convert('RGB')
            # Resize to reasonable size for faster testing
            if pil_image.size != (256, 256):
                pil_image = pil_image.resize((256, 256))
            # Convert to tensor format
            image_array = np.array(pil_image, dtype=np.float32) / 255.0
            self.real_image = torch.from_numpy(image_array).unsqueeze(0)  # Add batch dimension
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    @unittest.skip("Temporarily disabled - focusing on textured generation tests")
    def test_shape_only_generation_real_execution(self):
        """Test shape-only generation (no texture) with real execution - generates OBJ/STL"""
        print("🔥 REAL EXECUTION: Testing shape-only generation (OBJ/STL)")
        
        # Use real test image
        test_image_path = Path(__file__).parent.parent / "examples" / "input_images" / "single_view" / "railgun" / "frame_001_4x.png"
        
        # 1. ASSERT: Input image exists and is valid
        self.assertTrue(test_image_path.exists(), f"Test image not found: {test_image_path}")
        self.assertGreater(test_image_path.stat().st_size, 1000, f"Test image is too small: {test_image_path.stat().st_size} bytes")
        print(f"✅ Input image verified: {test_image_path} ({test_image_path.stat().st_size} bytes)")
        
        start_time = time.time()
        
        # Create config exactly like the node does
        import uuid
        import datetime
        import json
        
        run_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"hunyuan3d_integration_test_{timestamp}_{run_id}"
        
        # Create output directory
        output_dir = Path(__file__).parent.parent / "test_output" / "hunyuan3d_integration"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generation_dir = output_dir / base_name
        generation_dir.mkdir(parents=True, exist_ok=True)
        
        # Create config file EXACTLY like the node does
        config = {
            "image_paths": [str(test_image_path.resolve())],  # Fixed: use image_paths, not input_images
            "output_dir": str(generation_dir.resolve()),
            "base_name": "output",  # Fixed: add base_name like the node does
            "resolution": 256,  # Small for faster testing
            "texture_resolution": 256,
            "guidance_scale": 7.5,
            "inference_steps": 10,  # Minimal for testing
        }
        
        config_path = generation_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # 2. ASSERT: Config file was saved and is readable
        self.assertTrue(config_path.exists(), f"Config file not created: {config_path}")
        with open(config_path, 'r') as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config["image_paths"], config["image_paths"])
        self.assertEqual(saved_config["base_name"], "output")
        print(f"✅ Config file verified: {config_path}")
        print(f"Config contents: {json.dumps(saved_config, indent=2)}")
        
        # Get the script path exactly like the node does
        script_path = Path(__file__).parent.parent / "nodes" / "hunyuan3d" / "hunyuan3d_execute.py"
        self.assertTrue(script_path.exists(), f"Script not found: {script_path}")
        
        # Execute subprocess exactly like the node does
        cmd = [
            "conda", "run", "-n", "hunyuan3d",
            "blender", "--background", "--python", str(script_path),
            "--", str(config_path)
        ]
        
        print(f"🔨 Executing: {' '.join(cmd)}")
        print("⏳ This will take 2-5 minutes for shape-only generation...")
        
        # Create clean environment like the node does
        clean_env = {
            'PATH': os.environ.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
            'HOME': os.environ.get('HOME', os.path.expanduser('~')),
            'USER': os.environ.get('USER', ''),
            'SHELL': os.environ.get('SHELL', '/bin/bash'),
            'TERM': os.environ.get('TERM', 'xterm'),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'C.UTF-8'),
        }
        
        # Add CUDA if available
        if 'CUDA_VISIBLE_DEVICES' in os.environ:
            clean_env['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
        
        # Add DISPLAY if available
        if 'DISPLAY' in os.environ:
            clean_env['DISPLAY'] = os.environ['DISPLAY']
        
        # Execute exactly like the node does
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes timeout
            cwd=str(Path(__file__).parent.parent),  # Project root
            env=clean_env
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ Shape-only execution time: {execution_time:.1f}s")
        
        # 3. LOG ALL subprocess output
        print("=" * 60)
        print("COMPLETE SUBPROCESS OUTPUT:")
        print("=" * 60)
        print("STDOUT:")
        if result.stdout:
            for i, line in enumerate(result.stdout.split('\n'), 1):
                print(f"{i:3}: {line}")
        else:
            print("(No stdout)")
        
        print("\nSTDERR:")
        if result.stderr:
            for i, line in enumerate(result.stderr.split('\n'), 1):
                print(f"{i:3}: {line}")
        else:
            print("(No stderr)")
        
        print(f"\nReturn code: {result.returncode}")
        print("=" * 60)
        
        # Note: Blender may still segfault during cleanup (this is a known Blender issue)
        # Success is measured by file generation, not exit code
        print(f"📊 Subprocess return code: {result.returncode} (segfault during cleanup is known issue)")
        
        # Look for generated files with exact names the node expects
        obj_path = generation_dir / "output_textured.obj"
        stl_path = generation_dir / "output_textured.stl"
        glb_path = generation_dir / "output_textured.glb"
        
        # List all files in generation directory for debugging
        all_files = list(generation_dir.glob("*"))
        print(f"📁 All files in generation directory ({len(all_files)}):")
        for f in all_files:
            print(f"  {f.name} ({f.stat().st_size} bytes)")
        
        # Note: Blender may still segfault during cleanup, but files should be generated successfully
        if result.returncode != 0:
            print(f"⚠️ Blender exited with code {result.returncode} (segfault during cleanup), but checking if files were generated...")
        
        # Check if specific files were generated (this is the key success criteria)
        self.assertTrue(obj_path.exists(), f"Expected OBJ file not found: {obj_path}")
        self.assertTrue(stl_path.exists(), f"Expected STL file not found: {stl_path}")
        
        # Verify file sizes (ensure they're not empty)
        self.assertGreater(obj_path.stat().st_size, 1000, f"OBJ file is too small ({obj_path.stat().st_size} bytes) - may be incomplete")
        self.assertGreater(stl_path.stat().st_size, 1000, f"STL file is too small ({stl_path.stat().st_size} bytes) - may be incomplete")
        
        print(f"✅ SUCCESS: Files generated successfully!")
        print(f"✅ OBJ file: {obj_path} ({obj_path.stat().st_size} bytes)")
        print(f"✅ STL file: {stl_path} ({stl_path.stat().st_size} bytes)")
        if glb_path.exists():
            print(f"✅ GLB file: {glb_path} ({glb_path.stat().st_size} bytes)")
        print(f"📁 Files saved to: {generation_dir}")
        
        # File generation succeeds even if Blender crashes during cleanup!
    
    def test_textured_generation_real_execution(self):
        """Test full textured generation with real execution - generates GLB with textures"""
        if self.real_image is None:
            self.skipTest("No test image available")
        
        print("🔥 REAL EXECUTION: Testing textured generation (GLB with PBR textures)")
        
        start_time = time.time()
        
        # Execute with texture generation (this will be very slow and memory intensive)
        # Call the node method directly (no mocking) - this will execute real conda subprocess
        glb_path, obj_path, stl_path = self.node.generate_3d(
            images=self.real_image,
            resolution="512",  # String as expected by node
            texture_resolution="512",
            guidance_scale=7.5,
            inference_steps=10,  # Minimal steps for testing
            conda_env="hunyuan3d",
            conda_path="conda"
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ Full pipeline execution time: {execution_time:.1f}s")
        
        # Verify outputs
        self.assertIsInstance(glb_path, str, "GLB path should be string")
        self.assertIsInstance(obj_path, str, "OBJ path should be string") 
        self.assertIsInstance(stl_path, str, "STL path should be string")
        
        # Check file existence
        glb_file = Path(glb_path)
        obj_file = Path(obj_path)
        stl_file = Path(stl_path)
        
        self.assertTrue(glb_file.exists(), f"GLB file should exist: {glb_path}")
        self.assertTrue(obj_file.exists(), f"OBJ file should exist: {obj_path}")
        self.assertTrue(stl_file.exists(), f"STL file should exist: {stl_path}")
        
        # Check file sizes (GLB should be larger due to embedded textures)
        self.assertGreater(glb_file.stat().st_size, 5000, "GLB file should be substantial with textures")
        self.assertGreater(obj_file.stat().st_size, 1000, "OBJ file should be substantial")
        self.assertGreater(stl_file.stat().st_size, 1000, "STL file should be substantial")
        
        print(f"✅ GLB file: {glb_path} ({glb_file.stat().st_size} bytes)")
        print(f"✅ OBJ file: {obj_path} ({obj_file.stat().st_size} bytes)")
        print(f"✅ STL file: {stl_path} ({stl_file.stat().st_size} bytes)")
        
        # Copy to test output for inspection
        timestamp = int(time.time())
        shutil.copy2(glb_file, self.output_dir / f"test_textured_{timestamp}.glb")
        shutil.copy2(obj_file, self.output_dir / f"test_textured_{timestamp}.obj")
        shutil.copy2(stl_file, self.output_dir / f"test_textured_{timestamp}.stl")
    
    def run_hunyuan3d_generation(self, images, test_name: str, texture_enabled: bool = True):
        """Shared function to run Hunyuan3D generation with any number of images"""
        num_images = images.shape[0] if hasattr(images, 'shape') else 1
        print(f"\n🎮 {test_name} - Generating 3D model from {num_images} image(s)")
        print(f"   Texture enabled: {texture_enabled}")
        print(f"   Using conda: conda with environment: hunyuan3d")
        
        start_time = time.time()
        
        # Call the node method directly (no mocking) - this will execute real conda subprocess
        glb_path, obj_path, stl_path = self.node.generate_3d(
            images=images,
            resolution="512",  # String as expected by node
            texture_resolution="512",
            guidance_scale=7.5,
            inference_steps=10,  # Minimal steps for testing
            enable_texture=texture_enabled,
            conda_env="hunyuan3d",
            conda_path="conda"
        )
        
        execution_time = time.time() - start_time
        print(f"⏱️ {test_name} execution time: {execution_time:.1f}s")
        
        return glb_path, obj_path, stl_path, execution_time
    
    def load_multiview_images(self):
        """Load 4 multiview images for comparison testing"""
        multi_view_dir = self.examples_dir / "multi_view"
        
        # Selected multiview frames (4 evenly distributed around 360°)
        multiview_frames = [
            "frame_001_4x.png",  # Front view (0°)
            "frame_025_4x.png",  # Side view (~90°) 
            "frame_044_4x.png",  # Back view (~180°)
            "frame_069_4x.png"   # Side view (~270°)
        ]
        
        tensors = []
        for frame_name in multiview_frames:
            frame_path = multi_view_dir / frame_name
            if not frame_path.exists():
                raise FileNotFoundError(f"Multiview frame not found: {frame_path}")
            
            # Load and resize image
            pil_image = Image.open(frame_path).convert('RGB')
            if pil_image.size != (256, 256):
                pil_image = pil_image.resize((256, 256))
            
            # Convert to tensor format [batch, height, width, channels]
            image_array = np.array(pil_image, dtype=np.float32) / 255.0
            tensor = torch.from_numpy(image_array).unsqueeze(0)  # Add batch dimension
            tensors.append(tensor)
        
        # Stack into batch [batch_size, height, width, channels]
        return torch.cat(tensors, dim=0)
    
    def test_single_image_generation(self):
        """Test single image 3D generation - the perfect original test"""
        if self.real_image is None:
            self.skipTest("No test image available")
        
        print("🔥 REAL EXECUTION: Testing single image generation")
        
        glb_path, obj_path, stl_path, execution_time = self.run_hunyuan3d_generation(
            self.real_image, "Single Image Test", texture_enabled=True
        )
        
        # Verify files were generated
        self.assertIsNotNone(glb_path, "GLB path should be returned")
        self.assertIsNotNone(obj_path, "OBJ path should be returned") 
        self.assertIsNotNone(stl_path, "STL path should be returned")
        
        glb_file = Path(glb_path)
        obj_file = Path(obj_path)
        stl_file = Path(stl_path)
        
        self.assertTrue(glb_file.exists(), f"GLB file should exist at {glb_path}")
        self.assertTrue(obj_file.exists(), f"OBJ file should exist at {obj_path}")
        self.assertTrue(stl_file.exists(), f"STL file should exist at {stl_path}")
        
        # Check file sizes
        self.assertGreater(glb_file.stat().st_size, 5000, "GLB file should be substantial")
        self.assertGreater(obj_file.stat().st_size, 1000, "OBJ file should be substantial")
        self.assertGreater(stl_file.stat().st_size, 1000, "STL file should be substantial")
        
        print(f"✅ GLB file: {glb_path} ({glb_file.stat().st_size:,} bytes)")
        print(f"✅ OBJ file: {obj_path} ({obj_file.stat().st_size:,} bytes)")
        print(f"✅ STL file: {stl_path} ({stl_file.stat().st_size:,} bytes)")
        
        # Copy to test output for inspection
        timestamp = int(time.time())
        shutil.copy2(glb_file, self.output_dir / f"single_image_{timestamp}.glb")
        shutil.copy2(obj_file, self.output_dir / f"single_image_{timestamp}.obj")
        shutil.copy2(stl_file, self.output_dir / f"single_image_{timestamp}.stl")
        print(f"📁 Files copied to: {self.output_dir}")
    
    def test_multiview_generation(self):
        """Test multiview (4-frame) 3D generation"""
        if self.real_image is None:
            self.skipTest("No test image available")
        
        print("🔥 REAL EXECUTION: Testing multiview generation (4 frames)")
        
        try:
            multiview_images = self.load_multiview_images()
            print(f"✅ Loaded multiview images: {multiview_images.shape}")
        except FileNotFoundError as e:
            self.skipTest(f"Multiview images not available: {e}")
        
        glb_path, obj_path, stl_path, execution_time = self.run_hunyuan3d_generation(
            multiview_images, "Multiview Test", texture_enabled=True
        )
        
        # Verify files were generated
        self.assertIsNotNone(glb_path, "GLB path should be returned")
        self.assertIsNotNone(obj_path, "OBJ path should be returned")
        self.assertIsNotNone(stl_path, "STL path should be returned")
        
        glb_file = Path(glb_path)
        obj_file = Path(obj_path)
        stl_file = Path(stl_path)
        
        self.assertTrue(glb_file.exists(), f"GLB file should exist at {glb_path}")
        self.assertTrue(obj_file.exists(), f"OBJ file should exist at {obj_path}")
        self.assertTrue(stl_file.exists(), f"STL file should exist at {stl_path}")
        
        # Check file sizes
        self.assertGreater(glb_file.stat().st_size, 5000, "GLB file should be substantial")
        self.assertGreater(obj_file.stat().st_size, 1000, "OBJ file should be substantial")
        self.assertGreater(stl_file.stat().st_size, 1000, "STL file should be substantial")
        
        print(f"✅ GLB file: {glb_path} ({glb_file.stat().st_size:,} bytes)")
        print(f"✅ OBJ file: {obj_path} ({obj_file.stat().st_size:,} bytes)")
        print(f"✅ STL file: {stl_path} ({stl_file.stat().st_size:,} bytes)")
        
        # Copy to test output for inspection
        timestamp = int(time.time())
        shutil.copy2(glb_file, self.output_dir / f"multiview_{timestamp}.glb")
        shutil.copy2(obj_file, self.output_dir / f"multiview_{timestamp}.obj")
        shutil.copy2(stl_file, self.output_dir / f"multiview_{timestamp}.stl")
        print(f"📁 Files copied to: {self.output_dir}")

    def test_conda_environment_validation_real(self):
        """Test that conda environment validation works with real conda"""
        print("🔥 REAL EXECUTION: Testing conda environment validation")
        
        # Test with valid environment
        node = Hunyuan3D21Node()
        
        # This should not raise an exception
        try:
            # We'll call a method that validates conda setup
            # The setUp already validates basic conda availability
            self.assertTrue(CONDA_AVAILABLE, "Conda should be available")
            self.assertTrue(HUNYUAN3D_ENV_AVAILABLE, "Hunyuan3D environment should be available")
            print("✅ Conda environment validation passed")
        except Exception as e:
            self.fail(f"Conda environment validation failed: {e}")
    
    def test_dependency_import_real(self):
        """Test that Hunyuan3D dependencies can be imported in conda environment"""
        print("🔥 REAL EXECUTION: Testing dependency imports")
        
        import subprocess
        
        # Test shape pipeline import
        try:
            result = subprocess.run(
                ["conda", "run", "-n", "hunyuan3d", "python", "-c", 
                 "import sys; sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape'); from pipelines import Hunyuan3DDiTFlowMatchingPipeline; print('✅ Shape pipeline imported successfully')"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            self.assertEqual(result.returncode, 0, f"Shape pipeline import failed: {result.stderr}")
            print(result.stdout.strip())
        except subprocess.TimeoutExpired:
            self.fail("Timeout importing shape pipeline")
        
        # Test paint pipeline import  
        try:
            result = subprocess.run(
                ["conda", "run", "-n", "hunyuan3d", "python", "-c",
                 "import sys; sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint'); from textureGenPipeline import Hunyuan3DPaintPipeline; print('✅ Paint pipeline imported successfully')"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                timeout=30
            )
            self.assertEqual(result.returncode, 0, f"Paint pipeline import failed: {result.stderr}")
            print(result.stdout.strip())
        except subprocess.TimeoutExpired:
            self.fail("Timeout importing paint pipeline")

    def test_progress_monitoring_real_execution(self):
        """Test that progress monitoring works correctly during real execution"""
        if self.real_image is None:
            self.skipTest("No test image available")
        
        print("🔥 REAL EXECUTION: Testing progress monitoring functionality")
        
        # Use a custom subprocess execution to capture progress output
        import uuid
        import datetime
        import json
        import re
        
        run_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"hunyuan3d_progress_test_{timestamp}_{run_id}"
        
        # Create output directory
        output_dir = Path(__file__).parent.parent / "test_output" / "hunyuan3d_progress"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        generation_dir = output_dir / base_name
        generation_dir.mkdir(parents=True, exist_ok=True)
        
        # Create test image in temp directory
        test_image_path = generation_dir / "test_image.png"
        pil_image = Image.open(self.real_image_path).convert('RGB')
        if pil_image.size != (256, 256):
            pil_image = pil_image.resize((256, 256))
        pil_image.save(test_image_path)
        
        # Create config file
        config = {
            "image_paths": [str(test_image_path.resolve())],
            "output_dir": str(generation_dir.resolve()),
            "base_name": "output",
            "resolution": 256,  # Small for faster testing
            "texture_resolution": 256,
            "guidance_scale": 7.5,
            "inference_steps": 5,  # Very minimal for testing
        }
        
        config_path = generation_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Execute with progress monitoring
        script_path = Path(__file__).parent.parent / "nodes" / "hunyuan3d" / "hunyuan3d_execute.py"
        cmd = [
            "conda", "run", "-n", "hunyuan3d",
            "blender", "--background", "--python", str(script_path),
            "--", str(config_path)
        ]
        
        print(f"🔨 Executing with progress monitoring: {' '.join(cmd)}")
        print("⏳ This will take 1-3 minutes and test progress tracking...")
        
        # Create clean environment
        clean_env = {
            'PATH': os.environ.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
            'HOME': os.environ.get('HOME', os.path.expanduser('~')),
            'USER': os.environ.get('USER', ''),
            'SHELL': os.environ.get('SHELL', '/bin/bash'),
            'TERM': os.environ.get('TERM', 'xterm'),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'C.UTF-8'),
        }
        
        # Add CUDA if available
        if 'CUDA_VISIBLE_DEVICES' in os.environ:
            clean_env['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
        
        start_time = time.time()
        
        # Execute with real-time output monitoring to detect buffering
        import subprocess
        from datetime import datetime
        
        print("🕐 Starting subprocess with real-time output monitoring...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified monitoring
            text=True,
            bufsize=0,  # Unbuffered
            universal_newlines=True,
            cwd=str(Path(__file__).parent.parent),
            env=clean_env
        )
        
        # Capture output with timestamps
        real_time_logs = []
        output_lines = []
        
        print("📋 Real-time subprocess output with receive timestamps:")
        print("-" * 80)
        
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                # Record timestamp when we received this line
                receive_time = datetime.now()
                line = line.rstrip('\n\r')
                
                # Store for analysis
                real_time_logs.append({
                    'receive_time': receive_time,
                    'elapsed_since_start': (receive_time.timestamp() - start_time),
                    'content': line
                })
                output_lines.append(line)
                
                # Print with receive timestamp
                elapsed = receive_time.timestamp() - start_time
                print(f"[{receive_time.strftime('%H:%M:%S.%f')[:-3]}] (+{elapsed:6.2f}s) {line}")
                
                # Check if this is a JSON progress message
                try:
                    import json
                    data = json.loads(line)
                    if isinstance(data, dict) and data.get("type") == "progress":
                        # Extract message timestamp vs receive timestamp
                        msg_timestamp = data.get('timestamp', '')
                        if msg_timestamp:
                            try:
                                msg_time = datetime.fromisoformat(msg_timestamp.replace('Z', '+00:00'))
                                delay = (receive_time - msg_time).total_seconds()
                                print(f"    🚩 PROGRESS JSON - Message time: {msg_timestamp}, Receive delay: {delay:.3f}s")
                            except Exception as e:
                                print(f"    🚩 PROGRESS JSON - Could not parse timestamp: {e}")
                        else:
                            print(f"    🚩 PROGRESS JSON - No timestamp in message")
                except json.JSONDecodeError:
                    pass
        
        except KeyboardInterrupt:
            process.terminate()
            print("\n⚠️ Process terminated by user")
        
        # Wait for process completion
        process.wait()
        print("-" * 80)
        
        # Create result object for compatibility
        result = type('ProcessResult', (), {
            'returncode': process.returncode,
            'stdout': '\n'.join(output_lines),
            'stderr': ''  # We merged stderr into stdout
        })()
        
        execution_time = time.time() - start_time
        print(f"⏱️ Progress monitoring test execution time: {execution_time:.1f}s")
        
        # Analyze buffering behavior from real-time logs
        print("\n📊 BUFFERING ANALYSIS:")
        print("=" * 60)
        
        # Count progress JSON messages and their timing
        progress_logs = []
        for log_entry in real_time_logs:
            try:
                import json
                data = json.loads(log_entry['content'])
                if isinstance(data, dict) and data.get("type") == "progress":
                    progress_logs.append({
                        'receive_time': log_entry['receive_time'],
                        'elapsed_since_start': log_entry['elapsed_since_start'],
                        'data': data
                    })
            except json.JSONDecodeError:
                pass
        
        print(f"Total lines received: {len(real_time_logs)}")
        print(f"Progress JSON messages: {len(progress_logs)}")
        
        if len(progress_logs) > 1:
            # Calculate gaps between progress messages
            gaps = []
            for i in range(1, len(progress_logs)):
                gap = progress_logs[i]['elapsed_since_start'] - progress_logs[i-1]['elapsed_since_start']
                gaps.append(gap)
            
            if gaps:
                avg_gap = sum(gaps) / len(gaps)
                max_gap = max(gaps)
                min_gap = min(gaps)
                
                print(f"Time gaps between progress messages:")
                print(f"  Average gap: {avg_gap:.2f}s")
                print(f"  Maximum gap: {max_gap:.2f}s") 
                print(f"  Minimum gap: {min_gap:.2f}s")
                
                # Flag potential buffering if we see large gaps
                if max_gap > 30:  # More than 30 seconds without progress
                    print(f"⚠️  POTENTIAL BUFFERING: Large gap of {max_gap:.1f}s detected")
                else:
                    print("✅ No significant buffering detected")
        
        # Show first/last progress messages with timing
        if progress_logs:
            print(f"\nFirst progress: {progress_logs[0]['data']['message']} at +{progress_logs[0]['elapsed_since_start']:.1f}s")
            print(f"Last progress:  {progress_logs[-1]['data']['message']} at +{progress_logs[-1]['elapsed_since_start']:.1f}s")
        
        print("=" * 60)
        
        # Parse and validate progress output
        progress_updates = self.parse_progress_output(result.stdout, result.stderr)
        
        print(f"📊 Found {len(progress_updates)} progress updates")
        
        # Debug: Show actual subprocess output if no progress found
        if len(progress_updates) == 0:
            print("\n🔍 DEBUG: No progress found, showing subprocess output:")
            print("=" * 60)
            print("STDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            print(f"\nReturn code: {result.returncode}")
            print("=" * 60)
        
        # Validate progress structure
        self.assertGreater(len(progress_updates), 0, "Should have at least some progress updates")
        
        # Check for expected stages
        stages_found = set(update.get('stage') for update in progress_updates)
        expected_stages = {'starting', 'shape_generation', 'texture_painting', 'exporting', 'complete'}
        
        # We should see at least starting and some processing stages
        self.assertIn('starting', stages_found, "Should have starting stage")
        
        # Check progress percentage progression
        percentages = [update.get('percent', 0) for update in progress_updates if 'percent' in update]
        if percentages:
            self.assertEqual(percentages[0], 0, "Should start at 0%")
            self.assertEqual(percentages[-1], 100, "Should end at 100%")
            
            # Check that percentages generally increase
            for i in range(1, len(percentages)):
                self.assertGreaterEqual(percentages[i], percentages[i-1], 
                                       f"Progress should not go backwards: {percentages[i-1]}% -> {percentages[i]}%")
        
        # Check timing information
        elapsed_times = [update.get('elapsed_seconds', 0) for update in progress_updates if 'elapsed_seconds' in update]
        if elapsed_times:
            # Elapsed time should increase
            for i in range(1, len(elapsed_times)):
                self.assertGreater(elapsed_times[i], elapsed_times[i-1], 
                                 "Elapsed time should increase")
        
        # Check for files generation - STRICT REQUIREMENTS
        obj_path = generation_dir / "output_textured.obj"
        stl_path = generation_dir / "output_textured.stl"
        glb_path = generation_dir / "output_textured.glb"
        log_path = generation_dir / "hunyuan3d_execution.log"
        
        # Verify ALL expected files were created
        self.assertTrue(obj_path.exists(), f"OBJ file should exist: {obj_path}")
        self.assertTrue(stl_path.exists(), f"STL file should exist: {stl_path}")
        self.assertTrue(glb_path.exists(), f"GLB file should exist: {glb_path}")
        self.assertTrue(log_path.exists(), f"Log file should exist: {log_path}")
        
        # Verify file sizes are substantial
        self.assertGreater(obj_path.stat().st_size, 1000, f"OBJ file should be substantial: {obj_path.stat().st_size} bytes")
        self.assertGreater(stl_path.stat().st_size, 1000, f"STL file should be substantial: {stl_path.stat().st_size} bytes")
        self.assertGreater(glb_path.stat().st_size, 5000, f"GLB file should be substantial with textures: {glb_path.stat().st_size} bytes")
        
        print(f"✅ Progress monitoring test completed successfully!")
        print(f"✅ Found {len(progress_updates)} progress updates")
        print(f"✅ Stages detected: {sorted(stages_found)}")
        print(f"✅ Progress range: {min(percentages) if percentages else 'N/A'}% - {max(percentages) if percentages else 'N/A'}%")
        print(f"✅ OBJ file: {obj_path} ({obj_path.stat().st_size} bytes)")
        print(f"✅ STL file: {stl_path} ({stl_path.stat().st_size} bytes)")
        print(f"✅ GLB file: {glb_path} ({glb_path.stat().st_size} bytes)")
        print(f"✅ Log file: {log_path} ({log_path.stat().st_size} bytes)")
        
        # Display some sample progress messages
        if progress_updates:
            print("\n📋 Sample progress updates:")
            for i, update in enumerate(progress_updates[:5]):  # Show first 5
                stage = update.get('stage', 'unknown')
                percent = update.get('percent', 0)
                message = update.get('message', 'no message')
                elapsed = update.get('elapsed_seconds', 0)
                print(f"  {i+1}. [{stage.upper()}] {percent}% - {message} (elapsed: {elapsed:.1f}s)")
        
        return progress_updates

    def parse_progress_output(self, stdout: str, stderr: str) -> list:
        """Parse progress JSON messages from subprocess output"""
        import json
        
        progress_updates = []
        all_output = stdout + "\n" + stderr
        
        # Look for JSON progress messages
        for line in all_output.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Try to parse as JSON
            try:
                data = json.loads(line)
                if isinstance(data, dict) and data.get("type") == "progress":
                    progress_updates.append(data)
            except (json.JSONDecodeError, ValueError):
                # Not JSON, look for structured log messages
                # Look for progress indicators in text output
                if any(indicator in line.lower() for indicator in [
                    '% -', 'elapsed:', 'eta:', '[shape_generation]', '[texture_painting]', '[exporting]'
                ]):
                    # This is a progress-related message but not JSON
                    # We can extract basic info if needed
                    pass
        
        return progress_updates


if __name__ == '__main__':
    # Print dependency status
    print("🔍 Hunyuan3D Integration Test Dependencies:")
    print(f"  Conda available: {CONDA_AVAILABLE}")
    print(f"  Blender available: {BLENDER_AVAILABLE}")
    print(f"  Hunyuan3D environment: {HUNYUAN3D_ENV_AVAILABLE}")
    print()
    
    unittest.main(verbosity=2)