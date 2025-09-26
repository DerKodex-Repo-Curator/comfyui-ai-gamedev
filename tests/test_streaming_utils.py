"""
Test streaming utilities for progress reporting
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.streaming_utils import ProgressParser, execute_with_streaming_progress


class TestProgressParser(unittest.TestCase):
    """Test progress parsing functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.parser = ProgressParser()
    
    def test_stage_transitions(self):
        """Test stage transition detection"""
        # Test shape generation start
        result = self.parser.parse_line("🔨 Step 1: Shape Generation")
        self.assertEqual(result['stage'], 'shape_generation')
        self.assertEqual(result['progress'], 0)
        
        # Test texture painting start
        result = self.parser.parse_line("🎨 Step 2: Texture Painting")
        self.assertEqual(result['stage'], 'texture_painting')
        self.assertEqual(result['progress'], 0)
        
        # Test export start
        result = self.parser.parse_line("📦 Step 3: Exporting Formats")
        self.assertEqual(result['stage'], 'exporting')
        self.assertEqual(result['progress'], 0)
        
        # Test completion
        result = self.parser.parse_line("✅ GENERATION COMPLETE")
        self.assertEqual(result['stage'], 'complete')
        self.assertEqual(result['progress'], 100)
    
    def test_progress_parsing(self):
        """Test progress percentage parsing"""
        # Set stage to shape generation first
        self.parser.parse_line("🔨 Step 1: Shape Generation")
        
        # Test diffusion sampling progress
        result = self.parser.parse_line("Diffusion Sampling::  50%|█████     | 5/10 [00:01<00:01,  3.18it/s]")
        self.assertEqual(result['stage'], 'shape_generation')
        self.assertEqual(result['progress'], 50)
        
        # Test volume decoding progress
        result = self.parser.parse_line("Volume Decoding:  75%|███████▌  | 5350/7134 [00:16<00:05, 330.22it/s]")
        self.assertEqual(result['stage'], 'shape_generation')
        self.assertGreater(result['progress'], 50)  # Should be adjusted upward
        
        # Set stage to texture painting
        self.parser.parse_line("🎨 Step 2: Texture Painting")
        
        # Test pipeline loading progress
        result = self.parser.parse_line("Loading pipeline components...:  83%|████████▎ | 5/6 [00:00<00:00,  5.84it/s]")
        self.assertEqual(result['stage'], 'texture_painting')
        self.assertEqual(result['progress'], 83)
    
    def test_error_detection(self):
        """Test error line detection"""
        error_lines = [
            "❌ Generation failed",
            "ERROR: CUDA out of memory",
            "Error loading model",
            "Process failed with code 1"
        ]
        
        for error_line in error_lines:
            result = self.parser.parse_line(error_line)
            self.assertEqual(result['stage'], 'error')
            self.assertEqual(result['progress'], -1)
            self.assertIn(error_line, result['message'])


class TestStreamingExecution(unittest.TestCase):
    """Test streaming execution functionality"""
    
    def test_simple_streaming_command(self):
        """Test streaming with a simple command"""
        progress_updates = []
        
        def collect_progress(progress_info):
            progress_updates.append(progress_info)
            print(f"Progress: {progress_info}")
        
        # Test with a simple command that produces output
        result = execute_with_streaming_progress(
            ["echo", "test output"],
            progress_callback=collect_progress,
            timeout=5
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn("test output", result.stdout)
        
        # Should have at least one progress update (even if just the line itself)
        self.assertGreater(len(progress_updates), 0)
    
    def test_timeout_handling(self):
        """Test timeout handling"""
        progress_updates = []
        
        def collect_progress(progress_info):
            progress_updates.append(progress_info)
        
        # Test with a Python command that outputs and takes too long
        result = execute_with_streaming_progress(
            ["python", "-c", "import time; print('starting', flush=True); time.sleep(10); print('done')"],
            progress_callback=collect_progress,
            timeout=2  # 2 second timeout to ensure we get the output
        )
        
        # Should timeout and return -1
        self.assertEqual(result.returncode, -1)
        
        # Should have received the starting message (basic streaming works)
        self.assertGreater(len(progress_updates), 0)
        starting_messages = [p for p in progress_updates if 'starting' in p.get('message', '')]
        self.assertGreater(len(starting_messages), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)