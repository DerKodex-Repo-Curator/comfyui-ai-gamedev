"""
Unit tests for Hunyuan3D 2.1 ComfyUI node
Tests conditional texture generation and output validation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import torch
import numpy as np
from pathlib import Path
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.hunyuan3d_node import Hunyuan3D21Node


class TestHunyuan3DNode(unittest.TestCase):
    """Test suite for Hunyuan3D node functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.node = Hunyuan3D21Node()
        # Create a dummy image tensor (batch_size=1, height=512, width=512, channels=3)
        self.single_image = torch.rand(1, 512, 512, 3)
        # Multi-view batch (10 images)
        self.multi_images = torch.rand(10, 512, 512, 3)
        
    def test_node_class_attributes(self):
        """Test that node has correct class attributes"""
        # Check return types
        self.assertEqual(Hunyuan3D21Node.RETURN_TYPES, ("STRING", "STRING", "IMAGE"))
        self.assertEqual(Hunyuan3D21Node.RETURN_NAMES, ("mesh", "textured_glb", "preview"))
        self.assertEqual(Hunyuan3D21Node.FUNCTION, "generate_3d")
        self.assertEqual(Hunyuan3D21Node.CATEGORY, "gamedev/3d")
        self.assertTrue(Hunyuan3D21Node.OUTPUT_NODE)
        
    def test_input_types(self):
        """Test INPUT_TYPES class method"""
        input_types = Hunyuan3D21Node.INPUT_TYPES()
        
        # Check required inputs
        self.assertIn("required", input_types)
        self.assertIn("images", input_types["required"])
        self.assertIn("resolution", input_types["required"])
        self.assertIn("guidance_scale", input_types["required"])
        self.assertIn("steps", input_types["required"])
        
        # Check optional inputs
        self.assertIn("optional", input_types)
        self.assertIn("enable_texture", input_types["optional"])
        self.assertIn("texture_resolution", input_types["optional"])
        self.assertIn("multi_view_mode", input_types["optional"])
        self.assertIn("seed", input_types["optional"])
        self.assertIn("blender_path", input_types["optional"])
        
    def test_multi_view_detection(self):
        """Test multi-view mode detection logic"""
        # Test auto mode
        self.assertFalse(self.node._determine_multi_view(1, "auto"))
        self.assertTrue(self.node._determine_multi_view(5, "auto"))
        self.assertTrue(self.node._determine_multi_view(10, "auto"))
        self.assertFalse(self.node._determine_multi_view(11, "auto"))  # >10 should be false
        
        # Test forced single mode
        self.assertFalse(self.node._determine_multi_view(5, "single"))
        self.assertFalse(self.node._determine_multi_view(10, "single"))
        
        # Test forced multi mode
        self.assertTrue(self.node._determine_multi_view(2, "multi"))
        self.assertTrue(self.node._determine_multi_view(10, "multi"))
        
    @patch('nodes.hunyuan3d.hunyuan3d_node.CondaRunner')
    def test_conditional_texture_generation_disconnected(self, mock_conda_runner):
        """Test that texture is NOT generated when textured_glb output is disconnected"""
        # Mock conda runner
        mock_runner = Mock()
        mock_conda_runner.return_value = mock_runner
        mock_runner.check_environment.return_value = True
        mock_runner.execute_script.return_value = True
        
        # Mock the shape generation to return a valid path
        with patch.object(self.node, '_generate_shape') as mock_generate:
            mock_generate.return_value = {"path": "/tmp/test.obj", "type": "obj"}
            
            # Mock preview generation
            with patch.object(self.node, '_generate_preview') as mock_preview:
                mock_preview.return_value = torch.zeros(1, 512, 512, 3)
                
                # Mock texture application - this should NOT be called
                with patch.object(self.node, '_apply_texture') as mock_texture:
                    # Simulate disconnected textured_glb output
                    outputs_needed = {"textured_glb": False}
                    
                    result = self.node.generate_3d(
                        images=self.single_image,
                        resolution="512",
                        guidance_scale=7.5,
                        steps=50,
                        enable_texture=True,  # Even with this True
                        outputs_needed=outputs_needed  # But output disconnected
                    )
                    
                    # Verify texture was NOT applied
                    mock_texture.assert_not_called()
                    
                    # Check outputs
                    obj_path, glb_path, preview = result
                    self.assertIsInstance(obj_path, str)
                    self.assertEqual(glb_path, "")  # Should be empty
                    self.assertIsInstance(preview, torch.Tensor)
    
    @patch('nodes.hunyuan3d.hunyuan3d_node.CondaRunner')
    def test_conditional_texture_generation_connected(self, mock_conda_runner):
        """Test that texture IS generated when textured_glb output is connected"""
        # Mock conda runner
        mock_runner = Mock()
        mock_conda_runner.return_value = mock_runner
        mock_runner.check_environment.return_value = True
        mock_runner.execute_script.return_value = True
        
        # Mock the shape generation
        with patch.object(self.node, '_generate_shape') as mock_generate:
            mock_generate.return_value = {"path": "/tmp/test.obj", "type": "obj"}
            
            # Mock preview generation
            with patch.object(self.node, '_generate_preview') as mock_preview:
                mock_preview.return_value = torch.zeros(1, 512, 512, 3)
                
                # Mock texture application
                with patch.object(self.node, '_apply_texture') as mock_texture:
                    mock_texture.return_value = {"path": "/tmp/test.glb", "type": "glb", "has_texture": True}
                    
                    # Simulate connected textured_glb output
                    outputs_needed = {"textured_glb": True}
                    
                    result = self.node.generate_3d(
                        images=self.single_image,
                        resolution="512",
                        guidance_scale=7.5,
                        steps=50,
                        enable_texture=True,
                        texture_resolution="1024",
                        outputs_needed=outputs_needed
                    )
                    
                    # Verify texture WAS applied
                    mock_texture.assert_called_once()
                    
                    # Check outputs
                    obj_path, glb_path, preview = result
                    self.assertIsInstance(obj_path, str)
                    self.assertIsInstance(glb_path, str)
                    self.assertNotEqual(glb_path, "")  # Should have a path
                    self.assertIsInstance(preview, torch.Tensor)
    
    @patch('nodes.hunyuan3d.hunyuan3d_node.CondaRunner')
    def test_texture_disabled_by_parameter(self, mock_conda_runner):
        """Test that texture is not generated when enable_texture=False"""
        # Mock conda runner
        mock_runner = Mock()
        mock_conda_runner.return_value = mock_runner
        mock_runner.check_environment.return_value = True
        
        with patch.object(self.node, '_generate_shape') as mock_generate:
            mock_generate.return_value = {"path": "/tmp/test.obj", "type": "obj"}
            
            with patch.object(self.node, '_generate_preview') as mock_preview:
                mock_preview.return_value = torch.zeros(1, 512, 512, 3)
                
                with patch.object(self.node, '_apply_texture') as mock_texture:
                    # Even with output connected
                    outputs_needed = {"textured_glb": True}
                    
                    result = self.node.generate_3d(
                        images=self.single_image,
                        resolution="512",
                        guidance_scale=7.5,
                        steps=50,
                        enable_texture=False,  # Disabled by parameter
                        outputs_needed=outputs_needed
                    )
                    
                    # Texture should not be applied
                    mock_texture.assert_not_called()
                    
                    obj_path, glb_path, preview = result
                    self.assertEqual(glb_path, "")
    
    def test_script_generation(self):
        """Test that shape and texture scripts are generated correctly"""
        # Test shape script generation
        shape_script = self.node._create_shape_script(
            image_paths=["/tmp/img1.png"],
            output_mesh="/tmp/output.obj",
            resolution=512,
            guidance_scale=7.5,
            steps=50,
            is_multi_view=False,
            seed=42
        )
        
        # Check script contains required elements
        self.assertIn("import sys", shape_script)
        self.assertIn("sys.path.insert", shape_script)
        self.assertIn("Hunyuan3DDiTFlowMatchingPipeline", shape_script)
        self.assertIn("resolution=512", shape_script)
        self.assertIn("guidance_scale=7.5", shape_script)
        self.assertIn("num_inference_steps=50", shape_script)
        self.assertIn("torch.manual_seed(42)", shape_script)
        
        # Test texture script generation
        texture_script = self.node._create_texture_script(
            mesh_path="/tmp/mesh.obj",
            image_paths=["/tmp/img1.png"],
            output_glb="/tmp/output.glb",
            resolution=1024
        )
        
        # Check texture script contains required elements
        self.assertIn("Hunyuan3DPaintPipeline", texture_script)
        self.assertIn("resolution=1024", texture_script)
        self.assertIn("/tmp/output.glb", texture_script)
    
    def test_image_batch_processing(self):
        """Test handling of single vs batch images"""
        # Single image
        single_batch = self.single_image.shape[0]
        self.assertEqual(single_batch, 1)
        
        # Multi-view batch
        multi_batch = self.multi_images.shape[0]
        self.assertEqual(multi_batch, 10)
        
        # Test batch size limits for multi-view
        is_multi = self.node._determine_multi_view(multi_batch, "auto")
        self.assertTrue(is_multi)
        
        # Test batch size >10 (should not be multi-view in auto mode)
        large_batch = torch.rand(15, 512, 512, 3)
        is_multi_large = self.node._determine_multi_view(large_batch.shape[0], "auto")
        self.assertFalse(is_multi_large)
    
    def test_output_path_generation(self):
        """Test that output paths are generated correctly"""
        # The node should create unique output paths
        self.assertTrue(self.node.output_dir.exists())
        self.assertTrue(self.node.output_dir.is_dir())
        
    def test_conda_environment_check(self):
        """Test conda environment validation"""
        with patch('nodes.hunyuan3d.hunyuan3d_node.CondaRunner') as mock_conda:
            mock_runner = Mock()
            mock_conda.return_value = mock_runner
            
            # Test with valid environment
            mock_runner.check_environment.return_value = True
            node = Hunyuan3D21Node()
            # Should initialize without issues
            
            # Test with invalid environment
            mock_runner.check_environment.return_value = False
            node = Hunyuan3D21Node()
            # Should print warning but not crash


class TestHunyuan3DIntegration(unittest.TestCase):
    """Integration tests for Hunyuan3D node"""
    
    @unittest.skipUnless(
        Path("/home/matt/src/comfyui-ai-gamedev/examples/input_images/single_view/railgun/frame_001_4x.png").exists(),
        "Test image not found"
    )
    def test_with_real_image(self):
        """Test with real image file (if available)"""
        from PIL import Image
        import torchvision.transforms as transforms
        
        # Load test image
        img_path = "/home/matt/src/comfyui-ai-gamedev/examples/input_images/single_view/railgun/frame_001_4x.png"
        img = Image.open(img_path).convert("RGB")
        
        # Convert to tensor
        transform = transforms.ToTensor()
        img_tensor = transform(img).permute(1, 2, 0).unsqueeze(0)  # HWC format for ComfyUI
        
        # Verify tensor shape
        self.assertEqual(img_tensor.dim(), 4)
        self.assertEqual(img_tensor.shape[3], 3)  # RGB channels


if __name__ == "__main__":
    unittest.main()