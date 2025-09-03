#!/usr/bin/env python3
"""
Test script for Hunyuan3D 2.1 shape generation (Stage 1)
Run with: python test_shape.py
No Blender required for this stage
"""

import sys
import os
from pathlib import Path
from PIL import Image

# Use offline mode for HuggingFace to avoid SSL issues
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')

print("=" * 60)
print("Hunyuan3D 2.1 Shape Generation Test")
print("=" * 60)

# Import Hunyuan3D shape generation
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

# Load multi-view images
images = sorted(Path('.').glob('examples/input_images/multi_view/frame_*_4x.png'))[:10]
if not images:
    print("❌ No test images found")
    print("   Expected: examples/input_images/multi_view/frame_*_4x.png")
    sys.exit(1)

pil_images = [Image.open(img).convert("RGB") for img in images]
print(f"✅ Loaded {len(pil_images)} images")

# Create output dir
Path("test_out").mkdir(exist_ok=True)

# Generate shape
print("\n🎮 Loading shape generation model...")
print("   This will use models from ~/.cache/huggingface/hub/")

shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1',
    subfolder='hunyuan3d-dit-v2-1'
)

print("\n🎨 Generating 3D shape...")
print("   Input: Multi-view images")
print("   Steps: 30")
print("   Resolution: 512")

mesh = shape_pipeline(
    image=pil_images,
    num_inference_steps=30,
    multi_view=True
)[0]

# Save mesh
output_path = "test_out/mesh.obj"
mesh.export(output_path)
print(f"\n✅ Shape generation complete!")
print(f"   Output: {output_path}")

# Also save reference images for painting stage
print("\n💾 Saving reference images for painting stage...")
for i, img in enumerate(pil_images):
    path = f"test_out/ref_{i}.png"
    img.save(path)
print(f"   Saved {len(pil_images)} reference images")

print("\n📋 Next step:")
print("   Run: conda run -n hunyuan3d blender --background --python test_paint.py")
print("   to apply textures to the mesh")