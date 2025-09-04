"""
Conda environment runner for executing Hunyuan3D scripts
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple
import tempfile
import json

class CondaRunner:
    """Execute Python scripts in conda environment"""
    
    def __init__(self, env_name: str = None):
        # Use environment variables or defaults
        self.env_name = env_name or os.environ.get("HUNYUAN3D_CONDA_ENV", "hunyuan3d")
        self.conda_path = os.environ.get("HUNYUAN3D_CONDA_PATH", "conda")
        self.blender_path = os.environ.get("HUNYUAN3D_BLENDER_PATH", "blender")
        
        # Try to find conda if not an absolute path
        if not Path(self.conda_path).is_absolute():
            found_conda = self._find_conda()
            if found_conda:
                self.conda_path = found_conda
        
        # Get the project root directory dynamically
        # Look for the directory containing external/Hunyuan3D-2.1
        self.project_root = None
        
        # Start from this file and go up to find the project root
        for parent in Path(__file__).parents:
            if (parent / "external" / "Hunyuan3D-2.1").exists():
                self.project_root = parent
                break
        
        # If not found, try current working directory
        if self.project_root is None:
            if (Path.cwd() / "external" / "Hunyuan3D-2.1").exists():
                self.project_root = Path.cwd()
            # Or check if we're in ComfyUI and the node is in custom_nodes
            elif (Path.cwd() / "custom_nodes" / "comfyui-ai-gamedev" / "external" / "Hunyuan3D-2.1").exists():
                self.project_root = Path.cwd() / "custom_nodes" / "comfyui-ai-gamedev"
            else:
                # Last resort - assume we're 4 levels deep
                self.project_root = Path(__file__).parent.parent.parent.parent
                print(f"⚠️ Warning: Could not verify project root, using: {self.project_root}")
        
    def _find_conda(self) -> Optional[str]:
        """Find conda executable"""
        import shutil
        
        # Try common locations
        conda_locations = [
            shutil.which("conda"),
            os.path.expanduser("~/miniconda3/bin/conda"),
            os.path.expanduser("~/anaconda3/bin/conda"),
            os.path.expanduser("~/miniforge3/bin/conda"),
            os.path.expanduser("~/mambaforge/bin/conda"),
        ]
        
        for path in conda_locations:
            if path and os.path.exists(path):
                return path
        
        raise RuntimeError("Conda not found. Please ensure conda is installed.")
    
    def execute_script(self, script_path: Path, timeout: int = 600) -> bool:
        """
        Execute a Python script in the conda environment
        
        Args:
            script_path: Path to the Python script to execute
            timeout: Maximum execution time in seconds
            
        Returns:
            True if execution succeeded
        """
        cmd = [
            self.conda_path,
            "run",
            "-n", self.env_name,
            "python", str(script_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root)  # Run from project root
            )
            
            # Print output for debugging
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Stderr: {result.stderr}", file=sys.stderr)
            
            # Check for success (ignore Blender segfault)
            if result.returncode != 0:
                # Check if it's just the Blender segfault
                if "Segmentation fault" in result.stderr and "Saved textured model" in result.stdout:
                    print("Note: Blender segfaulted after completion (normal behavior)")
                    return True
                else:
                    print(f"Error: Script failed with return code {result.returncode}")
                    return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"Error: Script timed out after {timeout} seconds")
            return False
        except Exception as e:
            print(f"Error executing script: {e}")
            return False
    
    def execute_in_blender(self, script_path: Path, timeout: int = 300, output_file: Path = None) -> bool:
        """
        Execute a Python script inside Blender's Python environment
        Required for texture painting which needs the 'bpy' module
        
        Args:
            script_path: Path to Python script to execute in Blender
            timeout: Maximum execution time in seconds
            output_file: Expected output file to check for success
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Run the script inside Blender's Python environment
            # This provides access to the 'bpy' module needed for mesh operations
            result = subprocess.run(
                [
                    self.conda_path, "run", "-n", self.env_name,
                    self.blender_path, "--background", "--python", str(script_path)
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root)  # Run from project root
            )
            
            # Print output for debugging
            if result.stdout:
                print(result.stdout)
            
            # Check if output file was created (most reliable indicator)
            if output_file and output_file.exists():
                if result.returncode != 0:
                    print("Note: Blender exited with error but output was generated successfully")
                return True
            
            # Check if generation completed successfully
            # Ignore Blender crashes - they happen after the work is done
            success_indicators = [
                "Saved textured mesh:",
                "Saved mesh:",
                "Saved textured GLB",
                "✅ Saved textured GLB",
                "Texture painting complete",
                "✨ Texture painting workflow complete"
            ]
            
            if any(indicator in result.stdout for indicator in success_indicators):
                # Success - model was created, ignore any crashes
                # Don't report Blender segfault as an error
                return True
            
            # Only report real failures (when no output file was created)
            if result.returncode != 0:
                # Don't show segfault errors - they're expected
                if result.stderr and "Segmentation fault" not in result.stderr:
                    # Show other errors that might be relevant
                    stderr_lines = result.stderr.split('\n')
                    important_errors = []
                    ignore_patterns = [
                        "Segmentation fault",
                        "core dumped", 
                        "blender.crash.txt",
                        "Blender quit",
                        "Warning:",
                        "Info:",
                        "found bundled python",
                        "failed. (See above for error)"
                    ]
                    for line in stderr_lines:
                        if line and not any(ignore in line for ignore in ignore_patterns):
                            important_errors.append(line)
                    if important_errors:
                        print(f"Stderr: {chr(10).join(important_errors)}", file=sys.stderr)
                
                # Only report failure if no output was created
                print(f"❌ Texture painting failed (no output file created)")
                return False
            
            return True
            
        except subprocess.TimeoutExpired:
            print(f"❌ Blender script timed out after {timeout} seconds")
            return False
        except FileNotFoundError:
            print("❌ Blender not found! Please install Blender:")
            print("   sudo apt install blender  # or")
            print("   sudo snap install blender --classic")
            return False
        except Exception as e:
            print(f"❌ Error executing Blender script: {e}")
            return False
    
    def execute_in_blender_with_args(self, script_path: Path, args: List[str], timeout: int = 300, output_file: Path = None) -> bool:
        """
        Execute a Python script inside Blender with command line arguments
        
        Args:
            script_path: Path to Python script to execute in Blender
            args: List of command line arguments to pass to the script
            timeout: Maximum execution time in seconds
            output_file: Optional path to expected output file to check for success
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build command with script arguments after double dash
            cmd = [
                self.conda_path, "run", "-n", self.env_name,
                self.blender_path, "--background", "--python", str(script_path), "--"
            ] + args
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root)
            )
            
            # Print output for debugging
            if result.stdout:
                print(result.stdout)
            
            # Check for success indicators
            success_indicators = [
                "Export completed successfully",
                "✅ Export completed",
                "✅ Saved textured GLB",
                "Texture painting workflow complete",
                "✨ Texture painting workflow complete"
            ]
            
            if any(indicator in result.stdout for indicator in success_indicators):
                return True
            
            # Check if output file was created despite any issues
            if output_file and Path(output_file).exists():
                print("  ✅ Texture painting completed (output file created)")
                return True
            
            # Only show real errors, not Blender crashes
            if result.returncode != 0 and result.stderr:
                if "Segmentation fault" not in result.stderr:
                    stderr_lines = result.stderr.split('\n')
                    important_errors = []
                    ignore_patterns = [
                        "Segmentation fault", "core dumped", "blender.crash.txt",
                        "Blender quit", "Warning:", "Info:", "found bundled python"
                    ]
                    for line in stderr_lines:
                        if line and not any(ignore in line for ignore in ignore_patterns):
                            important_errors.append(line)
                    if important_errors:
                        print(f"Stderr: {chr(10).join(important_errors)}", file=sys.stderr)
                
                print(f"❌ Texture painting failed")
                return False
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"❌ Script timed out after {timeout} seconds")
            return False
        except FileNotFoundError:
            print("❌ Blender not found! Please install Blender")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def execute_command(self, command: str, timeout: int = 60) -> Tuple[bool, str, str]:
        """
        Execute a single command in the conda environment
        
        Args:
            command: Python command to execute
            timeout: Maximum execution time
            
        Returns:
            (success, stdout, stderr)
        """
        # Create temp script
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(command)
            script_path = Path(f.name)
        
        try:
            cmd = [
                self.conda_path,
                "run",
                "-n", self.env_name,
                "python", str(script_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root)
            )
            
            return (result.returncode == 0, result.stdout, result.stderr)
            
        finally:
            script_path.unlink(missing_ok=True)
    
    def check_environment(self) -> bool:
        """Check if the conda environment exists and has required packages"""
        # Check if environment exists
        cmd = [self.conda_path, "env", "list", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Error: Could not list conda environments")
            return False
        
        envs = json.loads(result.stdout)
        env_names = [Path(env).name for env in envs.get("envs", [])]
        
        if self.env_name not in env_names:
            print(f"Error: Conda environment '{self.env_name}' not found")
            print(f"Available environments: {env_names}")
            return False
        
        # Check for required packages
        check_script = """
import sys
try:
    import torch
    import torchvision
    from PIL import Image
    print("✅ Basic packages found")
    sys.exit(0)
except ImportError as e:
    print(f"❌ Missing package: {e}")
    sys.exit(1)
"""
        
        success, stdout, stderr = self.execute_command(check_script)
        if stdout:
            print(stdout)
        
        return success