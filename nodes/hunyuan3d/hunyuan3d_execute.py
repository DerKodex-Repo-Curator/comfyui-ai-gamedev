#!/usr/bin/env python3
"""
Hunyuan3D 2.1 execution script - based on working test_minimal.py
MUST BE RUN THROUGH BLENDER: conda run -n hunyuan3d blender --background --python hunyuan3d_execute.py -- config.json
"""

print("starting...")

print("=" * 60)
print("SCRIPT STARTING")
print("=" * 60)

import sys
print(f"Python: {sys.version}")
print(f"Executable: {sys.executable}")

import os
print(f"Current dir: {os.getcwd()}")

import json
from pathlib import Path

# Use offline mode to avoid SSL issues
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
print("Set offline mode")

# Get config file from command line arguments
config_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[-1]
print(f"Config path: {config_path}")

# Load configuration
with open(config_path, 'r') as f:
    config = json.load(f)
print(f"Config loaded with keys: {list(config.keys())}")
print(f"Config contents:")
print(json.dumps(config, indent=2))

# Setup paths exactly like demo.py
print("Adding to sys.path...")
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')
print(f"sys.path updated")

print("Importing PIL...")
from PIL import Image
print("✓ PIL imported")

print("Importing torch...")
import torch
print("✓ torch imported")

# Apply torchvision fix BEFORE importing pipelines (like demo.py)
print("Applying torchvision fix...")
try:
    from torchvision_fix import apply_fix
    apply_fix()
    print("✓ Torchvision fix applied")
except ImportError:
    print("Warning: torchvision_fix module not found, proceeding without compatibility fix")
except Exception as e:
    print(f"Warning: Failed to apply torchvision fix: {e}")

print("Importing Hunyuan3D shape pipeline...")
print(f"  sys.path[0]: {sys.path[0]}")
print(f"  sys.path[1]: {sys.path[1]}")
print(f"  sys.path[2]: {sys.path[2]}")

# Check if the module exists before importing
import importlib.util
spec = importlib.util.find_spec('hy3dshape')
print(f"  hy3dshape spec: {spec}")
if spec:
    print(f"  hy3dshape location: {spec.origin}")

print("  About to import hy3dshape.pipelines...")
sys.stdout.flush()
sys.stderr.flush()

try:
    import hy3dshape
    print(f"  ✓ hy3dshape module imported")
    print(f"  hy3dshape.__file__: {hy3dshape.__file__}")
except Exception as e:
    print(f"  ❌ Failed to import hy3dshape: {e}")
    sys.exit(1)

try:
    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
    print("✓ Shape pipeline imported")
except Exception as e:
    print(f"❌ Failed to import pipeline: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Importing texture pipeline...")
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
print("✓ Texture pipeline imported")

# Apply fix for image_path bug in texture pipeline
print("Applying texture pipeline fix...")
sys.path.insert(0, str(Path(__file__).parent))
from texture_pipeline_fix import apply_texture_pipeline_fix
apply_texture_pipeline_fix()

# Torchvision fix already applied at the beginning (like demo.py)

# No seed setting - removed for consistent generation

# Load images
print("Loading images...")
image_paths = config['image_paths']
print(f"Image paths: {image_paths}")
images = [Image.open(p).convert("RGB") for p in image_paths]
print(f"✓ Loaded {len(images)} images")

# Output paths
output_dir = Path(config['output_dir'])
output_dir.mkdir(parents=True, exist_ok=True)

# Change to output directory so all temp files go there
original_cwd = os.getcwd()
os.chdir(str(output_dir))
print(f"Changed working directory to: {os.getcwd()}")

base_name = config['base_name']
shape_path = output_dir / f"{base_name}_shape.obj"
textured_glb_path = output_dir / f"{base_name}_textured.glb"
textured_obj_path = output_dir / f"{base_name}_textured.obj"
textured_stl_path = output_dir / f"{base_name}_textured.stl"

# Print directory information
print(f"\n📁 Directory Setup:")
print(f"  Original directory: {original_cwd}")
print(f"  Working directory: {os.getcwd()}")
print(f"  Output directory: {output_dir}")
print(f"  Output directory exists: {output_dir.exists()}")
print(f"  Output files will be:")
print(f"    - {textured_glb_path.name}")
print(f"    - {textured_obj_path.name}")
print(f"    - {textured_stl_path.name}")

print("\n" + "="*60)
print("🎮 HUNYUAN3D 2.1 GENERATION")
print("="*60)

# Step 1: Generate shape (exactly like test_minimal.py)
print("\n🔨 Step 1: Shape Generation")
print("-" * 40)

print("Loading pretrained model...")
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1', 
    subfolder='hunyuan3d-dit-v2-1'
)
print("✓ Model loaded")

print(f"Generating shape with {config['inference_steps']} steps...")
result = shape_pipeline(
    image=images if len(images) > 1 else images[0],
    num_inference_steps=config['inference_steps'],
    guidance_scale=config['guidance_scale'],
    resolution=config['resolution']
)

if result is None or len(result) == 0 or result[0] is None:
    print("❌ Shape generation failed - no mesh returned")
    sys.exit(1)

mesh = result[0]
print("✓ Shape generated")

# Save shape as OBJ first (like test_minimal.py)
print(f"Saving shape to {shape_path}...")
mesh.export(str(shape_path))
print(f"✅ Shape saved: {shape_path.name}")

# Free up memory from shape pipeline before texture painting
print("\n♻️ Freeing shape generation memory...")
del shape_pipeline
del result
import gc
gc.collect()
torch.cuda.empty_cache()
print("✓ Memory freed")

# Step 2: Paint texture (exactly like test_minimal.py)
print("\n🎨 Step 2: Texture Painting")
print("-" * 40)

try:
    print("Importing trimesh...")
    import trimesh
    print("✓ Trimesh imported")
    
    # Configure texture painting
    max_num_view = len(images)
    print(f"Configuring paint with {max_num_view} views, resolution {config['texture_resolution']}...")
    paint_config = Hunyuan3DPaintConfig(max_num_view, config['texture_resolution'])
    
    # Set absolute paths for all required files
    # Use the original working directory before we changed to output_dir
    project_root = Path(original_cwd)  # Use the original cwd which is the project root
    paint_config.realesrgan_ckpt_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth")
    paint_config.multiview_cfg_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml")
    paint_config.custom_pipeline = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr")
    print("✓ Paint config set with absolute paths:")
    print(f"    RealESRGAN: {paint_config.realesrgan_ckpt_path}")
    print(f"    Config: {paint_config.multiview_cfg_path}")
    print(f"    Pipeline: {paint_config.custom_pipeline}")
    
    # Initialize paint pipeline
    print("Initializing paint pipeline...")
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    print("✓ Paint pipeline initialized")
    
    # Paint texture (returns path to textured OBJ)
    print(f"Painting texture...")
    # Paint pipeline can accept list of image paths for multi-view texture painting
    # Pass all image paths for better texture quality
    textured_result = paint_pipeline(
        str(shape_path),
        image_path=image_paths if len(image_paths) > 1 else image_paths[0],  # List for multi-view, single for single-view
    )
    
    print(f"✅ Texture painting complete: {textured_result}")
    
    # Convert to GLB using trimesh (like test_minimal.py)
    print("\n📦 Step 3: Exporting Formats")
    print("-" * 40)
    
    print(f"Loading textured mesh from {textured_result}...")
    mesh_textured = trimesh.load(textured_result)
    print("✓ Textured mesh loaded")
    
    # Export GLB
    print(f"Exporting GLB to {textured_glb_path}...")
    mesh_textured.export(str(textured_glb_path))
    print(f"✅ GLB exported: {textured_glb_path.name}")
    
    # Export OBJ
    print(f"Exporting OBJ to {textured_obj_path}...")
    mesh_textured.export(str(textured_obj_path))
    print(f"✅ OBJ exported: {textured_obj_path.name}")
    
    # Export STL
    print(f"Exporting STL to {textured_stl_path}...")
    mesh_textured.export(str(textured_stl_path))
    print(f"✅ STL exported: {textured_stl_path.name}")
    
except Exception as e:
    print(f"❌ Texture painting failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)  # Complete failure - no recovery

# Clean up temporary shape file
try:
    shape_path.unlink(missing_ok=True)
    print("✓ Cleaned up temporary files")
except:
    pass

print("\n" + "="*60)
print("✅ GENERATION COMPLETE")
print(f"   GLB: {textured_glb_path.name if textured_glb_path.exists() else 'Not created'}")
print(f"   OBJ: {textured_obj_path.name if textured_obj_path.exists() else 'Not created'}")
print(f"   STL: {textured_stl_path.name if textured_stl_path.exists() else 'Not created'}")
print("="*60)

# Script may segfault here - that's OK, files are already saved
print("Script complete. Blender may crash now - this is expected.")