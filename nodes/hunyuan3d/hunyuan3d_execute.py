#!/usr/bin/env python3
"""
Hunyuan3D 2.1 execution script with structured logging
MUST BE RUN THROUGH BLENDER: conda run -n hunyuan3d blender --background --python hunyuan3d_execute.py -- config.json
Note: Blender may segfault during cleanup - this is expected after successful generation
"""

print("starting...")

# Note: Blender segfault during cleanup is a known issue - files are generated successfully before crash

# Apply addon cleanup fix for clean Blender exit
def fix_blender_addon_cleanup():
    """Fix Blender addon cleanup: Replace non-callable unregister objects with callable mocks"""
    try:
        import sys
        fixed_count = 0
        problematic_modules = []
        all_unregister_modules = []
        
        for module_name, module in sys.modules.items():
            if module and hasattr(module, 'unregister'):
                all_unregister_modules.append(f"{module_name} ({type(module.unregister).__name__})")
                if not callable(module.unregister):
                    # Store original for debugging
                    original_type = type(module.unregister).__name__
                    try:
                        original_value = str(module.unregister)[:100]
                    except Exception as e:
                        original_value = f"<Error getting string repr: {e}>"
                    problematic_modules.append(f"{module_name} ({original_type}): {original_value}")
                    
                    # Create a proper mock function with closure to capture module name
                    def create_mock_unregister(name, orig_type):
                        def mock_unregister():
                            # Silent mock for known problematic types
                            pass
                        return mock_unregister
                    
                    # Replace with mock
                    module.unregister = create_mock_unregister(module_name, original_type)
                    fixed_count += 1
        
        print(f"🔍 Found {len(all_unregister_modules)} modules with unregister attribute:")
        for mod in all_unregister_modules:
            print(f"    - {mod}")
        
        if fixed_count > 0:
            print(f"🔧 Fixed {fixed_count} problematic addon unregister functions:")
            for mod in problematic_modules:
                print(f"    - {mod}")
        else:
            print("ℹ️ No problematic addon unregister functions found")
            
    except Exception as e:
        print(f"⚠️ Addon cleanup fix error: {e}")
        import traceback
        traceback.print_exc()

# Comprehensive segfault prevention strategy
import atexit
import signal

def aggressive_blender_cleanup():
    """Aggressive cleanup strategy that applies multiple fixes"""
    print("🔄 Running aggressive Blender cleanup...")
    
    # Apply our addon fix
    fix_blender_addon_cleanup()
    
    # Monkeypatch the actual Blender cleanup mechanism
    try:
        import addon_utils
        original_disable = addon_utils.disable
        
        def safe_disable(module_name, default_set=False, handle_error=None):
            """Safe version of addon_utils.disable that catches errors"""
            try:
                return original_disable(module_name, default_set, handle_error)
            except Exception as e:
                print(f"⚠️ Caught addon disable error for {module_name}: {e}")
                return None
        
        addon_utils.disable = safe_disable
        print("✓ Monkeypatched addon_utils.disable")
    except Exception as e:
        print(f"⚠️ Could not monkeypatch addon_utils: {e}")
    
    # Try to clear Blender state
    try:
        import bpy
        # Disable all addons first
        try:
            enabled_addons = list(bpy.context.preferences.addons.keys())
            for addon in enabled_addons:
                try:
                    bpy.ops.preferences.addon_disable(module=addon)
                except:
                    pass
        except:
            pass
        print("✓ Disabled all addons")
    except Exception as e:
        print(f"⚠️ Could not clear Blender state: {e}")

def exit_handler():
    """Exit handler that runs aggressive cleanup"""
    aggressive_blender_cleanup()

def signal_handler(signum, frame):
    """Signal handler for clean exit"""
    print(f"🔔 Received signal {signum}")
    aggressive_blender_cleanup()
    exit(0)

# Register multiple cleanup strategies
atexit.register(exit_handler)

# Register signal handlers
try:
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    print("✓ Registered signal handlers")
except:
    pass

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

# Import our progress tracking utilities
sys.path.insert(0, str(Path(__file__).parent))
from progress_utils import create_progress_tracker, STAGE_ESTIMATES
from progress_monitoring import monitor_pipeline_progress

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

# Initialize progress tracking with raw logging to file and real-time progress file
output_dir = Path(config['output_dir'])
log_file_path = output_dir / "hunyuan3d_execution.log"
progress_file_path = output_dir / "progress.jsonl"
progress_tracker = create_progress_tracker(str(log_file_path), str(progress_file_path))

# Start progress tracking
progress_tracker.update_progress(
    stage="starting", 
    percent=0, 
    message="Initializing Hunyuan3D execution", 
    estimated_total=STAGE_ESTIMATES["total"]
)
progress_tracker.log_raw("Script starting with structured logging", "info")

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

# Torchvision fix already applied at the beginning (like demo.py)

# No seed setting - removed for consistent generation

# Load images
print("Loading images...")
image_paths = config['image_paths']
print(f"Image paths: {image_paths}")
images = []
for i, p in enumerate(image_paths):
    print(f"  Loading image {i+1}/{len(image_paths)}: {p}")
    img = Image.open(p).convert("RGB")
    images.append(img)
    print(f"    Size: {img.size}")
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

# Print and log directory information
print(f"\n📁 Directory Setup:")
print(f"  Original directory: {original_cwd}")
print(f"  Working directory: {os.getcwd()}")
print(f"  Output directory: {output_dir}")
print(f"  Output directory exists: {output_dir.exists()}")
print(f"  Output files will be:")
print(f"    - {textured_glb_path.name}")
print(f"    - {textured_obj_path.name}")
print(f"    - {textured_stl_path.name}")

progress_tracker.log_raw(f"Directory setup complete - working dir: {os.getcwd()}, output dir: {output_dir}", "info")

print("\n" + "="*60)
print("🎮 HUNYUAN3D 2.1 GENERATION")
print("="*60)

# Use progress monitoring context for the entire generation process
with monitor_pipeline_progress(progress_tracker) as progress_monitor:
    # Step 1: Generate shape (exactly like test_minimal.py)
    print("\n🔨 Step 1: Shape Generation")
    print("-" * 40)

    # Progress: Starting shape generation
    progress_monitor.start_stage("shape_generation", "Loading 3D shape generation model")

    print("Loading pretrained model...")
    progress_tracker.log_raw("Loading shape generation model", "info")
    shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        'tencent/Hunyuan3D-2.1', 
        subfolder='hunyuan3d-dit-v2-1'
    )
    print("✓ Model loaded")
    progress_tracker.log_raw("Shape generation model loaded successfully", "info")

    # Progress: Model loaded, starting generation
    progress_monitor.update_stage_progress(
        stage="shape_generation", 
        substep_percent=20, 
        message=f"Generating 3D shape with {config['inference_steps']} steps"
    )

    print(f"Generating shape with {config['inference_steps']} steps...")
    progress_tracker.log_raw(f"Starting shape generation with {config['inference_steps']} steps", "info")

    # Set up progress callback for shape generation
    shape_callback = progress_monitor.monitor_shape_generation(
        pipeline=shape_pipeline,
        total_steps=config['inference_steps']
    )

    result = shape_pipeline(
        image=images if len(images) > 1 else images[0],
        num_inference_steps=config['inference_steps'],
        guidance_scale=config['guidance_scale'],
        resolution=config['resolution'],
        callback_on_step_end=shape_callback
    )
    
    progress_tracker.log_raw("Shape generation pipeline execution completed", "info")

    if result is None or len(result) == 0 or result[0] is None:
        print("❌ Shape generation failed - no mesh returned")
        progress_tracker.log_raw("Shape generation failed - no mesh returned", "error")
        sys.exit(1)

    mesh = result[0]
    print("✓ Shape generated")
    progress_tracker.log_raw("Shape mesh generated successfully", "info")

    # Progress: Shape generation complete (50% total progress)
    progress_monitor.complete_stage("shape_generation", "3D shape generation completed successfully")
    
    # Save logs after shape generation
    progress_tracker.save_raw_logs()

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

    # Progress: Starting texture painting
    progress_monitor.start_stage("texture_painting", "Initializing texture painting pipeline")

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
        progress_tracker.log_raw("Initializing texture painting pipeline", "info")
        paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
        print("✓ Paint pipeline initialized")
        progress_tracker.log_raw("Texture painting pipeline initialized successfully", "info")
        
        # Save logs after initialization
        progress_tracker.save_raw_logs()
        
        # Get the actual progress callback for texture painting
        texture_callback = progress_monitor.monitor_texture_painting(paint_pipeline)
        
        # Monkey-patch the forward_one method directly (since __call__ just calls forward_one)
        multiview_model = paint_pipeline.models["multiview_model"]
        original_forward_one = multiview_model.forward_one
        
        def patched_forward_one(self, input_images, control_images, prompt=None, custom_view_size=None, resize_input=False):
            self.seed_everything(0)
            custom_view_size = custom_view_size if custom_view_size is not None else self.pipeline.view_size
            if not isinstance(input_images, list):
                input_images = [input_images]
            if not resize_input:
                input_images = [
                    input_image.resize((self.pipeline.view_size, self.pipeline.view_size)) for input_image in input_images
                ]
            else:
                input_images = [input_image.resize((custom_view_size, custom_view_size)) for input_image in input_images]
            for i in range(len(control_images)):
                control_images[i] = control_images[i].resize((custom_view_size, custom_view_size))
                if control_images[i].mode == "L":
                    control_images[i] = control_images[i].point(lambda x: 255 if x > 1 else 0, mode="1")
            kwargs = dict(generator=torch.Generator(device=self.pipeline.device).manual_seed(0))

            num_view = len(control_images) // 2
            normal_image = [[control_images[i] for i in range(num_view)]]
            position_image = [[control_images[i + num_view] for i in range(num_view)]]

            kwargs["width"] = custom_view_size
            kwargs["height"] = custom_view_size
            kwargs["num_in_batch"] = num_view
            kwargs["images_normal"] = normal_image
            kwargs["images_position"] = position_image

            if hasattr(self.pipeline.unet, "use_dino") and self.pipeline.unet.use_dino:
                dino_hidden_states = self.dino_v2(input_images[0])
                kwargs["dino_hidden_states"] = dino_hidden_states

            sync_condition = None

            infer_steps_dict = {
                "EulerAncestralDiscreteScheduler": 30,
                "UniPCMultistepScheduler": 15,
                "DDIMScheduler": 50,
                "ShiftSNRScheduler": 15,
            }

            # Add the real progress callback for texture painting
            kwargs["callback_on_step_end"] = texture_callback

            mvd_image = self.pipeline(
                input_images[0:1],
                num_inference_steps=infer_steps_dict[self.pipeline.scheduler.__class__.__name__],
                prompt=prompt,
                sync_condition=sync_condition,
                guidance_scale=3.0,
                **kwargs,
            ).images

            if "pbr" in self.mode:
                mvd_image = {"albedo": mvd_image[:num_view], "mr": mvd_image[num_view:]}
            else:
                mvd_image = {"hdr": mvd_image}

            return mvd_image
        
        # Apply the monkey patch to forward_one directly
        import types
        multiview_model.forward_one = types.MethodType(patched_forward_one, multiview_model)
        
        # Paint texture (returns path to textured OBJ)
        print(f"Painting texture with progress monitoring...")
        progress_tracker.log_raw(f"Starting texture painting process", "info")
        
        textured_result = paint_pipeline(
            str(shape_path),
            image_path=image_paths[0],  # Pass single image to avoid bug
        )
        
        print(f"✅ Texture painting complete: {textured_result}")
        progress_tracker.log_raw(f"Texture painting completed successfully: {textured_result}", "info")
        
        # Progress: Texture painting complete
        progress_monitor.complete_stage("texture_painting", "Texture painting completed successfully")
        
        # Convert to GLB using trimesh (like test_minimal.py)
        print("\n📦 Step 3: Exporting Formats")
        print("-" * 40)
        
        # Progress: Starting export
        progress_monitor.start_stage("exporting", "Exporting 3D models to GLB, OBJ, and STL formats")
        
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
        progress_tracker.log_raw(f"Texture painting failed with error: {e}", "error")
        import traceback
        error_traceback = traceback.format_exc()
        print(error_traceback)
        progress_tracker.log_raw(f"Texture painting traceback: {error_traceback}", "error")
        
        # Save logs before exiting
        progress_tracker.save_raw_logs()
        sys.exit(1)  # Complete failure - no recovery

    # Clean up temporary shape file
    try:
        shape_path.unlink(missing_ok=True)
        print("✓ Cleaned up temporary files")
    except:
        pass

    # Progress: Complete!
    progress_monitor.complete_stage("complete", "Hunyuan3D generation completed successfully")

print("\n" + "="*60)
print("✅ GENERATION COMPLETE")
print(f"   GLB: {textured_glb_path.name if textured_glb_path.exists() else 'Not created'}")
print(f"   OBJ: {textured_obj_path.name if textured_obj_path.exists() else 'Not created'}")
print(f"   STL: {textured_stl_path.name if textured_stl_path.exists() else 'Not created'}")
print("="*60)

# Apply aggressive cleanup before exit
print("🔧 Applying aggressive cleanup before exit...")
aggressive_blender_cleanup()

# Save final log file
progress_tracker.save_raw_logs()
print("Script complete. Blender should exit cleanly.")