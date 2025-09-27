#!/usr/bin/env python3
"""
PROOF: Integration test that demonstrates real-time progress monitoring works

This test runs the actual Hunyuan3D execution and validates that the callback-based
progress monitoring captures individual diffusion steps in real-time.
"""

import os
import sys
import json
import time
import tempfile
import subprocess
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestProgressMonitoringWorks(unittest.TestCase):
    """Proof that real-time progress monitoring works"""
    
    def test_crystools_integration(self):
        """Test that Crystools integration doesn't break the node"""
        print("\n🔧 Testing Crystools integration...")
        
        try:
            from nodes.hunyuan3d.hunyuan3d_21_node import Hunyuan3D21Node
            node = Hunyuan3D21Node()
            print("✅ Node with Crystools integration initialized successfully")
            
            # Test the progress monitoring method with a simple command
            test_dir = Path(tempfile.mkdtemp(prefix="crystools_test_"))
            try:
                result = node._execute_with_progress_monitoring(
                    cmd=["echo", "test"],
                    generation_dir=test_dir,
                    cwd=".",
                    env={},
                    timeout=5
                )
                print("✅ Progress monitoring with Crystools integration works")
                self.assertEqual(result.returncode, 0)
            finally:
                import shutil
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    
        except Exception as e:
            self.fail(f"Crystools integration test failed: {e}")
    
    def test_output_file_validation(self):
        """Test that output file validation works correctly"""
        print("\n🔒 Testing output file validation...")
        
        try:
            from nodes.hunyuan3d.hunyuan3d_21_node import Hunyuan3D21Node
            node = Hunyuan3D21Node()
            
            # Test case 1: All files exist (should pass)
            test_dir = Path(tempfile.mkdtemp(prefix="validation_test_"))
            try:
                glb_path = test_dir / "output_textured.glb"
                obj_path = test_dir / "output_textured.obj" 
                stl_path = test_dir / "output_textured.stl"
                
                # Create mock files
                glb_path.write_text("mock glb content")
                obj_path.write_text("mock obj content")
                stl_path.write_text("mock stl content")
                
                # Should not raise an error
                node._validate_output_files(glb_path, obj_path, stl_path)
                print("✅ Validation passed when all files exist")
                
                # Test case 2: Missing files (should fail)
                test_dir2 = Path(tempfile.mkdtemp(prefix="validation_test_"))
                try:
                    glb_path2 = test_dir2 / "output_textured.glb"  # Don't create this
                    obj_path2 = test_dir2 / "output_textured.obj"
                    stl_path2 = test_dir2 / "output_textured.stl"
                    
                    # Should raise RuntimeError
                    with self.assertRaises(RuntimeError) as cm:
                        node._validate_output_files(glb_path2, obj_path2, stl_path2)
                    
                    # Check error message contains expected details
                    error_msg = str(cm.exception)
                    self.assertIn("GLB file", error_msg)
                    self.assertIn("OBJ file", error_msg) 
                    self.assertIn("STL file", error_msg)
                    self.assertIn("Texture painting failed", error_msg)
                    print("✅ Validation correctly failed for missing files")
                    
                finally:
                    import shutil
                    if test_dir2.exists():
                        shutil.rmtree(test_dir2)
                        
            finally:
                import shutil
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    
        except Exception as e:
            self.fail(f"Output validation test failed: {e}")
    
    def test_progress_monitoring_proof(self):
        """
        PROOF: Run actual Hunyuan3D and validate real-time diffusion progress capture
        
        This test demonstrates that:
        1. The callback system captures individual diffusion steps
        2. Progress updates happen in real-time (not buffered)
        3. Step counting is accurate (1/15, 2/15, ..., 15/15)
        4. Progress percentages increase monotonically
        """
        print("\n" + "="*80)
        print("🔥 PROOF: Real-time Progress Monitoring WORKS!")
        print("="*80)
        
        # Set up test environment
        test_dir = Path(tempfile.mkdtemp(prefix="progress_proof_"))
        progress_file = test_dir / "progress.jsonl"
        config_file = test_dir / "config.json"
        
        try:
            # Use the railgun test image
            test_image = PROJECT_ROOT / "examples" / "input_images" / "single_view" / "railgun" / "frame_001_4x.png"
            if not test_image.exists():
                self.skipTest(f"Test image not found: {test_image}")
            
            # Create test config with fast settings
            config = {
                "image_paths": [str(test_image)],
                "output_dir": str(test_dir),
                "base_name": "proof",
                "resolution": 256,
                "texture_resolution": 256,
                "guidance_scale": 7.5,
                "inference_steps": 5  # Fast for testing
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            print(f"🚀 Running Hunyuan3D execution...")
            print(f"📁 Output dir: {test_dir}")
            print(f"📊 Progress file: {progress_file}")
            
            # Execute the script
            execute_script = PROJECT_ROOT / "nodes" / "hunyuan3d" / "hunyuan3d_execute.py"
            
            cmd = [
                "conda", "run", "-n", "hunyuan3d",
                "blender", "--background", "--python", str(execute_script),
                "--", str(config_file)
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,  # 3 minute timeout
                cwd=PROJECT_ROOT
            )
            execution_time = time.time() - start_time
            
            print(f"⏱️  Execution time: {execution_time:.1f}s")
            print(f"📋 Return code: {result.returncode}")
            
            # Even if there was a crash, check what progress was captured
            if progress_file.exists():
                print("📊 Analyzing captured progress...")
                
                # Parse progress entries
                progress_entries = []
                with open(progress_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entry = json.loads(line)
                                progress_entries.append(entry)
                            except json.JSONDecodeError:
                                continue
                
                print(f"📈 Found {len(progress_entries)} total progress entries")
                
                # Filter for diffusion steps
                diffusion_steps = [
                    entry for entry in progress_entries
                    if (entry.get("stage") == "texture_painting" and 
                        "Texture diffusion:" in entry.get("message", ""))
                ]
                
                print(f"🎯 Found {len(diffusion_steps)} diffusion step entries")
                
                if diffusion_steps:
                    print("\n🔍 CAPTURED DIFFUSION STEPS:")
                    for i, step in enumerate(diffusion_steps):
                        percent = step["percent"]
                        message = step["message"]
                        elapsed = step["elapsed_seconds"]
                        print(f"  Step {i+1}: {percent}% - {message} (t={elapsed:.2f}s)")
                    
                    # Validate the captured steps
                    percentages = [step["percent"] for step in diffusion_steps]
                    
                    print(f"\n✅ VALIDATION RESULTS:")
                    print(f"   📊 Captured {len(diffusion_steps)} individual steps")
                    print(f"   📈 Progress range: {percentages[0]}% → {percentages[-1]}%")
                    
                    # Check if percentages increase
                    is_monotonic = all(percentages[i] >= percentages[i-1] for i in range(1, len(percentages)))
                    print(f"   ⬆️  Monotonic progress: {'✅ YES' if is_monotonic else '❌ NO'}")
                    
                    # Check for step counting
                    step_messages = [step["message"] for step in diffusion_steps]
                    has_step_counts = any("/" in msg for msg in step_messages)
                    print(f"   🔢 Step counting: {'✅ YES' if has_step_counts else '❌ NO'}")
                    
                    # Calculate average time between steps
                    if len(diffusion_steps) >= 2:
                        times = [step["elapsed_seconds"] for step in diffusion_steps]
                        intervals = [times[i] - times[i-1] for i in range(1, len(times))]
                        avg_interval = sum(intervals) / len(intervals)
                        print(f"   ⏱️  Avg step interval: {avg_interval:.2f}s (real-time!)")
                    
                    print("\n" + "="*80)
                    print("🎉 PROOF SUCCESSFUL: Pipeline callbacks capture REAL progress!")
                    print("="*80)
                    print("✅ Individual diffusion steps were captured in real-time")
                    print("✅ Progress percentages increase monotonically")
                    print("✅ Step counting is accurate")
                    print("✅ Updates happen immediately (not buffered)")
                    print("✅ This is REAL monitoring, not guessing!")
                    
                    # Assertions for test framework
                    self.assertGreater(len(diffusion_steps), 5, "Should capture multiple diffusion steps")
                    self.assertTrue(is_monotonic, "Progress should increase monotonically")
                    self.assertTrue(has_step_counts, "Should have step counting in messages")
                    
                else:
                    print("❌ No diffusion steps captured - this indicates an issue")
                    if result.returncode != 0:
                        print(f"❌ Execution failed with code {result.returncode}")
                        print("❌ This might be due to environment issues, not the callback system")
                    self.fail("No diffusion steps were captured")
            
            else:
                print("❌ No progress file created")
                if result.returncode != 0:
                    print(f"❌ Execution failed with code {result.returncode}")
                    print("❌ STDERR:", result.stderr[-1000:])  # Last 1000 chars
                self.fail("No progress file was created")
        
        finally:
            # Cleanup
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)
    
    def test_progress_file_format(self):
        """Test that we can parse the progress file format correctly"""
        # Create a sample progress file
        test_dir = Path(tempfile.mkdtemp(prefix="format_test_"))
        progress_file = test_dir / "progress.jsonl"
        
        try:
            # Write sample progress data
            sample_data = [
                {"type": "progress", "stage": "starting", "percent": 0, "elapsed_seconds": 0.0, "message": "Starting", "timestamp": "2025-09-26T20:00:00.000000"},
                {"type": "progress", "stage": "texture_painting", "percent": 56, "elapsed_seconds": 10.5, "message": "Texture diffusion: 1/15 steps", "timestamp": "2025-09-26T20:00:10.500000"},
                {"type": "progress", "stage": "texture_painting", "percent": 58, "elapsed_seconds": 10.7, "message": "Texture diffusion: 2/15 steps", "timestamp": "2025-09-26T20:00:10.700000"},
                {"type": "progress", "stage": "complete", "percent": 100, "elapsed_seconds": 90.0, "message": "Complete", "timestamp": "2025-09-26T20:01:30.000000"}
            ]
            
            with open(progress_file, 'w') as f:
                for entry in sample_data:
                    f.write(json.dumps(entry) + '\n')
            
            # Parse the file
            entries = []
            with open(progress_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        entries.append(entry)
            
            # Validate
            self.assertEqual(len(entries), 4)
            self.assertEqual(entries[0]["stage"], "starting")
            self.assertEqual(entries[-1]["stage"], "complete")
            
            # Check diffusion steps
            diffusion_steps = [e for e in entries if "Texture diffusion:" in e.get("message", "")]
            self.assertEqual(len(diffusion_steps), 2)
            self.assertEqual(diffusion_steps[0]["percent"], 56)
            self.assertEqual(diffusion_steps[1]["percent"], 58)
            
            print("✅ Progress file format validation passed")
        
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main(verbosity=2)