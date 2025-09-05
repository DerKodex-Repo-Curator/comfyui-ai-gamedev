#!/usr/bin/env python3
"""
Hunyuan3D 2.1 execution script - based on working test_minimal.py
MUST BE RUN THROUGH BLENDER: conda run -n hunyuan3d blender --background --python hunyuan3d_execute.py -- config.json
"""

print("starting...")

print("=" * 60, flush=True)
print("SCRIPT STARTING", flush=True)
print("=" * 60, flush=True)

import sys
print(f"Python: {sys.version}", flush=True)
print(f"Executable: {sys.executable}", flush=True)

import os
print(f"Current dir: {os.getcwd()}", flush=True)

import json
from pathlib import Path

# Use offline mode to avoid SSL issues
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
print("Set offline mode", flush=True)

# Get config file from command line arguments
config_path = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[-1]
print(f"Config path: {config_path}", flush=True)

# Load configuration
with open(config_path, 'r') as f:
    config = json.load(f)
print(f"Config loaded with keys: {list(config.keys())}", flush=True)
print(f"Config contents:", flush=True)
print(json.dumps(config, indent=2), flush=True)

# Setup paths exactly like demo.py
print("Adding to sys.path...", flush=True)
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')
print(f"sys.path updated", flush=True)

print("Importing PIL...", flush=True)
from PIL import Image
print("✓ PIL imported", flush=True)

# Apply torchvision fix BEFORE importing pipelines (like demo.py)
print("Applying torchvision fix...", flush=True)
try:
    from torchvision_fix import apply_fix
    apply_fix()
    print("✓ Torchvision fix applied", flush=True)
except ImportError:
    print("Warning: torchvision_fix module not found, proceeding without compatibility fix", flush=True)
except Exception as e:
    print(f"Warning: Failed to apply torchvision fix: {e}", flush=True)

print("Importing Hunyuan3D shape pipeline...", flush=True)
print(f"  sys.path[0]: {sys.path[0]}", flush=True)
print(f"  sys.path[1]: {sys.path[1]}", flush=True)
print(f"  sys.path[2]: {sys.path[2]}", flush=True)

# Check if the module exists before importing
import importlib.util
spec = importlib.util.find_spec('hy3dshape')
print(f"  hy3dshape spec: {spec}", flush=True)
if spec:
    print(f"  hy3dshape location: {spec.origin}", flush=True)

print("  About to import hy3dshape.pipelines...", flush=True)
sys.stdout.flush()
sys.stderr.flush()

try:
    import hy3dshape
    print(f"  ✓ hy3dshape module imported", flush=True)
    print(f"  hy3dshape.__file__: {hy3dshape.__file__}", flush=True)
except Exception as e:
    print(f"  ❌ Failed to import hy3dshape: {e}", flush=True)
    sys.exit(1)

try:
    from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
    print("✓ Shape pipeline imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import pipeline: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Importing texture pipeline...", flush=True)
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
print("✓ Texture pipeline imported", flush=True)

# Torchvision fix already applied at the beginning (like demo.py)

# Set seed if provided
if config.get('seed'):
    print(f"Setting seed to {config['seed']}...", flush=True)
    import torch
    torch.manual_seed(config['seed'])
    print("✓ Seed set", flush=True)

# Load images
print("Loading images...", flush=True)
image_paths = config['image_paths']
print(f"Image paths: {image_paths}", flush=True)
images = [Image.open(p).convert("RGB") for p in image_paths]
print(f"✓ Loaded {len(images)} images", flush=True)

# Output paths
output_dir = Path(config['output_dir'])
output_dir.mkdir(parents=True, exist_ok=True)
base_name = config['base_name']
shape_path = output_dir / f"{base_name}_shape.obj"
textured_glb_path = output_dir / f"{base_name}_textured.glb"
textured_obj_path = output_dir / f"{base_name}_textured.obj"
textured_stl_path = output_dir / f"{base_name}_textured.stl"
print(f"Output directory: {output_dir}", flush=True)

print("\n" + "="*60, flush=True)
print("🎮 HUNYUAN3D 2.1 GENERATION", flush=True)
print("="*60, flush=True)

# Step 1: Generate shape (exactly like test_minimal.py)
print("\n🔨 Step 1: Shape Generation", flush=True)
print("-" * 40, flush=True)

print("Loading pretrained model...", flush=True)
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1', 
    subfolder='hunyuan3d-dit-v2-1'
)
print("✓ Model loaded", flush=True)

print(f"Generating shape with {config['inference_steps']} steps...", flush=True)
result = shape_pipeline(
    image=images if len(images) > 1 else images[0],
    num_inference_steps=config['inference_steps'],
    guidance_scale=config['guidance_scale'],
    resolution=config['resolution']
)

if result is None or len(result) == 0 or result[0] is None:
    print("❌ Shape generation failed - no mesh returned", flush=True)
    sys.exit(1)

mesh = result[0]
print("✓ Shape generated", flush=True)

# Save shape as OBJ first (like test_minimal.py)
print(f"Saving shape to {shape_path}...", flush=True)
mesh.export(str(shape_path))
print(f"✅ Shape saved: {shape_path.name}", flush=True)

# Step 2: Paint texture (exactly like test_minimal.py)
print("\n🎨 Step 2: Texture Painting", flush=True)
print("-" * 40, flush=True)

try:
    print("Importing trimesh...", flush=True)
    import trimesh
    print("✓ Trimesh imported", flush=True)
    
    # Configure texture painting
    max_num_view = len(images)
    print(f"Configuring paint with {max_num_view} views, resolution {config['texture_resolution']}...", flush=True)
    paint_config = Hunyuan3DPaintConfig(max_num_view, config['texture_resolution'])
    
    # Set absolute paths for all required files (like test_minimal.py)
    # Use the actual working directory which is set to project root
    project_root = Path(os.getcwd())  # This is set to /home/matt/src/comfyui-ai-gamedev by the node
    paint_config.realesrgan_ckpt_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth")
    paint_config.multiview_cfg_path = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml")
    paint_config.custom_pipeline = str(project_root / "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr")
    print("✓ Paint config set", flush=True)
    
    # Initialize paint pipeline
    print("Initializing paint pipeline...", flush=True)
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    print("✓ Paint pipeline initialized", flush=True)
    
    # Paint texture (returns path to textured OBJ)
    print(f"Painting texture...", flush=True)
    textured_result = paint_pipeline(
        str(shape_path),
        image_path=image_paths if len(image_paths) > 1 else image_paths[0],
    )
    
    print(f"✅ Texture painting complete: {textured_result}", flush=True)
    
    # Convert to GLB using trimesh (like test_minimal.py)
    print("\n📦 Step 3: Exporting Formats", flush=True)
    print("-" * 40, flush=True)
    
    print(f"Loading textured mesh from {textured_result}...", flush=True)
    mesh_textured = trimesh.load(textured_result)
    print("✓ Textured mesh loaded", flush=True)
    
    # Export GLB
    print(f"Exporting GLB to {textured_glb_path}...", flush=True)
    mesh_textured.export(str(textured_glb_path))
    print(f"✅ GLB exported: {textured_glb_path.name}", flush=True)
    
    # Export OBJ
    print(f"Exporting OBJ to {textured_obj_path}...", flush=True)
    mesh_textured.export(str(textured_obj_path))
    print(f"✅ OBJ exported: {textured_obj_path.name}", flush=True)
    
    # Export STL
    print(f"Exporting STL to {textured_stl_path}...", flush=True)
    mesh_textured.export(str(textured_stl_path))
    print(f"✅ STL exported: {textured_stl_path.name}", flush=True)
    
except Exception as e:
    print(f"❌ Texture painting failed: {e}", flush=True)
    import traceback
    traceback.print_exc()
    
    # If texture fails, still export untextured mesh
    try:
        print("Attempting to export untextured mesh as fallback...", flush=True)
        import trimesh
        mesh_untextured = trimesh.load(str(shape_path))
        mesh_untextured.export(str(textured_glb_path))
        mesh_untextured.export(str(textured_obj_path))
        mesh_untextured.export(str(textured_stl_path))
        print("⚠️ Exported untextured mesh as fallback", flush=True)
    except:
        print("❌ Failed to export fallback", flush=True)

# Clean up temporary shape file
try:
    shape_path.unlink(missing_ok=True)
    print("✓ Cleaned up temporary files", flush=True)
except:
    pass

print("\n" + "="*60, flush=True)
print("✅ GENERATION COMPLETE", flush=True)
print(f"   GLB: {textured_glb_path.name if textured_glb_path.exists() else 'Not created'}", flush=True)
print(f"   OBJ: {textured_obj_path.name if textured_obj_path.exists() else 'Not created'}", flush=True)
print(f"   STL: {textured_stl_path.name if textured_stl_path.exists() else 'Not created'}", flush=True)
print("="*60, flush=True)

# Script may segfault here - that's OK, files are already saved
print("Script complete. Blender may crash now - this is expected.", flush=True)