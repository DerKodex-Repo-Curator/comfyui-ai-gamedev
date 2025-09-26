"""
Hunyuan3D 2.1 node for ComfyUI
Executes a single Python script through Blender
"""

import torch
import numpy as np
import uuid
import os
import json
import datetime
import subprocess
from pathlib import Path
from PIL import Image

try:
    import folder_paths
except ImportError:
    # For testing outside ComfyUI
    class folder_paths:
        @staticmethod
        def get_output_directory():
            return "output"

class Hunyuan3D21Node:
    """
    Hunyuan3D 2.1 - Generates textured 3D models from images
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # Get defaults from environment or use standard defaults
        default_conda_env = os.getenv("HUNYUAN3D_CONDA_ENV", "hunyuan3d")
        default_conda_path = os.getenv("HUNYUAN3D_CONDA_PATH", "conda")
        
        return {
            "required": {
                "images": ("IMAGE",),
                "resolution": (["256", "512", "768", "1024", "2048"], {"default": "512"}),  # Added 768 and 2048 options
                "texture_resolution": (["512", "768", "1024", "2048"], {"default": "768"}),  # Default to 768 for better quality
                "guidance_scale": ("FLOAT", {
                    "default": 7.5,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.5
                }),
                "inference_steps": ("INT", {
                    "default": 30,  # Standard quality (3 min generation per testing guide)
                    "min": 10,  # Minimum 10 steps required for shape generation
                    "max": 100,
                    "step": 1
                }),
            },
            "optional": {
                "conda_env": ("STRING", {"default": default_conda_env, "multiline": False}),
                "conda_path": ("STRING", {"default": default_conda_path, "multiline": False}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("glb_filepath", "obj_filepath", "stl_filepath")
    FUNCTION = "generate_3d"
    CATEGORY = "🎮 AI GameDev/3D"
    OUTPUT_NODE = True
    
    def __init__(self):
        # Get ComfyUI's output directory and resolve to absolute path
        output_dir = Path(folder_paths.get_output_directory()).resolve()
        self.output_dir = output_dir / "mesh"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Path to the single execution script (resolve symlinks)
        self.script_path = Path(__file__).resolve().parent / "hunyuan3d_execute.py"
        
        print(f"Hunyuan3D 2.1 initialized - output dir: {self.output_dir}")
    
    def generate_3d(self, images, resolution, texture_resolution,
                   guidance_scale, inference_steps, 
                   conda_env=None, conda_path=None, **kwargs):
        """Generate 3D model using single script execution through Blender"""
        
        # Use provided conda settings or defaults
        conda_env = conda_env or os.getenv("HUNYUAN3D_CONDA_ENV", "hunyuan3d")
        conda_path = conda_path or os.getenv("HUNYUAN3D_CONDA_PATH", "conda")
        
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        print(f"\n🎮 Hunyuan3D 2.1 - Generating 3D model from {batch_size} image(s)")
        print(f"   Using conda: {conda_path} with environment: {conda_env}")
        
        # Create unique run ID and directory for this generation
        run_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"hunyuan3d_{timestamp}_{run_id}"
        
        # Create a unique directory for this generation
        generation_dir = self.output_dir / base_name
        generation_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Generation directory: {generation_dir}")
        
        # Save input images to the generation directory
        image_paths = []
        for i in range(batch_size):
            img_array = (images[i].cpu().numpy() * 255).astype(np.uint8)
            img = Image.fromarray(img_array, mode='RGB')
            img_path = generation_dir / f"input_{i:03d}.png"
            img.save(img_path)
            image_paths.append(str(img_path))
        
        # Prepare config for the script (use absolute paths)
        config = {
            "image_paths": [str(Path(p).resolve()) for p in image_paths],
            "output_dir": str(generation_dir.resolve()),  # Use generation-specific directory
            "base_name": "output",  # Simplified name since we're in a unique directory
            "resolution": int(resolution),
            "texture_resolution": int(texture_resolution),
            "guidance_scale": guidance_scale,
            "inference_steps": inference_steps,
        }
        
        # Write config to generation directory
        config_path = generation_dir / "config.json"
        print(f"Writing config to: {config_path}")
        print(f"Config contents: {json.dumps(config, indent=2)}")
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Execute the single script through Blender
        cmd = [
            conda_path, "run", "-n", conda_env,
            "blender", "--background", "--python", str(self.script_path),
            "--", str(config_path)  # Pass config file as argument
        ]
        
        print(f"🔨 Executing: {' '.join(cmd)}")
        print("⏳ This will take 5-10 minutes...")
        
        # Create a minimal clean environment to avoid ComfyUI pollution
        clean_env = {
            'PATH': os.environ.get('PATH', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'),
            'HOME': os.environ.get('HOME', os.path.expanduser('~')),
            'USER': os.environ.get('USER', ''),
            'SHELL': os.environ.get('SHELL', '/bin/bash'),
            'TERM': os.environ.get('TERM', 'xterm'),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'C.UTF-8'),
        }
        
        # Only add CUDA_VISIBLE_DEVICES if it exists
        if 'CUDA_VISIBLE_DEVICES' in os.environ:
            clean_env['CUDA_VISIBLE_DEVICES'] = os.environ['CUDA_VISIBLE_DEVICES']
        
        # Add DISPLAY for Blender if it exists (though we run headless)
        if 'DISPLAY' in os.environ:
            clean_env['DISPLAY'] = os.environ['DISPLAY']
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(Path(__file__).resolve().parent.parent.parent),  # Project root (resolve symlinks)
                env=clean_env  # Use clean environment
            )
            
            # Print ALL output from the script
            if result.stdout:
                print("=== Script Output ===")
                # Print every single line, even blank ones
                for line in result.stdout.split('\n'):
                    print(f"  {line}")
            
            # Print ALL stderr output
            if result.stderr:
                print("=== Script Errors/Info ===")
                # Print all stderr lines
                for line in result.stderr.split('\n'):
                    print(f"  {line}")
            
            # Check if files were created (script should complete successfully with segfault fix)
            # Files are now in the generation-specific directory
            glb_path = generation_dir / "output_textured.glb"
            obj_path = generation_dir / "output_textured.obj"
            stl_path = generation_dir / "output_textured.stl"
            
            # Check both clean exit and file generation (both should succeed with segfault fix)
            if result.returncode != 0:
                print(f"⚠️ Process exited with non-zero code: {result.returncode}")
                if result.stderr:
                    print("Process stderr:")
                    for line in result.stderr.split('\n'):
                        if line.strip():
                            print(f"  {line}")
            
            if glb_path.exists():
                print(f"✅ Generated successfully with clean Blender exit:")
                print(f"   GLB: {glb_path.name}")
                if obj_path.exists():
                    print(f"   OBJ: {obj_path.name}")
                if stl_path.exists():
                    print(f"   STL: {stl_path.name}")
                
                # Cleanup temp files in generation directory
                # Keep the generation directory and outputs, but remove config
                config_path.unlink(missing_ok=True)
                
                return (
                    str(glb_path) if glb_path.exists() else "",
                    str(obj_path) if obj_path.exists() else "",
                    str(stl_path) if stl_path.exists() else ""
                )
            else:
                print(f"❌ Generation failed - output files not created")
                print(f"   Expected: {glb_path}")
                # Print stderr to help debug any actual errors
                if result.stderr:
                    print("Stderr output:")
                    for line in result.stderr.split('\n'):
                        if line.strip() and not "Color management" in line:
                            print(f"  {line}")
                    
        except subprocess.TimeoutExpired:
            print(f"❌ Generation timed out after 10 minutes")
        except Exception as e:
            print(f"❌ Execution failed: {e}")
        
        # Cleanup on failure - just remove config
        config_path.unlink(missing_ok=True)
        
        return ("", "", "")
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")


# Node registration
NODE_CLASS_MAPPINGS = {
    "Hunyuan3D21": Hunyuan3D21Node
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Hunyuan3D21": "Hunyuan3D 2.1"
}