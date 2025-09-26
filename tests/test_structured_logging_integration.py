"""
Integration test for structured logging in Hunyuan3D execution
"""

import unittest
import json
import tempfile
import subprocess
from pathlib import Path
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.progress_utils import ProgressParser, parse_hunyuan3d_output


class TestStructuredLoggingIntegration(unittest.TestCase):
    """Test structured logging integration with Hunyuan3D execution"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ProgressParser()
        self.project_root = Path(__file__).parent.parent
    
    def test_progress_parsing_from_sample_output(self):
        """Test parsing progress from sample JSON output"""
        # Sample output that our modified script should produce
        sample_output = [
            "starting...",
            "============================================================",
            "SCRIPT STARTING", 
            "============================================================",
            '{"type": "progress", "stage": "starting", "percent": 0, "elapsed_seconds": 0.1, "estimated_total_seconds": 450, "message": "Initializing Hunyuan3D execution", "timestamp": "2024-01-01T12:00:00"}',
            "Loading pretrained model...",
            '{"type": "progress", "stage": "shape_generation", "percent": 5, "elapsed_seconds": 15.2, "estimated_total_seconds": 450, "message": "Loading 3D shape generation model", "timestamp": "2024-01-01T12:00:15"}',
            "✓ Model loaded",
            '{"type": "progress", "stage": "shape_generation", "percent": 10, "elapsed_seconds": 30.5, "estimated_total_seconds": 450, "message": "Generating 3D shape with 10 steps", "timestamp": "2024-01-01T12:00:30"}',
            "Generating shape with 10 steps...",
            "Diffusion Sampling::  50%|█████     | 5/10 [00:30<00:30,  3.18it/s]",
            "✓ Shape generated",
            '{"type": "progress", "stage": "shape_generation", "percent": 50, "elapsed_seconds": 120.8, "estimated_total_seconds": 450, "message": "3D shape generation completed successfully", "timestamp": "2024-01-01T12:02:00"}',
            "♻️ Freeing shape generation memory...",
            "✓ Memory freed",
            '{"type": "progress", "stage": "texture_painting", "percent": 55, "elapsed_seconds": 140.1, "estimated_total_seconds": 450, "message": "Initializing texture painting pipeline", "timestamp": "2024-01-01T12:02:20"}',
            "🎨 Step 2: Texture Painting",
            "Importing trimesh...",
            "✓ Trimesh imported",
            "Loading pipeline components...:  50%|█████     | 3/6 [00:05<00:05,  1.8s/it]",
            "✅ Texture painting complete",
            '{"type": "progress", "stage": "texture_painting", "percent": 85, "elapsed_seconds": 320.7, "estimated_total_seconds": 450, "message": "Texture painting completed successfully", "timestamp": "2024-01-01T12:05:20"}',
            "📦 Step 3: Exporting Formats",
            '{"type": "progress", "stage": "exporting", "percent": 90, "elapsed_seconds": 340.2, "estimated_total_seconds": 450, "message": "Exporting 3D models to GLB, OBJ, and STL formats", "timestamp": "2024-01-01T12:05:40"}',
            "✅ GLB exported: output_textured.glb",
            "✅ OBJ exported: output_textured.obj", 
            "✅ STL exported: output_textured.stl",
            '{"type": "progress", "stage": "complete", "percent": 100, "elapsed_seconds": 420.5, "estimated_total_seconds": 450, "message": "Hunyuan3D generation completed successfully", "timestamp": "2024-01-01T12:07:00"}',
            "✅ GENERATION COMPLETE",
            "Script complete. Blender should exit cleanly."
        ]
        
        # Parse progress from the output
        progress_updates = parse_hunyuan3d_output(sample_output)
        
        # Should have extracted 8 progress updates
        self.assertEqual(len(progress_updates), 8)
        
        # Verify progression
        expected_stages = [
            ("starting", 0),
            ("shape_generation", 5),
            ("shape_generation", 10), 
            ("shape_generation", 50),
            ("texture_painting", 55),
            ("texture_painting", 85),
            ("exporting", 90),
            ("complete", 100)
        ]
        
        for i, (expected_stage, expected_percent) in enumerate(expected_stages):
            with self.subTest(i=i, stage=expected_stage):
                self.assertEqual(progress_updates[i].stage, expected_stage)
                self.assertEqual(progress_updates[i].percent, expected_percent)
                self.assertIsNotNone(progress_updates[i].message)
                self.assertGreater(progress_updates[i].elapsed_seconds, 0)
    
    def test_progress_time_calculations(self):
        """Test time calculations and formatting"""
        json_line = '{"type": "progress", "stage": "texture_painting", "percent": 67, "elapsed_seconds": 200.5, "estimated_total_seconds": 300, "message": "Texture painting in progress", "timestamp": "2024-01-01T12:03:20"}'
        
        progress = self.parser.parse_line(json_line)
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.percent, 67)
        self.assertEqual(progress.elapsed_seconds, 200.5)
        self.assertEqual(progress.estimated_total_seconds, 300)
        self.assertEqual(progress.remaining_seconds, 99.5)  # 300 - 200.5
        
        # Test pretty formatting
        formatted = progress.format_pretty()
        self.assertIn("67%", formatted)
        self.assertIn("TEXTURE_PAINTING", formatted)
        self.assertIn("3m 20s", formatted)  # elapsed time
        self.assertIn("1m 39s", formatted)  # remaining time
    
    def test_mixed_output_with_non_json(self):
        """Test parsing mixed output with regular stdout/stderr"""
        mixed_output = [
            "Blender startup messages",
            "Color management: using fallback mode",
            '{"type": "progress", "stage": "starting", "percent": 0, "elapsed_seconds": 0, "estimated_total_seconds": 180, "message": "Starting"}',
            "Some torch warnings...",
            "PointCrossAttentionEncoder INFO: pc_sharpedge_size is zero",
            "using moe",
            '{"type": "progress", "stage": "shape_generation", "percent": 25, "elapsed_seconds": 45, "estimated_total_seconds": 180, "message": "Shape generation 25%"}',
            "Volume Decoding:  50%|█████     | 3567/7134 [00:45<00:45, 330.22it/s]",
            "Exception in module unregister(): '_ops.py'",
            '{"type": "progress", "stage": "complete", "percent": 100, "elapsed_seconds": 150, "estimated_total_seconds": 180, "message": "Complete"}',
            "Segmentation fault (core dumped)"
        ]
        
        progress_updates = parse_hunyuan3d_output(mixed_output)
        
        # Should extract only the 3 JSON progress lines
        self.assertEqual(len(progress_updates), 3)
        self.assertEqual(progress_updates[0].percent, 0)
        self.assertEqual(progress_updates[1].percent, 25)
        self.assertEqual(progress_updates[2].percent, 100)
    
    def test_progress_with_file_logging(self):
        """Test progress tracking with file logging (simulated)"""
        from nodes.hunyuan3d.progress_utils import LoggingProgressTracker
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file_path = f.name
        
        try:
            # Create tracker with file logging
            tracker = LoggingProgressTracker(log_file_path)
            
            # Simulate progress updates
            tracker.update_progress("starting", 0, "Initializing", estimated_total=180)
            time.sleep(0.1)  # Small delay
            tracker.update_progress("shape_generation", 25, "Shape generation 25%")
            time.sleep(0.1)
            tracker.update_progress("texture_painting", 75, "Texture painting 75%")
            time.sleep(0.1)
            tracker.update_progress("complete", 100, "Generation complete")
            
            # Log some raw content
            tracker.log_raw("Some debug output", "debug")
            tracker.log_raw("Model loaded successfully", "info")
            
            # Save logs
            success = tracker.save_raw_logs()
            self.assertTrue(success)
            
            # Verify log file exists and has content
            log_path = Path(log_file_path)
            self.assertTrue(log_path.exists())
            
            log_content = log_path.read_text()
            self.assertIn("Initializing", log_content)  # Changed from "Starting"
            self.assertIn("Shape generation 25%", log_content)
            self.assertIn("Some debug output", log_content)
            self.assertIn("Model loaded successfully", log_content)
            
            # Should have timestamp entries
            self.assertIn("[info]", log_content)
            self.assertIn("[debug]", log_content)
            
        finally:
            # Cleanup
            Path(log_file_path).unlink(missing_ok=True)
    
    def test_error_handling_in_parsing(self):
        """Test error handling for malformed progress JSON"""
        error_cases = [
            '{"type": "progress"',  # Incomplete JSON
            '{"type": "not_progress", "stage": "test"}',  # Wrong type
            '{"type": "progress", "stage": "test"}',  # Missing required fields
            '{"type": "progress", "stage": "test", "percent": "not_a_number", "elapsed_seconds": 0, "message": "test"}',  # Invalid percent
            'Not JSON at all',
            '',  # Empty line
        ]
        
        for error_input in error_cases:
            with self.subTest(input=error_input):
                result = self.parser.parse_line(error_input)
                self.assertIsNone(result, f"Should return None for: {error_input}")
    
    def test_progress_stages_sequence(self):
        """Test that progress stages follow expected sequence"""
        # Expected stage progression with approximate percentages
        expected_sequence = [
            ("starting", 0, 5),
            ("shape_generation", 5, 50),
            ("texture_painting", 50, 90),
            ("exporting", 90, 99),
            ("complete", 100, 100)
        ]
        
        # Simulate realistic progress sequence
        progress_lines = []
        for stage, min_pct, max_pct in expected_sequence:
            # Add a progress update for this stage
            json_data = {
                "type": "progress",
                "stage": stage,
                "percent": min_pct,
                "elapsed_seconds": min_pct * 3,  # Simulate timing
                "estimated_total_seconds": 300,
                "message": f"Stage {stage} at {min_pct}%",
                "timestamp": "2024-01-01T12:00:00"
            }
            progress_lines.append(json.dumps(json_data))
        
        # Parse all progress
        progress_updates = parse_hunyuan3d_output(progress_lines)
        
        # Verify sequence
        self.assertEqual(len(progress_updates), len(expected_sequence))
        
        for i, (expected_stage, expected_min, expected_max) in enumerate(expected_sequence):
            progress = progress_updates[i]
            self.assertEqual(progress.stage, expected_stage)
            self.assertGreaterEqual(progress.percent, expected_min)
            self.assertLessEqual(progress.percent, expected_max)
            
            # Verify remaining time calculation
            if progress.estimated_total_seconds:
                expected_remaining = progress.estimated_total_seconds - progress.elapsed_seconds
                self.assertEqual(progress.remaining_seconds, expected_remaining)


class TestOutputLogFormat(unittest.TestCase):
    """Test the JSON output format matches our parsing expectations"""
    
    def test_json_format_specification(self):
        """Test that our JSON format meets the specification"""
        from nodes.hunyuan3d.progress_utils import LoggingProgressTracker
        
        tracker = LoggingProgressTracker()
        tracker.update_progress("shape_generation", 33, "Test message", estimated_total=180)
        
        json_str = tracker.to_json()
        
        # Parse and validate structure
        data = json.loads(json_str)
        
        # Required fields
        self.assertEqual(data["type"], "progress")
        self.assertIn("stage", data)
        self.assertIn("percent", data) 
        self.assertIn("elapsed_seconds", data)
        self.assertIn("message", data)
        self.assertIn("timestamp", data)
        
        # Optional fields
        self.assertIn("estimated_total_seconds", data)
        
        # Type validation
        self.assertIsInstance(data["percent"], int)
        self.assertIsInstance(data["elapsed_seconds"], (int, float))
        self.assertIsInstance(data["message"], str)
        self.assertIsInstance(data["timestamp"], str)


if __name__ == '__main__':
    unittest.main(verbosity=2)