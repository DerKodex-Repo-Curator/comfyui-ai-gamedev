"""
Unified Hunyuan3D 2.1 node for ComfyUI
Handles both shape generation and texture painting in one node
"""

import torch
import numpy as np
import uuid
import json
import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional
from PIL import Image
import folder_paths
import trimesh

# ComfyUI MESH type
try:
    from .mesh_types import MESH
except ImportError:
    # Define MESH class if not available
    class MESH:
        def __init__(self, vertices: torch.Tensor, faces: torch.Tensor):
            self.vertices = vertices  # [B, V, 3]
            self.faces = faces        # [B, F, 3]

from .utils.conda_runner import CondaRunner

class Hunyuan3D21UnifiedNode:
    """
    Unified Hunyuan3D 2.1 node for shape generation and texture painting
    
    Combines shape generation and optional texture painting in a single node.
    Texture painting requires Blender installation.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # Can be single or batch for multi-view
                "enable_texture": ("BOOLEAN", {"default": True}),
                "resolution": (["256", "512", "1024"], {"default": "512"}),
                "texture_resolution": (["512", "1024", "2048"], {"default": "1024"}),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.5
                }),
                "shape_steps": ("INT", {
                    "default": 50,
                    "min": 1,
                    "max": 200,
                    "step": 1
                }),
                "texture_steps": ("INT", {
                    "default": 50,
                    "min": 1,
                    "max": 200,
                    "step": 1
                }),
            },
            "optional": {
                "seed": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            }
        }
    
    RETURN_TYPES = (
        "MESH",          # 3D mesh (textured if enabled)
        "STRING",        # Path to GLB file
        "STRING",        # Path to OBJ file
        "STRING",        # Path to STL file
    )
    
    RETURN_NAMES = (
        "mesh",
        "glb_filepath",
        "obj_filepath",
        "stl_filepath",
    )
    
    FUNCTION = "generate_3d"
    CATEGORY = "🎮 AI GameDev/3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Save to ComfyUI output/mesh directory
        output_dir = Path(folder_paths.get_output_directory())
        self.output_dir = output_dir / "mesh"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conda_runner = CondaRunner()
        
        # Check environment on init
        if not self.conda_runner.check_environment():
            print(f"⚠️  Warning: Conda environment '{self.conda_runner.env_name}' not properly configured")
            print("   Please run: python install.py")
            print(f"   Or set HUNYUAN3D_CONDA_ENV environment variable to your conda env name")
        
        # Setup model paths
        from .utils.model_paths import setup_model_env, get_model_paths
        paths = setup_model_env()
        if paths.get("shape_model"):
            print(f"✅ Using shape model from ComfyUI: {paths['shape_model']}")
        else:
            print("📌 Using shape model from HuggingFace cache")
        
        # Check if Blender is installed for texture painting
        import subprocess
        self.blender_available = False
        try:
            result = subprocess.run(['blender', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.blender_available = True
                print(f"✅ Blender found: texture painting available")
            else:
                print("⚠️  Blender not found - texture painting disabled")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Blender not found - texture painting will be skipped")
            print("   Install Blender for texture support: sudo apt install blender")
    
    def generate_3d(
        self,
        images: torch.Tensor,
        enable_texture: bool,
        resolution: str,
        texture_resolution: str,
        guidance_scale: float,
        shape_steps: int,
        texture_steps: int,
        seed: int = -1,
        **kwargs
    ) -> Tuple[Any, str, str, str]:
        """
        Generate 3D model with optional texture painting
        
        Args:
            images: Input image(s) tensor [B, H, W, C]
            enable_texture: Whether to apply texture painting
            resolution: Shape generation resolution
            texture_resolution: Texture painting resolution
            guidance_scale: Diffusion guidance scale
            shape_steps: Number of diffusion steps for shape
            texture_steps: Number of steps for texture painting
            seed: Random seed (-1 for random)
            
        Returns:
            Tuple of (mesh, glb_filepath, obj_filepath, stl_filepath)
        """
        
        # Multi-view is automatic based on image count (1-10 images)
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        is_multi_view = batch_size > 1 and batch_size <= 10
        
        print(f"\n{'='*60}")
        print(f"🎮 HUNYUAN3D 2.1 GENERATION")
        print(f"{'='*60}")
        print(f"  📷 Input: {batch_size} image(s)")
        print(f"  📐 Shape resolution: {resolution}")
        print(f"  🎨 Texture: {'Enabled' if enable_texture and self.blender_available else 'Disabled'}")
        if enable_texture and self.blender_available:
            print(f"  📐 Texture resolution: {texture_resolution}")
        print(f"  🎯 Guidance scale: {guidance_scale}")
        print(f"  👀 Multi-view: {is_multi_view}")
        print(f"{'='*60}\n")
        
        # Generate base shape
        print("🔨 Phase 1: Shape Generation")
        print("-" * 40)
        base_mesh = self._generate_shape(
            images=images,
            resolution=int(resolution),
            guidance_scale=guidance_scale,
            steps=shape_steps,
            is_multi_view=is_multi_view,
            seed=seed
        )
        
        if not base_mesh or not base_mesh.get("path"):
            print("❌ Shape generation failed")
            return (None, "", "", "")
        
        # Load the OBJ file
        obj_path = base_mesh["path"]
        tm_mesh = trimesh.load(obj_path)
        
        # Generate additional formats
        glb_path = self._export_format(tm_mesh, obj_path, "glb")
        stl_path = self._export_format(tm_mesh, obj_path, "stl")
        
        # Apply texture if enabled and Blender is available
        final_glb = glb_path
        if enable_texture and self.blender_available:
            print("\n🎨 Phase 2: Texture Painting")
            print("-" * 40)
            
            textured = self._apply_texture(
                mesh_path=obj_path,
                images=images,
                resolution=int(texture_resolution),
                steps=texture_steps
            )
            
            if textured and textured.get("path"):
                final_glb = textured["path"]
                # Reload the textured mesh
                tm_mesh = trimesh.load(final_glb)
        elif enable_texture and not self.blender_available:
            print("\n⚠️  Texture painting skipped - Blender not available")
        
        # Convert to MESH object
        vertices = torch.from_numpy(tm_mesh.vertices).float().unsqueeze(0)
        faces = torch.from_numpy(tm_mesh.faces).long().unsqueeze(0)
        mesh = MESH(vertices, faces)
        
        print(f"\n{'='*60}")
        print(f"✅ GENERATION COMPLETE")
        print(f"  📦 Mesh: {vertices.shape[1]} vertices, {faces.shape[1]} faces")
        print(f"  📁 Files generated:")
        print(f"     GLB: {Path(final_glb).name}")
        print(f"     OBJ: {Path(obj_path).name}")
        print(f"     STL: {Path(stl_path).name}")
        print(f"{'='*60}\n")
        
        return (mesh, final_glb, obj_path, stl_path)
    
    def _generate_shape(self, images, resolution, guidance_scale, steps, is_multi_view, seed):
        """Generate 3D shape using Hunyuan3D model"""
        # Save images to temp files
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"input_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Output path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_mesh = self.output_dir / f"hunyuan3d_{timestamp}_{run_id}.obj"
        
        # Create execution script
        script = self._create_shape_script(
            image_paths=image_paths,
            output_mesh=str(output_mesh),
            resolution=resolution,
            guidance_scale=guidance_scale,
            steps=steps,
            is_multi_view=is_multi_view,
            seed=seed if seed != -1 else None
        )
        
        script_path = self.output_dir / f"generate_shape_{run_id}.py"
        script_path.write_text(script)
        
        print(f"  ⏳ Generating shape (this may take 2-5 minutes)...")
        success = self.conda_runner.execute_script(script_path, timeout=300)
        
        # Clean up
        script_path.unlink(missing_ok=True)
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        if success and output_mesh.exists():
            size_mb = output_mesh.stat().st_size / (1024 * 1024)
            print(f"  ✅ Shape generated: {output_mesh.name} ({size_mb:.2f} MB)")
            return {"path": str(output_mesh), "type": "obj"}
        else:
            return None
    
    def _apply_texture(self, mesh_path, images, resolution, steps):
        """Apply texture using Blender and Hunyuan3D painting"""
        # Save reference images
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"tex_ref_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Output path
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_glb = self.output_dir / f"hunyuan3d_textured_{timestamp}_{run_id}.glb"
        
        # Use permanent paint script
        script_path = Path(__file__).parent / "scripts" / "paint_texture.py"
        
        print(f"  ⏳ Painting texture (this may take 3-7 minutes)...")
        
        # Run painting with arguments
        success = self.conda_runner.execute_in_blender_with_args(
            script_path, 
            args=[
                "--mesh", mesh_path,
                "--images", json.dumps(image_paths),
                "--output", str(output_glb),
                "--resolution", str(resolution),
                "--steps", str(steps)
            ],
            timeout=600,
            output_file=output_glb
        )
        
        # Clean up temp files
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        if output_glb.exists():
            size_mb = output_glb.stat().st_size / (1024 * 1024)
            print(f"  ✅ Texture applied: {output_glb.name} ({size_mb:.2f} MB)")
            return {"path": str(output_glb), "type": "glb", "has_texture": True}
        else:
            print(f"  ⚠️ Texture painting failed, using untextured mesh")
            return None
    
    def _export_format(self, trimesh_obj, base_path, format):
        """Export mesh to different format"""
        base_path = Path(base_path)
        output_path = base_path.with_suffix(f".{format}")
        
        try:
            trimesh_obj.export(str(output_path), file_type=format)
            if output_path.exists():
                return str(output_path)
        except Exception as e:
            print(f"  ⚠️ Failed to export {format}: {e}")
        
        return ""
    
    def _create_shape_script(self, image_paths, output_mesh, resolution, 
                           guidance_scale, steps, is_multi_view, seed):
        """Create script for shape generation"""
        image_paths_str = json.dumps(image_paths)
        
        return f"""
import sys
import os
import torch
from pathlib import Path
from PIL import Image

# Use offline mode
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')

from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline

# Load images
image_paths = {image_paths_str}
pil_images = [Image.open(p).convert("RGB") for p in image_paths]

{f"torch.manual_seed({seed})" if seed else ""}

print("Loading shape generation model...")
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1',
    subfolder='hunyuan3d-dit-v2-1',
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map='auto'
)

print(f"Generating 3D shape from {{len(pil_images)}} images...")
mesh = shape_pipeline(
    image=pil_images if len(pil_images) > 1 else pil_images[0],
    num_inference_steps={steps},
    guidance_scale={guidance_scale},
    resolution={resolution},
    {"multi_view=True" if is_multi_view else ""}
)[0]

# Save mesh
mesh.export("{output_mesh}")
print(f"Saved mesh: {output_mesh}")
"""
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")