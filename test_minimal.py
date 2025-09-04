#!/usr/bin/env python3
"""
Minimal test for Hunyuan3D texture painting
Tests the complete pipeline: shape generation + texture painting
"""

import sys
import torch
import numpy as np
from pathlib import Path
from PIL import Image

# Add the nodes directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock folder_paths for testing outside ComfyUI
class MockFolderPaths:
    @staticmethod
    def get_output_directory():
        return str(Path(__file__).parent / "test_output")

sys.modules['folder_paths'] = MockFolderPaths()

from nodes.hunyuan3d.hunyuan3d_unified_node import Hunyuan3D21UnifiedNode

def create_test_image(width=512, height=512):
    """Create a simple test image"""
    # Create a gradient image for testing
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Create a simple pattern
    for y in range(height):
        for x in range(width):
            img[y, x] = [
                int((x / width) * 255),  # Red gradient
                int((y / height) * 255),  # Green gradient
                128  # Fixed blue
            ]
    
    return img

def main():
    print("=" * 60)
    print("MINIMAL HUNYUAN3D TEXTURE PAINTING TEST")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Load a test image
    test_image_path = Path(__file__).parent / "examples" / "input_images" / "single_view" / "railgun" / "frame_001_4x.png"
    
    if test_image_path.exists():
        print(f"✅ Using test image: {test_image_path}")
        img = Image.open(test_image_path).convert("RGB")
        img_array = np.array(img)
    else:
        print("⚠️  Test image not found, creating synthetic image")
        img_array = create_test_image()
    
    # Convert to tensor format [B, H, W, C] with values 0-1
    img_tensor = torch.from_numpy(img_array).float() / 255.0
    img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
    
    print(f"📷 Input shape: {img_tensor.shape}")
    
    # Initialize the node
    print("\n🔧 Initializing Hunyuan3D node...")
    node = Hunyuan3D21UnifiedNode()
    
    # Test parameters
    params = {
        "images": img_tensor,
        "enable_texture": True,  # Enable texture painting
        "resolution": "256",  # Low resolution for faster testing
        "texture_resolution": "512",  # Low texture resolution for testing
        "guidance_scale": 7.5,
        "shape_steps": 10,  # Minimal steps for testing
        "texture_steps": 10,  # Minimal steps for testing
        "seed": 42
    }
    
    print("\n🚀 Starting 3D generation with texture painting...")
    print(f"   Shape resolution: {params['resolution']}")
    print(f"   Texture resolution: {params['texture_resolution']}")
    print(f"   Shape steps: {params['shape_steps']}")
    print(f"   Texture steps: {params['texture_steps']}")
    
    try:
        # Run the generation
        mesh, glb_path, obj_path, stl_path = node.generate_3d(**params)
        
        print("\n" + "=" * 60)
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        if mesh:
            vertices = mesh.vertices[0]
            faces = mesh.faces[0]
            print(f"📦 Generated mesh: {vertices.shape[0]} vertices, {faces.shape[0]} faces")
        
        if glb_path:
            print(f"📁 GLB file: {glb_path}")
            if Path(glb_path).exists():
                size_mb = Path(glb_path).stat().st_size / (1024 * 1024)
                print(f"   Size: {size_mb:.2f} MB")
                
                # Check if it has texture by file size (textured > untextured)
                if size_mb > 0.5:  # Textured files are typically larger
                    print(f"   ✅ Appears to have texture (size > 0.5 MB)")
                else:
                    print(f"   ⚠️  May be untextured (size < 0.5 MB)")
        
        if obj_path and Path(obj_path).exists():
            print(f"📁 OBJ file: {obj_path}")
        
        if stl_path and Path(stl_path).exists():
            print(f"📁 STL file: {stl_path}")
        
        print("\n✨ Test passed! Files generated successfully.")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)