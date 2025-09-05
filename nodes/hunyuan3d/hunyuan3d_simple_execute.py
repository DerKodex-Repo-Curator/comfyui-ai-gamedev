#!/usr/bin/env python3
"""
Simplified Hunyuan3D execution - hardcoded settings based on working test_minimal.py
Arguments: image_path output_dir base_name
"""

import sys
import os
from pathlib import Path

# Use offline mode
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Get arguments
image_path = sys.argv[sys.argv.index('--') + 1]
output_dir = Path(sys.argv[sys.argv.index('--') + 2])
base_name = sys.argv[sys.argv.index('--') + 3]

print(f"Processing: {image_path}")
print(f"Output to: {output_dir}/{base_name}")

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

from PIL import Image

# Apply torchvision fix first (like demo.py)
try:
    from torchvision_fix import apply_fix
    apply_fix()
except:
    pass

from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig

# Load image
img = Image.open(image_path).convert("RGB")

# Output paths
shape_path = output_dir / f"{base_name}_shape.obj"
textured_glb_path = output_dir / f"{base_name}_textured.glb"
textured_obj_path = output_dir / f"{base_name}_textured.obj" 
textured_stl_path = output_dir / f"{base_name}_textured.stl"

print("\n🔨 Step 1: Shape Generation")
print("-" * 40)

# Generate shape with HARDCODED reliable settings
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1',
    subfolder='hunyuan3d-dit-v2-1'
)

# HARDCODED: 10 steps (minimum that works), resolution 256 (fast), guidance 7.5 (default)
result = shape_pipeline(
    image=img,
    num_inference_steps=10,
    guidance_scale=7.5,
    resolution=256
)

if result is None or len(result) == 0 or result[0] is None:
    print("❌ Shape generation failed")
    sys.exit(1)

mesh = result[0]
mesh.export(str(shape_path))
print(f"✅ Shape saved: {shape_path.name}")

print("\n🎨 Step 2: Texture Painting")
print("-" * 40)

try:
    import trimesh
    
    # HARDCODED texture settings: resolution 512 (fast but decent quality)
    paint_config = Hunyuan3DPaintConfig(1, 512)
    
    # Set paths (use current working directory)
    project_root = Path(os.getcwd())
    paint_config.realesrgan_ckpt_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth")
    paint_config.multiview_cfg_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml")
    paint_config.custom_pipeline = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr")
    
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    
    # Paint texture
    textured_result = paint_pipeline(
        str(shape_path),
        image_path=image_path,
    )
    
    print(f"✅ Texture complete: {textured_result}")
    
    # Export formats
    print("\n📦 Step 3: Exporting Formats")
    print("-" * 40)
    
    mesh_textured = trimesh.load(textured_result)
    
    # Export all formats
    mesh_textured.export(str(textured_glb_path))
    print(f"✅ GLB: {textured_glb_path.name}")
    
    mesh_textured.export(str(textured_obj_path))
    print(f"✅ OBJ: {textured_obj_path.name}")
    
    mesh_textured.export(str(textured_stl_path))
    print(f"✅ STL: {textured_stl_path.name}")
    
except Exception as e:
    print(f"❌ Texture painting failed: {e}")
    # Export untextured as fallback
    try:
        import trimesh
        mesh_untextured = trimesh.load(str(shape_path))
        mesh_untextured.export(str(textured_glb_path))
        mesh_untextured.export(str(textured_obj_path))
        mesh_untextured.export(str(textured_stl_path))
        print("⚠️ Exported untextured mesh as fallback")
    except:
        pass

# Cleanup temp shape file
shape_path.unlink(missing_ok=True)

print("\n✅ COMPLETE")
print(f"   Output: {base_name}_textured.glb")
# Script will segfault here - that's OK