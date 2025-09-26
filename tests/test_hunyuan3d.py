"""
Unit tests for Hunyuan3D 2.1 node that simulate ComfyUI execution
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import os
import torch
import numpy as np
from pathlib import Path
import sys
import tempfile
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.hunyuan3d_21_node import Hunyuan3D21Node
from tests.comfyui_mock import ComfyUIMockContext, create_test_image_tensor, MockComfyUINode, create_mock_subprocess_result


class TestHunyuan3D21Node(unittest.TestCase, MockComfyUINode):
    """Test suite for Hunyuan3D 2.1 node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = Hunyuan3D21Node()
        
        # Create test images
        self.single_image = create_test_image_tensor(batch_size=1, height=256, width=256)
        self.multi_images = create_test_image_tensor(batch_size=4, height=512, width=512)
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
        
    def test_node_class_attributes(self):
        """Test that node has correct class attributes"""
        self.assertEqual(Hunyuan3D21Node.RETURN_TYPES, ("STRING", "STRING", "STRING"))
        self.assertEqual(Hunyuan3D21Node.RETURN_NAMES, ("glb_filepath", "obj_filepath", "stl_filepath"))
        self.assertEqual(Hunyuan3D21Node.FUNCTION, "generate_3d")
        self.assertEqual(Hunyuan3D21Node.CATEGORY, "🎮 AI GameDev/3D")
        self.assertTrue(Hunyuan3D21Node.OUTPUT_NODE)
        
    def test_input_types(self):
        """Test INPUT_TYPES class method"""
        input_types = Hunyuan3D21Node.INPUT_TYPES()
        
        # Check required inputs
        self.assertIn("required", input_types)
        self.assertIn("images", input_types["required"])
        self.assertIn("resolution", input_types["required"])
        self.assertIn("texture_resolution", input_types["required"])
        self.assertIn("guidance_scale", input_types["required"])
        self.assertIn("inference_steps", input_types["required"])
        
        # Check optional inputs
        self.assertIn("optional", input_types)
        self.assertIn("conda_env", input_types["optional"])
        self.assertIn("conda_path", input_types["optional"])
        
        # Check image input type
        images_config = input_types["required"]["images"]
        self.assertEqual(images_config[0], "IMAGE")
        
        # Check resolution options
        resolution_config = input_types["required"]["resolution"]
        self.assertIn("256", resolution_config[0])
        self.assertIn("512", resolution_config[0])
        self.assertIn("1024", resolution_config[0])
        
        # Check guidance scale range
        guidance_config = input_types["required"]["guidance_scale"]
        self.assertEqual(guidance_config[1]["min"], 1.0)
        self.assertEqual(guidance_config[1]["max"], 20.0)
        self.assertEqual(guidance_config[1]["default"], 7.5)
        
        # Check inference steps range
        steps_config = input_types["required"]["inference_steps"]
        self.assertEqual(steps_config[1]["min"], 10)
        self.assertEqual(steps_config[1]["max"], 100)
        self.assertEqual(steps_config[1]["default"], 30)
    
    def test_node_initialization(self):
        """Test node initializes correctly"""
        self.assertIsNotNone(self.node.output_dir)
        self.assertTrue(self.node.output_dir.exists())
        self.assertEqual(self.node.output_dir.name, "mesh")
        
        # Check script path exists
        self.assertTrue(self.node.script_path.exists())
        self.assertEqual(self.node.script_path.name, "hunyuan3d_execute.py")
    
    @patch('subprocess.run')
    def test_successful_3d_generation(self, mock_subprocess):
        """Test successful 3D model generation"""
        # Setup mock successful subprocess result
        mock_subprocess.return_value = create_mock_subprocess_result(
            stdout="✅ Shape generation completed\n✅ Texture generation completed\n✅ Export completed",
            stderr="",
            returncode=0
        )
        
        # Mock the output files existing
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = self.simulate_comfyui_execution(
                self.node,
                "generate_3d",
                images=self.single_image,
                resolution="512",
                texture_resolution="768",
                guidance_scale=7.5,
                inference_steps=30
            )
            
            glb_path, obj_path, stl_path = result
            
            # Check that file paths are returned
            self.assertIsInstance(glb_path, str)
            self.assertIsInstance(obj_path, str)
            self.assertIsInstance(stl_path, str)
            self.assertTrue(glb_path.endswith('.glb'))
            self.assertTrue(obj_path.endswith('.obj'))
            self.assertTrue(stl_path.endswith('.stl'))
            
            # Check subprocess was called correctly
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args
            
            # Verify conda command structure
            cmd = call_args[0][0]
            self.assertIn("conda", cmd[0])
            self.assertIn("run", cmd[1])
            self.assertIn("-n", cmd[2])
            self.assertIn("hunyuan3d", cmd[3])  # default conda env
            self.assertIn("blender", cmd[4])
            self.assertIn("--background", cmd[5])
            self.assertIn("--python", cmd[6])
    
    @patch('subprocess.run')
    def test_failed_3d_generation(self, mock_subprocess):
        """Test failed 3D model generation"""
        # Setup mock failed subprocess result
        mock_subprocess.return_value = create_mock_subprocess_result(
            stdout="❌ Shape generation failed",
            stderr="Error: CUDA out of memory",
            returncode=1
        )
        
        # Mock the output files NOT existing
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = self.simulate_comfyui_execution(
                self.node,
                "generate_3d",
                images=self.single_image,
                resolution="512",
                texture_resolution="768",
                guidance_scale=7.5,
                inference_steps=30
            )
            
            glb_path, obj_path, stl_path = result
            
            # Check that empty paths are returned on failure
            self.assertEqual(glb_path, "")
            self.assertEqual(obj_path, "")
            self.assertEqual(stl_path, "")
            
            # Check subprocess was still called
            mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_custom_conda_settings(self, mock_subprocess):
        """Test custom conda environment and path settings"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            self.simulate_comfyui_execution(
                self.node,
                "generate_3d",
                images=self.single_image,
                resolution="256",
                texture_resolution="512",
                guidance_scale=5.0,
                inference_steps=20,
                conda_env="custom_env",
                conda_path="/custom/conda"
            )
            
            # Check subprocess was called with custom settings
            call_args = mock_subprocess.call_args
            cmd = call_args[0][0]
            
            self.assertEqual(cmd[0], "/custom/conda")
            self.assertIn("custom_env", cmd)
    
    @patch('subprocess.run')
    def test_multi_image_input(self, mock_subprocess):
        """Test generation with multiple input images"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            result = self.simulate_comfyui_execution(
                self.node,
                "generate_3d",
                images=self.multi_images,  # 4 images
                resolution="512",
                texture_resolution="768",
                guidance_scale=7.5,
                inference_steps=30
            )
            
            # Should still return file paths
            glb_path, obj_path, stl_path = result
            self.assertNotEqual(glb_path, "")
            self.assertNotEqual(obj_path, "")
            self.assertNotEqual(stl_path, "")
            
            # Check that subprocess was called
            mock_subprocess.assert_called_once()
    
    @patch('subprocess.run')
    def test_environment_variable_defaults(self, mock_subprocess):
        """Test environment variable defaults for conda settings"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Mock environment variables
            with patch.dict('os.environ', {'HUNYUAN3D_CONDA_ENV': 'env_from_env', 'HUNYUAN3D_CONDA_PATH': '/env/conda'}):
                # Create new node to pick up env vars
                test_node = Hunyuan3D21Node()
                
                self.simulate_comfyui_execution(
                    test_node,
                    "generate_3d",
                    images=self.single_image,
                    resolution="512",
                    texture_resolution="768",
                    guidance_scale=7.5,
                    inference_steps=30
                )
                
                # Check subprocess was called with env var settings
                call_args = mock_subprocess.call_args
                cmd = call_args[0][0]
                
                self.assertEqual(cmd[0], "/env/conda")
                self.assertIn("env_from_env", cmd)
    
    @patch('subprocess.run')
    def test_subprocess_timeout_handling(self, mock_subprocess):
        """Test handling of subprocess timeout"""
        # Mock timeout exception
        mock_subprocess.side_effect = subprocess.TimeoutExpired("cmd", timeout=600)
        
        result = self.simulate_comfyui_execution(
            self.node,
            "generate_3d",
            images=self.single_image,
            resolution="512",
            texture_resolution="768",
            guidance_scale=7.5,
            inference_steps=30
        )
        
        glb_path, obj_path, stl_path = result
        
        # Should return empty strings on timeout
        self.assertEqual(glb_path, "")
        self.assertEqual(obj_path, "")
        self.assertEqual(stl_path, "")
    
    @patch('subprocess.run')
    def test_image_tensor_formats(self, mock_subprocess):
        """Test different image tensor formats are handled correctly"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Test with different tensor formats
            test_cases = [
                create_test_image_tensor(1, 256, 256, 3),  # Standard format
                create_test_image_tensor(1, 512, 512, 3),  # Different resolution
                create_test_image_tensor(3, 256, 256, 3),  # Multiple images
            ]
            
            for test_images in test_cases:
                with self.subTest(shape=test_images.shape):
                    result = self.simulate_comfyui_execution(
                        self.node,
                        "generate_3d",
                        images=test_images,
                        resolution="512",
                        texture_resolution="768",
                        guidance_scale=7.5,
                        inference_steps=30
                    )
                    
                    # Should succeed with valid tensor formats
                    glb_path, obj_path, stl_path = result
                    if mock_exists.return_value:  # If files exist, should return paths
                        self.assertNotEqual(glb_path, "")
    
    def test_output_directory_creation(self):
        """Test that output directory is created correctly"""
        # The directory should be created during initialization
        self.assertTrue(self.node.output_dir.exists())
        self.assertTrue(self.node.output_dir.is_dir())
        
        # Should be under ComfyUI output directory
        self.assertIn("mesh", str(self.node.output_dir))
    
    @patch('subprocess.run')
    def test_clean_exit_handling(self, mock_subprocess):
        """Test that Blender exits cleanly with segfault fix applied"""
        # Mock subprocess that exits cleanly (with segfault fix)
        mock_subprocess.return_value = create_mock_subprocess_result(
            stdout="✅ Shape generation completed\n✅ Texture generation completed\n✅ Script complete. Blender should exit cleanly",
            stderr="",
            returncode=0  # Clean exit with segfault fix
        )
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True  # Files were created successfully
            
            result = self.simulate_comfyui_execution(
                self.node,
                "generate_3d",
                images=self.single_image,
                resolution="512",
                texture_resolution="768",
                guidance_scale=7.5,
                inference_steps=30
            )
            
            glb_path, obj_path, stl_path = result
            
            # Should return file paths when process exits cleanly and files exist
            self.assertNotEqual(glb_path, "")
            self.assertNotEqual(obj_path, "")
            self.assertNotEqual(stl_path, "")
    
    def test_is_changed_method(self):
        """Test IS_CHANGED class method"""
        result = Hunyuan3D21Node.IS_CHANGED()
        # Should return NaN to indicate always changed
        self.assertTrue(np.isnan(result))


class TestHunyuan3DIntegration(unittest.TestCase, MockComfyUINode):
    """Integration tests for Hunyuan3D node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_node_registration(self):
        """Test node is properly registered for ComfyUI"""
        from nodes.hunyuan3d.hunyuan3d_21_node import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
        
        self.assertIn("Hunyuan3D21", NODE_CLASS_MAPPINGS)
        self.assertEqual(NODE_CLASS_MAPPINGS["Hunyuan3D21"], Hunyuan3D21Node)
        
        self.assertIn("Hunyuan3D21", NODE_DISPLAY_NAME_MAPPINGS)
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["Hunyuan3D21"], "Hunyuan3D 2.1")
    
    def test_execution_script_exists(self):
        """Test that the execution script exists and is readable"""
        node = Hunyuan3D21Node()
        self.assertTrue(node.script_path.exists(), "Hunyuan3D execution script not found")
        self.assertTrue(node.script_path.is_file(), "Execution script is not a file")
        
        # Should be a Python file
        self.assertEqual(node.script_path.suffix, ".py")
    
    @patch('subprocess.run')
    def test_parameter_validation(self, mock_subprocess):
        """Test that different parameter combinations work"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        node = Hunyuan3D21Node()
        test_image = create_test_image_tensor(1, 256, 256, 3)
        
        # Test different parameter combinations
        test_params = [
            {"resolution": "256", "texture_resolution": "512", "guidance_scale": 1.0, "inference_steps": 10},
            {"resolution": "512", "texture_resolution": "768", "guidance_scale": 10.0, "inference_steps": 50},
            {"resolution": "1024", "texture_resolution": "1024", "guidance_scale": 20.0, "inference_steps": 100},
        ]
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            for params in test_params:
                with self.subTest(**params):
                    result = node.generate_3d(
                        images=test_image,
                        **params
                    )
                    
                    # Should return three file paths
                    self.assertEqual(len(result), 3)
                    glb_path, obj_path, stl_path = result
                    self.assertIsInstance(glb_path, str)
                    self.assertIsInstance(obj_path, str)
                    self.assertIsInstance(stl_path, str)
    
    @patch('subprocess.run')
    def test_config_file_creation_and_cleanup(self, mock_subprocess):
        """Test that config files are created and cleaned up properly"""
        mock_subprocess.return_value = create_mock_subprocess_result(returncode=0)
        
        node = Hunyuan3D21Node()
        test_image = create_test_image_tensor(1, 256, 256, 3)
        
        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True
            
            # Track file operations
            with patch('builtins.open', unittest.mock.mock_open()) as mock_open:
                with patch('pathlib.Path.unlink') as mock_unlink:
                    
                    node.generate_3d(
                        images=test_image,
                        resolution="512",
                        texture_resolution="768",
                        guidance_scale=7.5,
                        inference_steps=30
                    )
                    
                    # Should have opened a file for writing config
                    mock_open.assert_called()
                    
                    # Should have cleaned up config file
                    mock_unlink.assert_called()


if __name__ == '__main__':
    unittest.main()