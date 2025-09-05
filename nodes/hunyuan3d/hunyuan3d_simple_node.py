"""
Simplified Hunyuan3D node for ComfyUI - hardcoded values based on working test_minimal.py
Only image input is dynamic, everything else is hardcoded for reliability
"""

import torch
import numpy as np
import os
import subprocess
from pathlib import Path
from PIL import Image
import datetime
import uuid

try:
    import folder_paths
except ImportError:
    class folder_paths:
        @staticmethod
        def get_output_directory():
            return "output"

class Hunyuan3DSimpleNode:
    """
    Simplified Hunyuan3D - Minimal parameters, maximum reliability
    Based on working test_minimal.py
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("glb_path", "obj_path", "stl_path")
    FUNCTION = "generate_3d"
    CATEGORY = "🎮 AI GameDev/3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Setup output directory
        output_dir = Path(folder_paths.get_output_directory()).resolve()
        self.output_dir = output_dir / "mesh"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to execution script
        self.script_path = Path(__file__).resolve().parent / "hunyuan3d_simple_execute.py"
        
        print(f"Hunyuan3D Simple initialized - output: {self.output_dir}")
    
    def generate_3d(self, images, **kwargs):
        """Generate 3D model with hardcoded reliable settings"""
        
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        print(f"\n🎮 Hunyuan3D Simple - Processing {batch_size} image(s)")
        
        # Create unique run ID
        run_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"hunyuan3d_{timestamp}_{run_id}"
        
        # Save input images
        image_paths = []
        for i in range(batch_size):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = self.output_dir / f"input_{run_id}_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
            print(f"  Saved input image: {img_path.name}")
        
        # Execute script with hardcoded settings
        cmd = [
            "conda", "run", "-n", "hunyuan3d",
            "blender", "--background", "--python", str(self.script_path),
            "--",
            str(image_paths[0]),  # First image path
            str(self.output_dir),  # Output directory
            base_name  # Base name for outputs
        ]
        
        print(f"🔨 Executing simplified pipeline...")
        print(f"  Output will be: {base_name}_textured.glb")
        
        try:
            # Run with longer timeout for generation
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes
                cwd=str(Path(__file__).resolve().parent.parent.parent)
            )
            
            # Print ALL output from the script
            if result.stdout:
                print("=== Script Output ===")
                for line in result.stdout.split('\n'):
                    print(f"  {line}")
            
            # Print ALL stderr output
            if result.stderr:
                print("=== Script Errors/Info ===")
                for line in result.stderr.split('\n'):
                    print(f"  {line}")
            
            # Check if files were created (ignore segfault)
            glb_path = self.output_dir / f"{base_name}_textured.glb"
            obj_path = self.output_dir / f"{base_name}_textured.obj"
            stl_path = self.output_dir / f"{base_name}_textured.stl"
            
            if glb_path.exists():
                print(f"✅ Success! Generated:")
                if glb_path.exists():
                    print(f"   GLB: {glb_path.name} ({glb_path.stat().st_size // 1024}KB)")
                if obj_path.exists():
                    print(f"   OBJ: {obj_path.name} ({obj_path.stat().st_size // 1024}KB)")
                if stl_path.exists():
                    print(f"   STL: {stl_path.name} ({stl_path.stat().st_size // 1024}KB)")
                
                # Cleanup temp files
                for path in image_paths:
                    Path(path).unlink(missing_ok=True)
                
                return (
                    str(glb_path) if glb_path.exists() else "",
                    str(obj_path) if obj_path.exists() else "",
                    str(stl_path) if stl_path.exists() else ""
                )
            else:
                print(f"❌ Generation failed - no output created")
                print(f"   Check console for errors")
                
        except subprocess.TimeoutExpired:
            print(f"❌ Generation timed out after 5 minutes")
        except Exception as e:
            print(f"❌ Execution failed: {e}")
        
        # Cleanup on failure
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        
        return ("", "", "")
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


# Node registration
NODE_CLASS_MAPPINGS = {
    "Hunyuan3DSimple": Hunyuan3DSimpleNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3DSimple": "Hunyuan3D Simple (Reliable)"
}