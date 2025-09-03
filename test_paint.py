#!/usr/bin/env python3
"""
Test script for Hunyuan3D 2.1 texture painting (Stage 2)
Run with: conda run -n hunyuan3d blender --background --python test_paint.py
Requires: Blender for texture painting
"""

import sys
import os
from pathlib import Path
from PIL import Image

# Use offline mode for HuggingFace
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

print("=" * 60)
print("Hunyuan3D 2.1 Texture Painting Test")
print("=" * 60)

# Apply torchvision compatibility fix
try:
    from hy3dpaint.utils.torchvision_fix import fix_torchvision_functional_tensor
    fix_torchvision_functional_tensor()
except ImportError:
    print("⚠️  Torchvision fix not available")

# Import Hunyuan3D painting
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig

# Check inputs from shape stage
mesh_path = "test_out/mesh.obj"
if not Path(mesh_path).exists():
    print("❌ Mesh not found at test_out/mesh.obj")
    print("   Run test_shape.py first to generate the mesh")
    sys.exit(1)

print(f"✅ Found mesh: {mesh_path}")

# Load reference images
ref_images = sorted(Path('test_out').glob('ref_*.png'))
if not ref_images:
    print("❌ No reference images found")
    print("   Run test_shape.py first")
    sys.exit(1)

# Load as PIL images
refs = [Image.open(p) for p in ref_images]
print(f"✅ Found {len(refs)} reference images")

# Configure painting
print("\n🎨 Configuring texture painting...")
paint_config = Hunyuan3DPaintConfig(
    max_num_view=len(refs),
    resolution=256  # Lower res for testing
)

# Set paths - models should be in ComfyUI directory
paint_config.multiview_cfg_path = "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
paint_config.custom_pipeline = "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr"

# RealESRGAN should be symlinked to ComfyUI's model
realesrgan_path = Path.home() / "src/ComfyUI/models/upscale_models/RealESRGAN_x4plus.pth"
if realesrgan_path.exists():
    # Create symlink in expected location if needed
    local_path = Path("external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth")
    if not local_path.exists():
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.symlink_to(realesrgan_path)
    paint_config.realesrgan_ckpt_path = str(local_path)
    print(f"   Using RealESRGAN from ComfyUI models")
else:
    print("   ⚠️  RealESRGAN not found - upscaling disabled")

print("\n🚀 Loading texture painting pipeline...")
print("   This uses models from ~/.cache/huggingface/hub/")

try:
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    print("   ✅ Pipeline loaded")
except Exception as e:
    print(f"   ❌ Failed to load pipeline: {e}")
    sys.exit(1)

print("\n🎨 Painting textures...")
print(f"   Mesh: {mesh_path}")
print(f"   References: {len(refs)} views")
print(f"   Resolution: {paint_config.resolution}")
print(f"   Steps: 30")

# Run painting (pass first image to work around multi-view bug)
try:
    result = paint_pipeline(
        mesh_path=mesh_path,
        image_path=refs[0],  # Single image due to bug in their code
        output_mesh_path="test_out/textured_mesh.glb",
        save_glb=True
    )
    print("\n✅ Texture painting complete!")
    print("   Output: test_out/textured_mesh.glb")
    
except Exception as e:
    print(f"\n❌ Texture painting failed: {e}")
    import traceback
    traceback.print_exc()
    
    # Check for common issues
    if "meshVerticeInpaint" in str(e):
        print("\n💡 Note: Custom inpainting component not compiled")
        print("   Run: cd external/Hunyuan3D-2.1/hy3dpaint/DifferentiableRenderer")
        print("        bash compile_mesh_painter.sh")
    elif "SSL" in str(e):
        print("\n💡 Note: SSL error - models may not be downloaded")
        print("   Run the install script to download models")
    
    sys.exit(1)

# List output files
print("\n📦 Output files:")
for f in Path("test_out").glob("*.glb"):
    size = f.stat().st_size / (1024 * 1024)
    print(f"   {f.name}: {size:.1f} MB")
for f in Path("test_out").glob("*.obj"):
    size = f.stat().st_size / (1024 * 1024)
    print(f"   {f.name}: {size:.1f} MB")