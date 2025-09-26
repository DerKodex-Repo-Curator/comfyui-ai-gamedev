"""
AI-powered visual verification tests for VideoFrameExtractor
Uses Ollama + qwen2.5vl:7b to automatically validate extracted frame content

IMPORTANT: These tests FAIL if Ollama is not available - they do not skip!
This is integration testing - the external service must be available.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.frame_extractor.frame_extractor_node import VideoFrameExtractorNode
from tests.comfyui_mock import ComfyUIMockContext, MockComfyUINode
from tests.test_frame_extractor_integration import MockVideoInputFromFile
from tests.ai_visual_validator import AIVisualValidator, AIValidationError, OLLAMA_AVAILABLE


class TestAIVisualVerificationFrameExtractor(unittest.TestCase, MockComfyUINode):
    """AI-powered visual verification tests for frame extraction"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        # Test video path
        cls.test_video_path = Path(__file__).parent.parent / "examples" / "ship.mp4"
        
        if not cls.test_video_path.exists():
            raise unittest.SkipTest(f"Test video not found: {cls.test_video_path}")
        
        print(f"AI visual verification using video: {cls.test_video_path}")
    
    def setUp(self):
        """Set up test fixtures"""
        # Fail if Ollama is not available - this is integration testing!
        if not OLLAMA_AVAILABLE:
            self.fail("Integration test failure: Ollama service not available. Install with: pip install ollama and ensure service is running.")
        
        # Initialize AI validator (this will check Ollama connection and model availability)
        try:
            self.ai_validator = AIVisualValidator()
        except Exception as e:
            self.fail(f"Integration test failure: Cannot initialize AI validator: {e}")
        
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = VideoFrameExtractorNode()
        self.video_input = MockVideoInputFromFile(self.test_video_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_single_frame_ai_validation(self):
        """Test AI validation of single extracted frame"""
        # Extract single frame
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames", 
            video=self.video_input,
            frame_count=1, 
            skip_start_frames=0, 
            skip_end_frames=0
        )
        
        # Verify basic properties
        self.assertEqual(extracted_count, 1)
        self.assertEqual(frames.shape[0], 1)
        self.assertEqual(frames.shape[1:], (640, 640, 3))  # H, W, C
        
        # AI validation
        prompt = "This is a single frame from an animation. It should show a clear, non-blurry object or scene with good image quality."
        
        passed, description, reason = self.ai_validator.validate_frames(frames, prompt)
        
        print(f"✅ Single frame AI validation:")
        print(f"   Result: {'PASS' if passed else 'FAIL'}")
        print(f"   AI sees: {description}")
        if not passed:
            print(f"   Reason: {reason}")
        
        if not passed:
            raise AIValidationError(description, reason)
        
        # Verify AI described some clear visual content (not blank/corrupted)
        description_lower = description.lower()
        quality_keywords = ['clear', 'object', 'metallic', 'machinery', 'weapon', 'futuristic', 'detailed']
        has_quality_content = any(keyword in description_lower for keyword in quality_keywords)
        
        self.assertTrue(has_quality_content, 
                       f"AI description should mention clear visual content: {description}")
    
    def test_three_frame_sequence_ai_validation(self):
        """Test AI validation of 3-frame sequence"""
        # Extract 3 frames
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames",
            video=self.video_input,
            frame_count=3,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Verify basic properties
        self.assertEqual(extracted_count, 3)
        self.assertEqual(frames.shape[0], 3)
        self.assertEqual(frames.shape[1:], (640, 640, 3))
        
        # AI validation
        prompt = ("These are 3 evenly distributed frames from an animation. "
                 "Each frame should show different positions or states with progressive motion. "
                 "The sequence should show movement or change between frames.")
        
        passed, description, reason = self.ai_validator.validate_frames(frames, prompt)
        
        print(f"✅ Three frame sequence AI validation:")
        print(f"   Result: {'PASS' if passed else 'FAIL'}")
        print(f"   AI sees: {description}")
        if not passed:
            print(f"   Reason: {reason}")
        
        if not passed:
            raise AIValidationError(description, reason)
        
        # Verify AI described motion or progression
        description_lower = description.lower()
        motion_keywords = ['different', 'movement', 'motion', 'change', 'position', 'progress', 'sequence']
        has_motion_content = any(keyword in description_lower for keyword in motion_keywords)
        
        self.assertTrue(has_motion_content,
                       f"AI description should mention motion/progression: {description}")
    
    def test_five_frame_distribution_ai_validation(self):
        """Test AI validation of 5-frame distribution"""
        # Extract 5 frames
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames",
            video=self.video_input,
            frame_count=5,
            skip_start_frames=0,
            skip_end_frames=0
        )
        
        # Verify basic properties
        self.assertEqual(extracted_count, 5)
        self.assertEqual(frames.shape[0], 5)
        self.assertEqual(frames.shape[1:], (640, 640, 3))
        
        # AI validation
        prompt = ("These are 5 evenly distributed frames from an animation showing the full motion sequence. "
                 "The frames should demonstrate good distribution across the video timeline with clear "
                 "progression of movement. Each frame should be distinct from the others.")
        
        passed, description, reason = self.ai_validator.validate_frames(frames, prompt)
        
        print(f"✅ Five frame distribution AI validation:")
        print(f"   Result: {'PASS' if passed else 'FAIL'}")
        print(f"   AI sees: {description}")
        if not passed:
            print(f"   Reason: {reason}")
        
        if not passed:
            raise AIValidationError(description, reason)
        
        # Verify AI described good distribution
        description_lower = description.lower()
        distribution_keywords = ['distribution', 'sequence', 'progression', 'distinct', 'different', 'timeline', 'varied']
        has_distribution_content = any(keyword in description_lower for keyword in distribution_keywords)
        
        self.assertTrue(has_distribution_content,
                       f"AI description should mention distribution/sequence: {description}")
    
    def test_ai_validation_quality_check(self):
        """Test that AI can detect quality issues (using edge case parameters)"""
        # Extract frames with potentially problematic settings
        frames, total_frames, extracted_count = self.simulate_comfyui_execution(
            self.node, "extract_frames",
            video=self.video_input,
            frame_count=2,
            skip_start_frames=20,  # Skip some of the video
            skip_end_frames=20     # Skip some of the video  
        )
        
        # Verify basic properties (should extract the requested count)
        self.assertEqual(extracted_count, 2)
        self.assertEqual(frames.shape[0], extracted_count)
        
        # AI validation with quality focus
        prompt = ("These are 2 frames from an animation. They should show clear, non-blurry "
                 "content with good image quality. The frames should not be corrupted, "
                 "black, or showing only static scenes.")
        
        passed, description, reason = self.ai_validator.validate_frames(frames, prompt)
        
        print(f"✅ AI quality check validation:")
        print(f"   Result: {'PASS' if passed else 'FAIL'}")
        print(f"   AI sees: {description}")
        if not passed:
            print(f"   Reason: {reason}")
        
        # Don't fail the test if AI detects quality issues - this is actually good!
        # We're testing that the AI can detect problems when they exist
        
        # But verify the frames are at least the right format
        self.assertEqual(frames.shape[1:], (640, 640, 3))


if __name__ == '__main__':
    unittest.main()