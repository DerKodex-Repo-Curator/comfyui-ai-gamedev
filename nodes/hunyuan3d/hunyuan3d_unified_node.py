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
        
        # Generate 3D model with unified pipeline
        print("🔨 Generating 3D Model")
        print("-" * 40)
        
        output_glb = self._generate_3d_unified(
            images=images,
            enable_texture=enable_texture,
            resolution=int(resolution),
            texture_resolution=int(texture_resolution),
            guidance_scale=guidance_scale,
            shape_steps=shape_steps,
            texture_steps=texture_steps,
            is_multi_view=is_multi_view,
            seed=seed
        )
        
        if not output_glb:
            print("❌ 3D generation failed")
            return (None, "", "", "")
        
        # Load the generated mesh
        tm_mesh = trimesh.load(output_glb)
        
        # Export to other formats
        output_obj = str(Path(output_glb).with_suffix(".obj"))
        output_stl = str(Path(output_glb).with_suffix(".stl"))
        
        tm_mesh.export(output_obj)
        tm_mesh.export(output_stl)
        
        final_glb = output_glb
        final_obj = output_obj
        final_stl = output_stl
        
        # Convert to MESH object
        vertices = torch.from_numpy(tm_mesh.vertices).float().unsqueeze(0)
        faces = torch.from_numpy(tm_mesh.faces).long().unsqueeze(0)
        mesh = MESH(vertices, faces)
        
        print(f"\n{'='*60}")
        print(f"✅ GENERATION COMPLETE")
        print(f"  📦 Mesh: {vertices.shape[1]} vertices, {faces.shape[1]} faces")
        print(f"  📁 Files generated:")
        print(f"     GLB: {Path(final_glb).name}")
        print(f"     OBJ: {Path(final_obj).name}")
        print(f"     STL: {Path(final_stl).name}")
        print(f"{'='*60}\n")
        
        return (mesh, final_glb, final_obj, final_stl)
    
    def _generate_3d_unified(self, images, enable_texture, resolution, texture_resolution,
                            guidance_scale, shape_steps, texture_steps, is_multi_view, seed):
        """Generate 3D shape and texture in one unified process like demo.py"""
        # Save images to temp files
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"input_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Output paths
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if enable_texture and self.blender_available:
            output_glb = self.output_dir / f"hunyuan3d_textured_{timestamp}_{run_id}.glb"
        else:
            output_glb = self.output_dir / f"hunyuan3d_{timestamp}_{run_id}.glb"
        
        # Create unified script like demo.py
        script = self._create_unified_script(
            image_paths=image_paths,
            output_glb=str(output_glb),
            resolution=resolution,
            texture_resolution=texture_resolution,
            guidance_scale=guidance_scale,
            shape_steps=shape_steps,
            texture_steps=texture_steps,
            is_multi_view=is_multi_view,
            enable_texture=enable_texture and self.blender_available,
            seed=seed if seed != -1 else None
        )
        
        script_path = self.output_dir / f"generate_unified_{run_id}.py"
        script_path.write_text(script)
        
        print(f"  ⏳ Generating 3D model (this may take 5-10 minutes)...")
        
        # Run in Blender if texture is enabled, otherwise regular Python
        if enable_texture and self.blender_available:
            success = self.conda_runner.execute_in_blender(
                script_path, 
                timeout=600,
                output_file=output_glb
            )
        else:
            success = self.conda_runner.execute_script(script_path, timeout=600)
        
        # Clean up
        script_path.unlink(missing_ok=True)
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        if success and output_glb.exists():
            size_mb = output_glb.stat().st_size / (1024 * 1024)
            print(f"  ✅ Model generated: {output_glb.name} ({size_mb:.2f} MB)")
            return str(output_glb)
        else:
            print(f"  ❌ Generation failed - output file not created")
            return None
    
    def _create_unified_script(self, image_paths, output_glb, resolution, texture_resolution,
                              guidance_scale, shape_steps, texture_steps, is_multi_view, 
                              enable_texture, seed):
        """Create unified script like demo.py - shape and texture in one go"""
        image_paths_str = json.dumps(image_paths)
        
        # Base script that matches demo.py structure
        script = f"""
import sys
import os

# Use offline mode
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

# Setup paths
sys.path.insert(0, 'external/Hunyuan3D-2.1')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

from PIL import Image
from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
{f"torch.manual_seed({seed})" if seed else ""}

# Load images
image_paths = {image_paths_str}
pil_images = [Image.open(p).convert("RGB") for p in image_paths]

print("Loading shape generation model...")
shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
    'tencent/Hunyuan3D-2.1',
    subfolder='hunyuan3d-dit-v2-1'
)

print(f"Generating 3D shape from {{len(pil_images)}} images...")
try:
    result = shape_pipeline(
        image=pil_images if len(pil_images) > 1 else pil_images[0],
        num_inference_steps={shape_steps},
        guidance_scale={guidance_scale},
        resolution={resolution},
        {"multi_view=True" if is_multi_view else ""}
    )
    
    if result and len(result) > 0:
        mesh = result[0]
        if mesh is not None:
"""
        
        if enable_texture:
            # With texture - save intermediate GLB then texture it
            script += f"""
            # Save intermediate mesh
            temp_mesh = "{output_glb.replace('_textured', '')}"
            mesh.export(temp_mesh)
            print(f"Saved intermediate mesh: {{temp_mesh}}")
            
            # Apply texture painting
            print("\nApplying texture...")
            from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
            
            # Configure texture painting
            paint_config = Hunyuan3DPaintConfig(
                max_num_view=len(pil_images),
                resolution={texture_resolution}
            )
            paint_config.realesrgan_ckpt_path = "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth"
            paint_config.multiview_cfg_path = "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
            paint_config.custom_pipeline = "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr"
            
            paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
            
            # Paint texture
            output_path = paint_pipeline(
                mesh_path=temp_mesh,
                image_path=image_paths if len(image_paths) > 1 else image_paths[0],
                output_mesh_path="{output_glb}"
            )
            
            if output_path:
                print(f"Saved textured mesh: {{output_path}}")
            else:
                print("ERROR: Texture painting failed")
                import sys
                sys.exit(1)
"""
        else:
            # No texture - just save as GLB
            script += f"""
            # Save mesh
            mesh.export("{output_glb}")
            print(f"Saved mesh: {output_glb}")
"""
        
        # Complete the script
        script += """
        else:
            print("ERROR: Generated mesh is None")
            import sys
            sys.exit(1)
    else:
        print("ERROR: Pipeline returned empty result")
        import sys
        sys.exit(1)
except Exception as e:
    print(f"ERROR: Generation failed: {e}")
    import traceback
    traceback.print_exc()
    import sys
    sys.exit(1)
"""
        return script
    
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
    
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")