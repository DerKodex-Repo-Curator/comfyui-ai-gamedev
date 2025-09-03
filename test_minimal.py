# Minimal test for Hunyuan3D 2.1 multi-view pipeline
# Paste this into interactive Python shell

import sys
from pathlib import Path
from PIL import Image

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

# Import Hunyuan3D
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig

# Load multi-view images
images = sorted(Path('.').glob('examples/input_images/multi_view/frame_*_4x.png'))[:10]
pil_images = [Image.open(img).convert("RGB") for img in images]
print(f"Loaded {len(pil_images)} images")

# Create output dir
Path("test_out").mkdir(exist_ok=True)

# Step 1: Generate shape
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

mesh.export("test_out/mesh.obj")
print("Saved: test_out/mesh.obj")

# Step 2: Paint textures with Blender
print("Loading paint model...")
paint_config = Hunyuan3DPaintConfig(
    max_num_view=len(pil_images),
    resolution=512
)
paint_pipeline = Hunyuan3DPaintPipeline(paint_config)

# Save temp reference images
refs = []
for i, img in enumerate(pil_images):
    path = f"test_out/ref_{i}.png"
    img.save(path)
    refs.append(path)

print("Painting textures with Blender...")
textured = paint_pipeline(
    mesh_path="test_out/mesh.obj",
    image_path=refs,
    output_dir="test_out",
    num_inference_steps=50,
    multi_view=True
)

textured.export("test_out/final.glb")
print("Done! Output: test_out/final.glb")