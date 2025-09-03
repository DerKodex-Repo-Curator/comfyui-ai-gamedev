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
    
    def __init__(self, env_name: str = "hunyuan3d"):
        self.env_name = env_name
        self.conda_path = self._find_conda()
        
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
                cwd=os.path.expanduser("~/src/comfyui-ai-gamedev")  # Run from project root
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
                cwd=os.path.expanduser("~/src/comfyui-ai-gamedev")
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