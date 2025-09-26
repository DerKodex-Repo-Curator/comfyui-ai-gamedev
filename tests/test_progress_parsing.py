"""
Test progress parsing for structured JSON logging from Hunyuan3D execution
"""

import unittest
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.progress_utils import ProgressTracker, ProgressParser, format_duration


class TestProgressParser(unittest.TestCase):
    """Test parsing of JSON progress messages"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ProgressParser()
    
    def test_parse_valid_json_progress(self):
        """Test parsing valid JSON progress messages"""
        # Test shape generation progress
        json_line = '{"type": "progress", "stage": "shape_generation", "percent": 25, "elapsed_seconds": 30, "estimated_total_seconds": 120, "message": "Generating 3D shape", "timestamp": "2024-01-01T12:00:00"}'
        
        progress = self.parser.parse_line(json_line)
        
        self.assertIsNotNone(progress)
        self.assertEqual(progress.stage, "shape_generation")
        self.assertEqual(progress.percent, 25)
        self.assertEqual(progress.elapsed_seconds, 30)
        self.assertEqual(progress.estimated_total_seconds, 120)
        self.assertEqual(progress.remaining_seconds, 90)
        self.assertEqual(progress.message, "Generating 3D shape")
        
    def test_parse_stage_transitions(self):
        """Test parsing of stage transition messages"""
        test_cases = [
            ('{"type": "progress", "stage": "shape_generation", "percent": 0, "elapsed_seconds": 0, "estimated_total_seconds": 300, "message": "Starting shape generation"}', "shape_generation", 0),
            ('{"type": "progress", "stage": "texture_painting", "percent": 50, "elapsed_seconds": 150, "estimated_total_seconds": 300, "message": "Starting texture painting"}', "texture_painting", 50),
            ('{"type": "progress", "stage": "exporting", "percent": 90, "elapsed_seconds": 270, "estimated_total_seconds": 300, "message": "Exporting 3D models"}', "exporting", 90),
            ('{"type": "progress", "stage": "complete", "percent": 100, "elapsed_seconds": 300, "estimated_total_seconds": 300, "message": "Generation complete"}', "complete", 100),
        ]
        
        for json_line, expected_stage, expected_percent in test_cases:
            with self.subTest(stage=expected_stage):
                progress = self.parser.parse_line(json_line)
                self.assertIsNotNone(progress)
                self.assertEqual(progress.stage, expected_stage)
                self.assertEqual(progress.percent, expected_percent)
    
    def test_parse_non_json_lines(self):
        """Test that non-JSON lines are ignored"""
        non_json_lines = [
            "Regular stdout line",
            "ERROR: Something went wrong",
            "🔨 Step 1: Shape Generation",
            "Diffusion Sampling:: 50%|█████     | 5/10 [00:01<00:01,  3.18it/s]",
            "",
            "Color management: using fallback mode",
        ]
        
        for line in non_json_lines:
            with self.subTest(line=line):
                progress = self.parser.parse_line(line)
                self.assertIsNone(progress, f"Expected None for line: {line}")
    
    def test_parse_malformed_json(self):
        """Test handling of malformed JSON"""
        malformed_lines = [
            '{"type": "progress", "stage": "shape_generation"',  # Missing closing brace
            '{"type": "progress", stage: "shape_generation"}',   # Missing quotes
            '{"type": "progress", "stage": "shape_generation", "percent": "not_a_number"}',  # Invalid percent
        ]
        
        for line in malformed_lines:
            with self.subTest(line=line):
                progress = self.parser.parse_line(line)
                self.assertIsNone(progress, f"Expected None for malformed JSON: {line}")
    
    def test_parse_mixed_output(self):
        """Test parsing mixed JSON and non-JSON output"""
        mixed_output = [
            "Script starting...",
            '{"type": "progress", "stage": "shape_generation", "percent": 0, "elapsed_seconds": 0, "estimated_total_seconds": 180, "message": "Starting"}',
            "Loading model weights...",
            "✓ Model loaded",
            '{"type": "progress", "stage": "shape_generation", "percent": 25, "elapsed_seconds": 45, "estimated_total_seconds": 180, "message": "Shape generation 25%"}',
            "Diffusion Sampling:: 25%|██▌       | 25/100 [00:45<02:15,  1.8s/it]",
            '{"type": "progress", "stage": "texture_painting", "percent": 50, "elapsed_seconds": 90, "estimated_total_seconds": 180, "message": "Starting texture painting"}',
            "Blender quit",
        ]
        
        progress_updates = []
        for line in mixed_output:
            progress = self.parser.parse_line(line)
            if progress:
                progress_updates.append(progress)
        
        # Should have extracted 3 progress updates
        self.assertEqual(len(progress_updates), 3)
        
        # Check progression
        self.assertEqual(progress_updates[0].percent, 0)
        self.assertEqual(progress_updates[1].percent, 25)
        self.assertEqual(progress_updates[2].percent, 50)
        
        # Check stages
        self.assertEqual(progress_updates[0].stage, "shape_generation")
        self.assertEqual(progress_updates[1].stage, "shape_generation")
        self.assertEqual(progress_updates[2].stage, "texture_painting")


class TestProgressTracker(unittest.TestCase):
    """Test progress tracking functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.tracker = ProgressTracker()
    
    def test_initial_state(self):
        """Test initial tracker state"""
        self.assertEqual(self.tracker.stage, "starting")
        self.assertEqual(self.tracker.percent, 0)
        self.assertLess(self.tracker.elapsed_seconds, 0.1)  # Should be very small but not exactly 0
        self.assertIsNone(self.tracker.estimated_total_seconds)
    
    def test_stage_progression(self):
        """Test stage progression with time estimates"""
        # Start shape generation
        self.tracker.update_progress("shape_generation", 0, "Starting shape generation", estimated_total=300)
        self.assertEqual(self.tracker.stage, "shape_generation")
        self.assertEqual(self.tracker.estimated_total_seconds, 300)
        
        # Progress through shape generation
        time.sleep(0.1)  # Small delay
        self.tracker.update_progress("shape_generation", 25, "Shape generation 25%")
        self.assertEqual(self.tracker.percent, 25)
        self.assertGreater(self.tracker.elapsed_seconds, 0)
        
        # Move to texture painting
        self.tracker.update_progress("texture_painting", 50, "Starting texture painting")
        self.assertEqual(self.tracker.stage, "texture_painting")
        self.assertEqual(self.tracker.percent, 50)
        
        # Complete
        self.tracker.update_progress("complete", 100, "Generation complete")
        self.assertEqual(self.tracker.stage, "complete")
        self.assertEqual(self.tracker.percent, 100)
    
    def test_json_output(self):
        """Test JSON serialization of progress"""
        self.tracker.update_progress("shape_generation", 33, "Progress message", estimated_total=180)
        
        json_str = self.tracker.to_json()
        self.assertIsInstance(json_str, str)
        
        # Parse back to verify
        data = json.loads(json_str)
        self.assertEqual(data["type"], "progress")
        self.assertEqual(data["stage"], "shape_generation")
        self.assertEqual(data["percent"], 33)
        self.assertEqual(data["message"], "Progress message")
        self.assertIn("timestamp", data)
        self.assertIn("elapsed_seconds", data)
        self.assertIn("estimated_total_seconds", data)
    
    def test_remaining_time_calculation(self):
        """Test remaining time calculation"""
        self.tracker.update_progress("shape_generation", 0, "Starting", estimated_total=100)
        
        # Simulate 25% progress after 25 seconds
        self.tracker.start_time = time.time() - 25
        self.tracker.update_progress("shape_generation", 25, "25% complete")
        
        # Should estimate 75 seconds remaining (75% of 100s total)
        remaining = self.tracker.estimated_total_seconds - self.tracker.elapsed_seconds
        self.assertAlmostEqual(remaining, 75, delta=5)  # Allow some variance


class TestDurationFormatting(unittest.TestCase):
    """Test duration formatting utilities"""
    
    def test_format_duration_seconds(self):
        """Test formatting durations in seconds"""
        test_cases = [
            (0, "0s"),
            (30, "30s"),
            (59, "59s"),
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_duration(seconds)
                self.assertEqual(result, expected)
    
    def test_format_duration_minutes(self):
        """Test formatting durations in minutes"""
        test_cases = [
            (60, "1m 0s"),
            (90, "1m 30s"),
            (120, "2m 0s"),
            (125, "2m 5s"),
            (3599, "59m 59s"),
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_duration(seconds)
                self.assertEqual(result, expected)
    
    def test_format_duration_hours(self):
        """Test formatting durations in hours"""
        test_cases = [
            (3600, "1h 0m 0s"),
            (3661, "1h 1m 1s"),
            (7200, "2h 0m 0s"),
            (7325, "2h 2m 5s"),
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_duration(seconds)
                self.assertEqual(result, expected)
    
    def test_format_duration_fractional(self):
        """Test formatting fractional seconds"""
        test_cases = [
            (30.5, "30s"),  # Should round down
            (90.7, "1m 30s"),  # Should round down
            (125.9, "2m 5s"),  # Should round down
        ]
        
        for seconds, expected in test_cases:
            with self.subTest(seconds=seconds):
                result = format_duration(seconds)
                self.assertEqual(result, expected)


class TestProgressObject(unittest.TestCase):
    """Test the Progress object with pretty formatting"""
    
    def test_progress_object_creation(self):
        """Test creating Progress objects"""
        progress = ProgressTracker.Progress(
            stage="shape_generation",
            percent=33,
            elapsed_seconds=60,
            estimated_total_seconds=180,
            message="Generating shape",
            timestamp="2024-01-01T12:00:00"
        )
        
        self.assertEqual(progress.stage, "shape_generation")
        self.assertEqual(progress.percent, 33)
        self.assertEqual(progress.elapsed_seconds, 60)
        self.assertEqual(progress.estimated_total_seconds, 180)
        self.assertEqual(progress.remaining_seconds, 120)
        self.assertEqual(progress.message, "Generating shape")
    
    def test_progress_pretty_formatting(self):
        """Test pretty formatting of progress"""
        progress = ProgressTracker.Progress(
            stage="texture_painting",
            percent=67,
            elapsed_seconds=125,
            estimated_total_seconds=200,
            message="Painting textures",
            timestamp="2024-01-01T12:02:05"
        )
        
        formatted = progress.format_pretty()
        
        # Should include all key information
        self.assertIn("67%", formatted)
        self.assertIn("TEXTURE_PAINTING", formatted)  # Stage is uppercased
        self.assertIn("Painting textures", formatted)
        self.assertIn("2m 5s", formatted)  # elapsed time
        self.assertIn("1m 15s", formatted)  # remaining time
    
    def test_progress_eta_calculation(self):
        """Test ETA calculation"""
        progress = ProgressTracker.Progress(
            stage="exporting",
            percent=90,
            elapsed_seconds=270,
            estimated_total_seconds=300,
            message="Exporting models",
            timestamp="2024-01-01T12:04:30"
        )
        
        # Should have 30 seconds remaining
        self.assertEqual(progress.remaining_seconds, 30)
        
        # ETA should be approximately 30 seconds from timestamp
        eta = progress.get_eta()
        self.assertIsInstance(eta, datetime)


if __name__ == '__main__':
    unittest.main(verbosity=2)