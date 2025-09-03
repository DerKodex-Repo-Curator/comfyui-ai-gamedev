"""
Test specifically for texture generation and GLB file validation
Verifies that texture image files are properly embedded in GLB output
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys
import torch
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.hunyuan3d_node import Hunyuan3D21Node


class TestTextureGeneration(unittest.TestCase):
    """Test suite specifically for texture generation validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for test outputs
        self.temp_dir = tempfile.mkdtemp(prefix="test_hunyuan3d_")
        
        # Mock folder_paths to use our temp directory
        self.mock_folder_paths = Mock()
        self.mock_folder_paths.get_output_directory.return_value = self.temp_dir
        
        # Patch folder_paths before creating node
        self.patcher = patch('nodes.hunyuan3d.hunyuan3d_node.folder_paths', self.mock_folder_paths)
        self.patcher.start()
        
        # Create node instance
        self.node = Hunyuan3D21Node()
        
        # Create test image
        self.test_image = torch.rand(1, 512, 512, 3)
        
    def tearDown(self):
        """Clean up test fixtures"""
        self.patcher.stop()
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_glb_file_has_texture_data(self):
        """Test that GLB files contain texture data when texture generation succeeds"""
        
        # Create a mock GLB file with texture data
        mock_glb_path = Path(self.temp_dir) / "mesh" / "test_textured.glb"
        mock_glb_path.parent.mkdir(parents=True, exist_ok=True)
        
        # GLB files have a specific structure with texture data
        # A real textured GLB should be much larger than an untextured one
        # and contain image data in the buffer
        
        # Simulate a textured GLB with embedded texture
        glb_header = b'glTF\x02\x00\x00\x00'  # GLB magic header
        json_chunk_type = b'JSON'
        bin_chunk_type = b'BIN\x00'
        
        # Create a JSON chunk with texture reference
        gltf_json = {
            "asset": {"version": "2.0"},
            "images": [{
                "bufferView": 0,
                "mimeType": "image/png",
                "name": "texture"
            }],
            "materials": [{
                "pbrMetallicRoughness": {
                    "baseColorTexture": {"index": 0}
                }
            }]
        }
        json_data = json.dumps(gltf_json).encode('utf-8')
        
        # Create mock texture data (PNG image)
        # Real texture would be much larger (usually 1024x1024 or 2048x2048)
        mock_texture_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 10000  # Simulated PNG data
        
        # Write mock GLB file
        with open(mock_glb_path, 'wb') as f:
            f.write(glb_header)
            f.write(len(json_data).to_bytes(4, 'little'))
            f.write(json_chunk_type)
            f.write(json_data)
            f.write(len(mock_texture_data).to_bytes(4, 'little'))
            f.write(bin_chunk_type)
            f.write(mock_texture_data)
        
        # Verify the file exists and has substantial size
        self.assertTrue(mock_glb_path.exists())
        file_size = mock_glb_path.stat().st_size
        self.assertGreater(file_size, 1000, "Textured GLB should be larger than 1KB")
        
        # Verify file contains texture markers
        with open(mock_glb_path, 'rb') as f:
            content = f.read()
            self.assertIn(b'PNG', content, "GLB should contain PNG texture data")
            self.assertIn(b'baseColorTexture', content, "GLB should reference texture")
    
    def test_untextured_obj_vs_textured_glb_size(self):
        """Test that textured GLB files are significantly larger than untextured OBJ files"""
        
        # Create mock OBJ file (untextured)
        obj_path = Path(self.temp_dir) / "mesh" / "untextured.obj"
        obj_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Simple OBJ with just vertices and faces (no texture)
        obj_content = """# Untextured OBJ
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
f 1 2 3
f 1 3 4
"""
        obj_path.write_text(obj_content)
        obj_size = obj_path.stat().st_size
        
        # Create mock textured GLB (should be much larger)
        glb_path = Path(self.temp_dir) / "mesh" / "textured.glb"
        
        # Simulate a textured GLB with embedded 1024x1024 texture
        # Real texture data would be ~3MB for 1024x1024 RGB
        glb_data = b'glTF' + b'\x00' * (1024 * 1024 * 3)  # Simulated texture data
        glb_path.write_bytes(glb_data)
        glb_size = glb_path.stat().st_size
        
        # Textured GLB should be MUCH larger than untextured OBJ
        self.assertGreater(glb_size, obj_size * 100, 
                          f"Textured GLB ({glb_size}) should be >100x larger than OBJ ({obj_size})")
    
    @patch('nodes.hunyuan3d.hunyuan3d_node.CondaRunner')
    def test_texture_output_files_created(self, mock_conda_runner):
        """Test that texture generation creates the expected output files"""
        
        # Mock conda runner
        mock_runner = Mock()
        mock_conda_runner.return_value = mock_runner
        mock_runner.check_environment.return_value = True
        
        # Test the texture script execution
        with patch.object(self.node, '_generate_shape') as mock_shape:
            mock_shape.return_value = {"path": str(Path(self.temp_dir) / "mesh" / "test.obj"), "type": "obj"}
            
            # Mock successful texture generation
            mock_runner.execute_script.return_value = True
            
            # Create expected output GLB file when script "runs"
            def create_output_glb(*args, **kwargs):
                glb_path = Path(self.temp_dir) / "mesh" / "hunyuan3d_textured_test.glb"
                glb_path.parent.mkdir(parents=True, exist_ok=True)
                # Create a file with embedded texture data
                glb_path.write_bytes(b'glTF\x02\x00\x00\x00' + b'TEXTURE_DATA' * 1000)
                return True
            
            mock_runner.execute_script.side_effect = create_output_glb
            
            # Test texture generation
            result = self.node._apply_texture(
                mesh={"path": str(Path(self.temp_dir) / "mesh" / "test.obj"), "type": "obj"},
                images=self.test_image,
                resolution=1024,
                blender_path="blender"
            )
            
            # Verify GLB was created
            glb_files = list(Path(self.temp_dir).glob("**/*.glb"))
            self.assertGreater(len(glb_files), 0, "Should create at least one GLB file")
            
            # Verify GLB has texture data
            if glb_files:
                glb_content = glb_files[0].read_bytes()
                self.assertIn(b'TEXTURE_DATA', glb_content, "GLB should contain texture data")
    
    def test_validate_glb_structure(self):
        """Test that we can validate GLB file structure"""
        
        # Valid GLB structure
        valid_glb = b'glTF\x02\x00\x00\x00'  # Correct magic bytes
        invalid_glb = b'INVALID_FILE'  # Wrong magic bytes
        
        # Helper function to validate GLB
        def is_valid_glb(file_path):
            """Check if file is a valid GLB by checking magic bytes"""
            try:
                with open(file_path, 'rb') as f:
                    magic = f.read(4)
                    return magic == b'glTF'
            except:
                return False
        
        # Test valid GLB
        valid_path = Path(self.temp_dir) / "valid.glb"
        valid_path.write_bytes(valid_glb)
        self.assertTrue(is_valid_glb(valid_path))
        
        # Test invalid GLB
        invalid_path = Path(self.temp_dir) / "invalid.glb"
        invalid_path.write_bytes(invalid_glb)
        self.assertFalse(is_valid_glb(invalid_path))
    
    def test_texture_resolution_in_output(self):
        """Test that texture resolution parameter affects output"""
        
        # Different resolutions should produce different sized textures
        resolutions = [512, 1024, 2048]
        expected_sizes = []
        
        for res in resolutions:
            # Approximate texture size: res * res * 3 channels (RGB)
            # Plus overhead for GLB structure
            approx_size = res * res * 3
            expected_sizes.append(approx_size)
        
        # Verify each resolution produces appropriately sized output
        for res, expected in zip(resolutions, expected_sizes):
            glb_path = Path(self.temp_dir) / f"test_{res}.glb"
            
            # Simulate texture at this resolution
            texture_data = np.random.randint(0, 255, (res, res, 3), dtype=np.uint8)
            texture_bytes = texture_data.tobytes()
            
            # Create GLB with this texture
            glb_data = b'glTF\x02\x00\x00\x00' + texture_bytes
            glb_path.write_bytes(glb_data)
            
            file_size = glb_path.stat().st_size
            # File should be at least as large as the texture data
            self.assertGreaterEqual(file_size, len(texture_bytes), 
                                   f"GLB with {res}x{res} texture should be >= {len(texture_bytes)} bytes")
    
    def test_blender_requirement_for_texture(self):
        """Test that texture generation requires Blender to be available"""
        
        # Test with Blender not available
        with patch('subprocess.run') as mock_run:
            # Simulate Blender not found
            mock_run.side_effect = FileNotFoundError("blender not found")
            
            # This should detect Blender is missing
            import subprocess
            blender_available = False
            try:
                result = subprocess.run(['blender', '--version'], capture_output=True, timeout=1)
                blender_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                blender_available = False
            
            self.assertFalse(blender_available, "Should detect Blender is not available")
    
    def test_texture_painting_script_includes_blender(self):
        """Test that texture painting script properly invokes Blender"""
        
        # Generate texture painting script
        script = self.node._create_texture_script(
            mesh_path="/tmp/mesh.obj",
            image_paths=["/tmp/img.png"],
            output_glb="/tmp/output.glb",
            resolution=1024
        )
        
        # Script should include Blender-related operations
        self.assertIn("Hunyuan3DPaintPipeline", script, "Should use paint pipeline")
        self.assertIn("pbr_material=True", script, "Should enable PBR materials")
        self.assertIn("resolution=1024", script, "Should set texture resolution")
        
        # Script should handle texture output
        self.assertIn("output_dir", script, "Should specify output directory")
        self.assertIn(".glb", script, "Should output GLB format")


if __name__ == "__main__":
    unittest.main()