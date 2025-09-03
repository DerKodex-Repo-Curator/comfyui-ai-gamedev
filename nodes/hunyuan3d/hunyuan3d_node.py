"""
Hunyuan3D 2.1 Node Implementation
Generates 3D models from images with optional texture painting
"""

import torch
import numpy as np
from pathlib import Path
from typing import Optional, Union, List, Tuple, Any
import tempfile
import uuid
from PIL import Image
import json

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

class Hunyuan3D21Node:
    """
    ComfyUI node for Hunyuan3D 2.1 3D shape generation (Stage 1)
    
    Features:
    - Automatic background removal (no RemBG node needed)
    - Single and multi-view support (1-10 images)
    - Generates untextured 3D mesh
    
    Outputs:
    - mesh: Untextured mesh for texture painting (MESH)
    - mesh_filepath: Path to OBJ file (STRING)
    
    For textured models, connect to Hunyuan3D Paint Texture node
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),  # Can be single or batch for multi-view
                "resolution": (["256", "512", "1024"], {"default": "512"}),
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.5
                }),
                "steps": ("INT", {
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
        "MESH",          # Untextured mesh
        "STRING",        # Path to OBJ file
    )
    
    RETURN_NAMES = (
        "mesh",
        "obj_filepath",
    )
    
    FUNCTION = "generate_3d"
    CATEGORY = "🎮 AI GameDev/3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Save to ComfyUI output/mesh directory to match SaveGLB node
        output_dir = Path(folder_paths.get_output_directory())
        self.output_dir = output_dir / "mesh"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.conda_runner = CondaRunner(env_name="hunyuan3d")
        
        # Check environment on init
        if not self.conda_runner.check_environment():
            print("⚠️  Warning: Hunyuan3D conda environment not properly configured")
            print("   Please run: python install.py")
        
        # Check if Blender is installed
        import subprocess
        try:
            result = subprocess.run(['blender', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ Blender found: {result.stdout.split()[1] if result.stdout else 'version unknown'}")
            else:
                print("⚠️  Warning: Blender not found or not working properly")
                print("   Texture generation requires Blender. Install with:")
                print("   sudo apt install blender  # or")
                print("   sudo snap install blender --classic")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("❌ Blender not found! Texture generation will fail.")
            print("   Install Blender with:")
            print("   sudo apt install blender  # or")
            print("   sudo snap install blender --classic")
        
    def generate_3d(
        self,
        images: torch.Tensor,
        resolution: str,
        guidance_scale: float,
        steps: int,
        seed: int = -1,
        **kwargs
    ) -> Tuple[Any, str]:
        """
        Generate 3D shape from input images
        
        Args:
            images: Input image(s) tensor [B, H, W, C]
            resolution: Model generation resolution
            guidance_scale: Diffusion guidance scale
            steps: Number of diffusion steps
            seed: Random seed (-1 for random)
            
        Returns:
            Tuple of (mesh, obj_filepath)
        """
        
        # Multi-view is automatic based on image count (1-10 images)
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        is_multi_view = batch_size > 1 and batch_size <= 10
        
        # Check which outputs are connected (placeholder - ComfyUI provides this)
        outputs_needed = self._get_connected_outputs()
        
        # Generate base mesh
        base_mesh = self._generate_shape(
            images=images,
            resolution=int(resolution),
            guidance_scale=guidance_scale,
            steps=steps,
            is_multi_view=is_multi_view,
            seed=seed
        )
        
        # Prepare outputs
        obj_path = base_mesh.get("path", "") if base_mesh else ""
        
        # Load the OBJ file and convert to ComfyUI mesh format
        if base_mesh and base_mesh.get("path"):
            import trimesh
            tm_mesh = trimesh.load(base_mesh["path"])
            
            # Convert trimesh to ComfyUI mesh format
            vertices = torch.from_numpy(tm_mesh.vertices).float().unsqueeze(0)  # Add batch dimension
            faces = torch.from_numpy(tm_mesh.faces).long().unsqueeze(0)  # Add batch dimension
            
            # Create a mesh object that ComfyUI expects
            mesh = MESH(vertices, faces)
            print(f"✅ Mesh generated: {obj_path}")
        else:
            mesh = None
            print("❌ No mesh generated")
            
        return (mesh, obj_path)
    
    
    def _get_connected_outputs(self) -> dict:
        """
        Check which outputs have connected nodes
        This is a placeholder - actual implementation would query ComfyUI
        """
        # TODO: Query ComfyUI graph to determine connected outputs
        # For now, return all as connected
        return {
            "obj_mesh": True,
            "glb_mesh": True,
            "stl_mesh": True,
            "textured_glb": True,
        }
    
    def _generate_shape(
        self,
        images: torch.Tensor,
        resolution: int,
        guidance_scale: float,
        steps: int,
        is_multi_view: bool,
        seed: int
    ) -> Any:
        """
        Generate 3D shape using Hunyuan3D model via conda environment
        """
        # Save images to temp files
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"input_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Output path with descriptive name
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_mesh = self.output_dir / f"hunyuan3d_{timestamp}_{run_id[:8]}.obj"
        
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
        
        print(f"🎮 Generating 3D shape (res={resolution}, steps={steps})...")
        success = self.conda_runner.execute_script(script_path, timeout=300)
        
        # Clean up
        script_path.unlink(missing_ok=True)
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        if not success or not output_mesh.exists():
            raise RuntimeError("Shape generation failed")
        
        return {"path": str(output_mesh), "type": "obj"}
    
    def _apply_texture(
        self,
        mesh: Any,
        images: torch.Tensor,
        resolution: int,
        blender_path: str
    ) -> Any:
        """
        Apply texture to mesh using Blender and Hunyuan3D painting
        """
        # Save images for texture reference
        run_id = uuid.uuid4().hex[:8]
        image_paths = []
        
        for i in range(images.shape[0]):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"tex_ref_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Output path with descriptive name
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 
        output_glb = self.output_dir / f"hunyuan3d_textured_{timestamp}_{run_id[:8]}.glb"
        
        # Create texture painting script
        script = self._create_texture_script(
            mesh_path=mesh["path"],
            image_paths=image_paths,
            output_glb=str(output_glb),
            resolution=resolution
        )
        
        script_path = self.output_dir / f"paint_texture_{run_id}.py"
        script_path.write_text(script)
        
        print(f"🎨 Painting textures (res={resolution})...")
        print(f"  Script: {script_path}")
        print(f"  Output: {output_glb}")
        
        # Run texture painting inside Blender's Python environment
        success = self.conda_runner.execute_in_blender(script_path, timeout=300)
        
        # Clean up temp files
        script_path.unlink(missing_ok=True)
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        if not success:
            print("❌ Texture painting script failed")
            return mesh
        
        if output_glb.exists():
            file_size = output_glb.stat().st_size
            print(f"✅ GLB file created: {output_glb} ({file_size:,} bytes)")
            return {"path": str(output_glb), "type": "glb", "has_texture": True}
        else:
            print(f"❌ GLB file not found at: {output_glb}")
            return mesh
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """Force re-execution when inputs change"""
        return float("nan")
    
    def _create_shape_script(self, image_paths, output_mesh, resolution, 
                           guidance_scale, steps, is_multi_view, seed):
        """Create script for shape generation in conda environment"""
        
        image_paths_str = json.dumps(image_paths)
        
        return f"""
import sys
import torch
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
        pass

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
    
    def _create_texture_script(self, mesh_path, image_paths, output_glb, resolution):
        """Create script for texture painting in conda environment"""
        
        image_paths_str = json.dumps(image_paths)
        
        return f"""
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
        pass

from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
import os
import tempfile
import shutil

# Load reference images
image_paths = {image_paths_str}

print("Loading texture painting model...")
paint_config = Hunyuan3DPaintConfig(
    max_num_view=len(image_paths),
    resolution={resolution}
)
paint_pipeline = Hunyuan3DPaintPipeline(paint_config)

print("Painting textures with Blender...")
# Use a temp directory for intermediate files
temp_dir = tempfile.mkdtemp(prefix="hunyuan_paint_")
try:
    # Run texture painting
    paint_pipeline(
        mesh_path="{mesh_path}",
        image_path=image_paths if len(image_paths) > 1 else image_paths[0],
        output_dir=temp_dir,
        num_inference_steps=50,
        multi_view=len(image_paths) > 1
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
"""