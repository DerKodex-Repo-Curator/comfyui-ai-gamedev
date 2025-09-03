"""
Hunyuan3D 2.1 Paint Node - Texture painting for 3D meshes
Separate node for applying textures to meshes using Blender
"""

import torch
import numpy as np
from pathlib import Path
from typing import Optional, Union, Tuple, Any
import tempfile
import uuid
from PIL import Image
import json
import datetime

from .utils.conda_runner import CondaRunner

# Import ComfyUI modules
try:
    from comfy_extras.nodes_hunyuan3d import MESH
except ImportError:
    # Fallback if not available
    class MESH:
        def __init__(self, vertices, faces):
            self.vertices = vertices
            self.faces = faces

try:
    import folder_paths
except ImportError:
    # Fallback for testing outside ComfyUI
    class folder_paths:
        @staticmethod
        def get_output_directory():
            return Path.home() / "ComfyUI" / "output"

class Hunyuan3DPaintNode:
    """
    Applies textures to 3D meshes using Hunyuan3D 2.1 texture painting
    
    Takes a mesh (from Hunyuan3D shape node) and reference images
    to generate PBR textures using Blender integration.
    
    Inputs:
    - mesh: 3D mesh to paint (MESH type from shape node)
    - images: Reference images for texture generation
    - resolution: Texture resolution (512, 1024, 2048)
    - steps: Inference steps for texture generation
    
    Outputs:
    - mesh: Textured mesh with PBR materials (MESH)
    - mesh_filepath: Path to textured GLB file (STRING)
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mesh": ("MESH",),  # Input mesh from shape node
                "images": ("IMAGE",),  # Reference images
                "resolution": (["512", "1024", "2048"], {"default": "1024"}),
                "steps": ("INT", {
                    "default": 50,
                    "min": 1,
                    "max": 200,
                    "step": 1
                }),
            },
            "optional": {
                "mesh_path": ("STRING", {"default": "", "multiline": False}),  # Alternative: file path
                "conda_path": ("STRING", {"default": "conda", "multiline": False}),
                "blender_path": ("STRING", {"default": "blender", "multiline": False}),
            }
        }
    
    RETURN_TYPES = (
        "MESH",          # Textured mesh
        "STRING",        # Path to textured GLB file
    )
    
    RETURN_NAMES = (
        "textured_mesh",
        "glb_filepath",
    )
    
    FUNCTION = "paint_texture"
    CATEGORY = "🎮 AI GameDev/3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Save to ComfyUI output/mesh directory
        output_dir = Path(folder_paths.get_output_directory())
        self.output_dir = output_dir / "mesh"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conda_runner = CondaRunner(env_name="hunyuan3d")
        
        # Check environment on init
        if not self.conda_runner.check_environment():
            print("⚠️  Warning: Hunyuan3D conda environment not properly configured")
            print("   Please run: python install.py")
    
    def paint_texture(
        self,
        mesh: Any,
        images: torch.Tensor,
        resolution: str,
        steps: int,
        mesh_path: str = "",
        conda_path: str = "conda",
        blender_path: str = "blender",
        **kwargs
    ) -> Tuple[Any, str]:
        """
        Apply textures to mesh using Hunyuan3D painting pipeline
        
        Args:
            mesh: Input mesh object or None if using mesh_path
            images: Reference images tensor [B, H, W, C]
            resolution: Texture resolution
            steps: Number of inference steps
            mesh_path: Optional path to mesh file (if mesh not provided)
            conda_path: Path to conda executable
            blender_path: Path to blender executable
            
        Returns:
            Tuple of (textured_mesh, glb_filepath)
        """
        
        # Determine mesh source
        if mesh and hasattr(mesh, 'vertices'):
            # Save mesh to temp file for painting
            temp_mesh = self.output_dir / f"temp_mesh_{uuid.uuid4().hex[:8]}.obj"
            self._save_mesh_as_obj(mesh, temp_mesh)
            mesh_file = str(temp_mesh)
            print(f"📦 Using mesh object, saved to: {temp_mesh}")
        elif mesh_path:
            mesh_file = mesh_path
            print(f"📦 Using mesh file: {mesh_file}")
        else:
            print("❌ No mesh provided!")
            return (None, "")
        
        # Save reference images
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"paint_ref_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        print(f"🖼️  Saved {len(image_paths)} reference images")
        
        # Configure conda runner paths
        self.conda_runner.conda_path = conda_path
        self.conda_runner.blender_path = blender_path
        
        # Generate textured GLB
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_glb = self.output_dir / f"hunyuan3d_painted_{timestamp}_{run_id}.glb"
        
        # Create painting script
        script = self._create_paint_script(
            mesh_path=mesh_file,
            image_paths=image_paths,
            output_glb=str(output_glb),
            resolution=int(resolution),
            steps=steps
        )
        
        script_path = self.output_dir / f"paint_{run_id}.py"
        script_path.write_text(script)
        
        print(f"🎨 Painting texture (res={resolution}, steps={steps})...")
        print(f"  Output: {output_glb}")
        
        # Run painting inside Blender
        success = self.conda_runner.execute_in_blender(script_path, timeout=600)
        
        # Clean up temp files
        script_path.unlink(missing_ok=True)
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        if mesh and hasattr(mesh, 'vertices'):
            temp_mesh.unlink(missing_ok=True)
        
        if success and output_glb.exists():
            print(f"✅ Texture painting successful: {output_glb}")
            
            # Load the textured mesh
            import trimesh
            tm_mesh = trimesh.load(str(output_glb))
            
            # Convert to MESH object
            vertices = torch.from_numpy(tm_mesh.vertices).float().unsqueeze(0)
            faces = torch.from_numpy(tm_mesh.faces).long().unsqueeze(0)
            textured_mesh = MESH(vertices, faces)
            
            return (textured_mesh, str(output_glb))
        else:
            print("❌ Texture painting failed")
            return (mesh, "")
    
    def _save_mesh_as_obj(self, mesh: Any, output_path: Path):
        """Save MESH object as OBJ file"""
        vertices = mesh.vertices[0].cpu().numpy()  # Remove batch dim
        faces = mesh.faces[0].cpu().numpy()
        
        with open(output_path, 'w') as f:
            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]} {v[1]} {v[2]}\n")
            
            # Write faces (OBJ uses 1-indexed)
            for face in faces:
                f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")
    
    def _create_paint_script(self, mesh_path: str, image_paths: list, 
                            output_glb: str, resolution: int, steps: int) -> str:
        """Create texture painting script for Blender execution"""
        
        image_paths_str = json.dumps(image_paths)
        
        # RealESRGAN should be in ComfyUI models directory
        # The install script creates a symlink from Hunyuan3D to ComfyUI's model
        
        return f"""
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
        pass

from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
import os
import tempfile
import shutil

# Load reference images
image_paths = {image_paths_str}
is_multi_view = len(image_paths) > 1

print(f"Loading texture painting model for {{len(image_paths)}} views...")
paint_config = Hunyuan3DPaintConfig(
    max_num_view=len(image_paths),
    resolution={resolution}
)

# Set config paths explicitly
paint_config.multiview_cfg_path = "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
paint_config.custom_pipeline = "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr"
paint_config.realesrgan_ckpt_path = "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth"

paint_pipeline = Hunyuan3DPaintPipeline(paint_config)

print("Painting textures with Blender...")
# Use a temp directory for intermediate files
temp_dir = tempfile.mkdtemp(prefix="hunyuan_paint_")
try:
    # Run texture painting
    paint_pipeline(
        mesh_path="{mesh_path}",
        image_path=image_paths if is_multi_view else image_paths[0],
        output_dir=temp_dir,
        num_inference_steps={steps},
        multi_view=is_multi_view
    )
    
    # Find the generated GLB file
    import glob
    glb_files = glob.glob(os.path.join(temp_dir, "*.glb"))
    if glb_files:
        # Copy to final location
        shutil.copy(glb_files[0], "{output_glb}")
        print(f"Saved textured GLB: {output_glb}")
    else:
        print("Warning: No GLB file generated")
finally:
    # Clean up temp directory
    shutil.rmtree(temp_dir, ignore_errors=True)

print("Texture painting complete!")
"""
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Force re-execution when inputs change
        return float("nan")

NODE_CLASS_MAPPINGS = {
    "Hunyuan3DPaintNode": Hunyuan3DPaintNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3DPaintNode": "🎨 Hunyuan3D Paint Texture"
}