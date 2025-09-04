#!/usr/bin/env python3
"""
Minimal test for Hunyuan3D 2.1 pipeline
MUST BE RUN THROUGH BLENDER: conda run -n hunyuan3d blender --background --python test_minimal.py
"""

import sys
import os
# Use offline mode to avoid SSL issues
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
from pathlib import Path

# Apply torchvision fix for painting
try:
    from torchvision_fix import fix_torchvision_functional_tensor
    fix_torchvision_functional_tensor()
except:
    pass

# Create output directory
Path('test_out').mkdir(exist_ok=True)

# Generate shape
print("Generating shape...")
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained('tencent/Hunyuan3D-2.1', subfolder='hunyuan3d-dit-v2-1')
mesh = shape_pipeline(image='examples/input_images/single_view/railgun/frame_001_4x.png', num_inference_steps=10)[0]
mesh.export('test_out/mesh.obj')
print("✅ Shape saved: test_out/mesh.obj")

# Paint texture
print("Painting texture...")
try:
    import trimesh
    
    paint_config = Hunyuan3DPaintConfig(max_num_view=1, resolution=512)
    # Set absolute paths for all required files
    base_dir = os.path.dirname(os.path.abspath(__file__))
    paint_config.realesrgan_ckpt_path = os.path.join(base_dir, "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth")
    paint_config.multiview_cfg_path = os.path.join(base_dir, "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml")
    paint_config.custom_pipeline = os.path.join(base_dir, "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr")
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    
    # Use simpler API - just get textured OBJ path
    textured_obj_path = paint_pipeline(
        'test_out/mesh.obj',
        image_path='examples/input_images/single_view/railgun/frame_001_4x.png',
    )
    print("✅ Done painting!")
    
    # Convert to GLB using trimesh
    print("Converting to GLB format...")
    mesh_textured = trimesh.load(textured_obj_path)
    glb_path = 'test_out/textured.glb'
    mesh_textured.export(glb_path)
    print(f"✅ Textured model: {glb_path}")
    
except Exception as e:
    print(f"❌ Painting failed: {e}")
    import traceback
    traceback.print_exc()