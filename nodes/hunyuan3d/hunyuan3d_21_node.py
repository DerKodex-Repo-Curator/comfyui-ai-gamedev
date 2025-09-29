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

# Import progress tracking utilities
try:
    from .progress_utils import ProgressParser
except ImportError:
    # For testing when module structure is different
    from progress_utils import ProgressParser

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
    
    Features:
    - Real-time progress monitoring via callback integration
    - File-based progress tracking to bypass subprocess buffering
    - Crystools progress reporting integration (when available)
    - Individual diffusion step capture (1/15 → 15/15)
    - Customizable output directory (optional)
    - Comprehensive error handling with descriptive messages
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
                "output_dir": ("STRING", {"default": "mesh/painted", "multiline": False}),
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
        
        print(f"Hunyuan3D 2.1 initialized - fallback output dir: {self.output_dir}")
        print(f"   Default output: ComfyUI_output/mesh/painted/")
    
    def _validate_output_files(self, glb_path, obj_path, stl_path):
        """
        Validate that expected output files exist and provide detailed error messages
        
        Args:
            glb_path: Path to expected GLB file
            obj_path: Path to expected OBJ file  
            stl_path: Path to expected STL file
            
        Raises:
            RuntimeError: If any expected output file is missing with detailed error message
        """
        missing_files = []
        
        # Check each output file
        if not glb_path.exists():
            missing_files.append(f"GLB file: {glb_path}")
        if not obj_path.exists():
            missing_files.append(f"OBJ file: {obj_path}")
        if not stl_path.exists():
            missing_files.append(f"STL file: {stl_path}")
            
        # If any files are missing, provide detailed error
        if missing_files:
            error_msg = (
                f"Hunyuan3D generation failed to create expected output files:\n"
                f"Missing files:\n" + 
                "\n".join(f"  • {file}" for file in missing_files) +
                f"\n\nThis usually indicates:\n"
                f"  • Texture painting failed during execution\n"
                f"  • Blender crashed before export completion\n"
                f"  • Insufficient VRAM (requires 21GB+ for texture generation)\n"
                f"  • Model download or path issues\n\n"
                f"Check the console output above for specific error details."
            )
            print(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
            
        print(f"✅ All output files validated successfully")
    
    def _execute_with_progress_monitoring(self, cmd, generation_dir, cwd, env, timeout=600):
        """Execute subprocess with real-time progress monitoring via progress file"""
        import subprocess
        import threading
        import time
        from pathlib import Path
        from .progress_utils import ProgressParser
        
        # Try to import Crystools progress reporting
        crystools_available = False
        try:
            from crystools import progress as crystools_progress
            crystools_available = True
            print("✅ Crystools progress reporting available")
        except ImportError:
            print("ℹ️ Crystools not available - using console progress only")
        
        progress_file_path = generation_dir / "progress.jsonl"
        
        # Create mock result object to maintain compatibility
        class MockResult:
            def __init__(self):
                self.stdout = ""
                self.stderr = ""
                self.returncode = None
        
        result = MockResult()
        
        # Start subprocess
        print(f"🕐 Starting subprocess with progress file monitoring...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=0,
            universal_newlines=True,
            cwd=cwd,
            env=env
        )
        
        # Progress monitoring thread
        def monitor_progress():
            progress_parser = ProgressParser()
            progress_count = 0
            last_position = 0
            
            # Initialize Crystools progress if available
            if crystools_available:
                try:
                    crystools_progress.start(total=100, desc="Hunyuan3D Generation")
                    print("📊 Crystools progress session started")
                except Exception as e:
                    print(f"⚠️ Crystools progress start failed: {e}")
            
            print("📋 Real-time progress monitoring started:")
            print("-" * 60)
            
            while process.poll() is None:  # While process is running
                try:
                    if progress_file_path.exists():
                        with open(progress_file_path, 'r', encoding='utf-8') as f:
                            f.seek(last_position)
                            new_lines = f.readlines()
                            last_position = f.tell()
                            
                            for line in new_lines:
                                line = line.strip()
                                if not line:
                                    continue
                                
                                # Parse progress from JSON line
                                progress = progress_parser.parse_line(line)
                                if progress:
                                    progress_count += 1
                                    elapsed_str = f"{progress.elapsed_seconds:.1f}s"
                                    remaining_str = f"{progress.remaining_seconds:.1f}s" if progress.remaining_seconds else "N/A"
                                    
                                    # Update Crystools progress if available
                                    if crystools_available:
                                        try:
                                            crystools_progress.update(
                                                progress=progress.percent / 100.0,
                                                desc=f"[{progress.stage.upper()}] {progress.message}"
                                            )
                                        except Exception as e:
                                            print(f"⚠️ Crystools progress update failed: {e}")
                                    
                                    print(f"📊 [{progress.stage.upper()}] {progress.percent}% - {progress.message}")
                                    print(f"    Elapsed: {elapsed_str} | Remaining: {remaining_str}")
                                    
                except Exception as e:
                    # Don't break monitoring on file errors
                    pass
                
                time.sleep(0.5)  # Check every 500ms
            
            print("-" * 60)
            print(f"📈 Total progress updates received: {progress_count}")
            
            # Finish Crystools progress if available
            if crystools_available:
                try:
                    crystools_progress.finish()
                    print("✅ Crystools progress session completed")
                except Exception as e:
                    print(f"⚠️ Crystools progress finish failed: {e}")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
        monitor_thread.start()
        
        # Collect output
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            result.stdout = stdout or ""
            result.stderr = stderr or ""
            result.returncode = process.returncode
            
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            result.stdout = stdout or ""
            result.stderr = stderr or ""
            result.returncode = -1
            print(f"❌ Process timed out after {timeout} seconds")
        
        # Wait for monitor thread to complete
        monitor_thread.join(timeout=1.0)
        
        return result
    
    def generate_3d(self, images, resolution, texture_resolution,
                   guidance_scale, inference_steps, output_dir=None,
                   conda_env=None, conda_path=None, **kwargs):
        """Generate 3D model using single script execution through Blender"""
        
        # Use provided conda settings or defaults
        conda_env = conda_env or os.getenv("HUNYUAN3D_CONDA_ENV", "hunyuan3d")
        conda_path = conda_path or os.getenv("HUNYUAN3D_CONDA_PATH", "conda")
        
        # Use provided output directory or default to mesh subdirectory
        if output_dir and output_dir.strip():
            # If it's a relative path, make it relative to ComfyUI output directory
            if not Path(output_dir).is_absolute():
                base_output_dir = Path(folder_paths.get_output_directory()).resolve() / output_dir
            else:
                base_output_dir = Path(output_dir).resolve()
        else:
            # Fallback: ComfyUI output directory + mesh subfolder (should not happen with new default)
            base_output_dir = self.output_dir
        
        batch_size = images.shape[0] if len(images.shape) == 4 else 1
        print(f"\n🎮 Hunyuan3D 2.1 - Generating 3D model from {batch_size} image(s)")
        print(f"   Using conda: {conda_path} with environment: {conda_env}")
        
        # Create unique run ID and directory for this generation
        run_id = uuid.uuid4().hex[:8]
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"hunyuan3d_{timestamp}_{run_id}"
        
        # Create a unique directory for this generation
        generation_dir = base_output_dir / base_name
        generation_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Generation directory: {generation_dir}")
        
        # Print output directory info
        if output_dir and output_dir.strip():
            print(f"   Custom output directory: {base_output_dir}")
        else:
            print(f"   Default output directory: {base_output_dir}")
        
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
            # Execute with real-time progress monitoring
            result = self._execute_with_progress_monitoring(
                cmd, 
                generation_dir,
                cwd=str(Path(__file__).resolve().parent.parent.parent),
                env=clean_env,
                timeout=600
            )
            
            # Parse progress from stdout and log JSON progress objects
            progress_parser = ProgressParser()
            progress_count = 0
            
            # Print ALL output from the script AND parse progress
            if result.stdout:
                print("=== Script Output ===")
                # Print every single line, even blank ones
                for line in result.stdout.split('\n'):
                    print(f"  {line}")
                    
                    # Try to parse progress from this line
                    progress = progress_parser.parse_line(line)
                    if progress:
                        progress_count += 1
                        print(f"📊 PROGRESS UPDATE #{progress_count}:")
                        print(f"    Stage: {progress.stage}")
                        print(f"    Percent: {progress.percent}%")
                        print(f"    Message: {progress.message}")
                        print(f"    Elapsed: {progress_parser.format_duration(progress.elapsed_seconds)}")
                        if progress.remaining_seconds is not None:
                            print(f"    Remaining: {progress_parser.format_duration(progress.remaining_seconds)}")
                        print(f"    Raw JSON: {progress_parser.last_raw_json}")
            
            print(f"📈 Total progress updates received: {progress_count}")
            
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
                
                # Validate output files and provide descriptive errors for missing files
                self._validate_output_files(glb_path, obj_path, stl_path)
                
                # Cleanup temp files in generation directory
                # Keep the generation directory and outputs, but remove config
                config_path.unlink(missing_ok=True)
                
                return (
                    str(glb_path) if glb_path.exists() else "",
                    str(obj_path) if obj_path.exists() else "",
                    str(stl_path) if stl_path.exists() else ""
                )
            else:
                # Primary GLB file missing - this is a complete failure
                error_msg = (
                    f"Hunyuan3D generation completely failed - no output files created.\n"
                    f"Expected primary output: {glb_path}\n\n"
                    f"This indicates a critical failure during:\n"
                    f"  • Shape generation stage (first 50% of process)\n" 
                    f"  • Texture painting initialization\n"
                    f"  • Blender environment setup\n"
                    f"  • Model loading or VRAM allocation\n\n"
                    f"Check the console output above for specific error details."
                )
                print(f"❌ {error_msg}")
                
                # Print stderr to help debug any actual errors
                if result.stderr:
                    print("Process stderr output:")
                    for line in result.stderr.split('\n'):
                        if line.strip() and not "Color management" in line:
                            print(f"  {line}")
                            
                raise RuntimeError(error_msg)
                    
        except subprocess.TimeoutExpired:
            error_msg = (
                f"Hunyuan3D generation timed out after 10 minutes.\n"
                f"This usually indicates:\n"
                f"  • Insufficient system resources (CPU/GPU/VRAM)\n"
                f"  • Model download in progress (first run takes longer)\n"
                f"  • Process stuck in diffusion steps\n"
                f"  • System overload or resource contention\n\n"
                f"Try reducing resolution or texture_resolution settings."
            )
            print(f"❌ {error_msg}")
            config_path.unlink(missing_ok=True)
            raise TimeoutError(error_msg)
            
        except Exception as e:
            error_msg = (
                f"Hunyuan3D execution failed with unexpected error: {str(e)}\n"
                f"This indicates a system-level problem:\n"
                f"  • Missing dependencies (conda, blender, models)\n"
                f"  • Permission or path issues\n"  
                f"  • Environment configuration problems\n"
                f"  • Hardware compatibility issues\n\n"
                f"Check installation and system requirements."
            )
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            config_path.unlink(missing_ok=True)
            raise RuntimeError(error_msg)
        
        # This should never be reached due to error handling above
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