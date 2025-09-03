# Two-stage pipeline: Shape generation and texture painting as separate steps
# This demonstrates memory-efficient processing

import sys
from pathlib import Path
from PIL import Image
import gc
import torch

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

# Apply torchvision compatibility fix
try:
    from hy3dpaint.utils.torchvision_fix import fix_torchvision_functional_tensor
    fix_torchvision_functional_tensor()
except ImportError:
    try:
        from torchvision_fix import fix_torchvision_functional_tensor
        fix_torchvision_functional_tensor()
    except ImportError:
        print("⚠️  Torchvision fix not found - proceeding without fix")

# Load images once
images = sorted(Path('.').glob('examples/input_images/multi_view/frame_*_4x.png'))[:10]
pil_images = [Image.open(img).convert("RGB") for img in images]
print(f"Loaded {len(pil_images)} images")

Path("test_out").mkdir(exist_ok=True)

# ============ STAGE 1: Shape Generation ============
print("\n=== STAGE 1: Shape Generation ===")
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

print("Loading shape model...")
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1',
    subfolder='hunyuan3d-dit-v2-1'
)

print("Generating 3D shape...")
mesh = shape_pipeline(
    image=pil_images,
    num_inference_steps=50,
    multi_view=True
)[0]

# Save untextured mesh
mesh.export("test_out/mesh.obj")
print("Saved untextured mesh: test_out/mesh.obj")

# FREE MEMORY - Critical for memory efficiency!
del shape_pipeline
del mesh
gc.collect()
torch.cuda.empty_cache()
print("Shape model unloaded from memory")

# ============ STAGE 2: Texture Painting ============
print("\n=== STAGE 2: Texture Painting ===")
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig

print("Loading paint model...")
paint_config = Hunyuan3DPaintConfig(
    max_num_view=len(pil_images),
    resolution=512,
    pbr_material=True
)
paint_pipeline = Hunyuan3DPaintPipeline(paint_config)

# Save reference images for painting
refs = []
for i, img in enumerate(pil_images):
    path = f"test_out/ref_{i}.png"
    img.save(path)
    refs.append(path)

print("Painting textures with Blender...")
textured = paint_pipeline(
    mesh_path="test_out/mesh.obj",  # Load from disk!
    image_path=refs,
    output_dir="test_out",
    num_inference_steps=50,
    multi_view=True
)

# Export final textured model
textured.export("test_out/final.glb")
print("Saved textured model: test_out/final.glb")

# Cleanup
del paint_pipeline
gc.collect()
torch.cuda.empty_cache()

print("\n=== Pipeline Complete ===")
print("Outputs:")
print("  - Untextured: test_out/mesh.obj")
print("  - Textured: test_out/final.glb")