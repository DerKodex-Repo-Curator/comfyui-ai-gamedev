#!/usr/bin/env python3
"""
Installation script for ComfyUI AI GameDev nodes
Handles post-install setup including Hunyuan3D-2.1 dependencies
"""

import subprocess
import sys
import os
from pathlib import Path
import argparse
import shutil

class ComfyUIGameDevInstaller:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.hunyuan_dir = self.root_dir / "external" / "Hunyuan3D-2.1"
        
    def check_prerequisites(self):
        """Check if required tools are available"""
        print("🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 10):
            print("❌ Python 3.10+ is required")
            return False
            
        # Check if git is available
        if not shutil.which("git"):
            print("❌ Git is not installed")
            return False
            
        # Check if CUDA is available (optional but recommended)
        try:
            import torch
            if torch.cuda.is_available():
                print(f"✅ CUDA available: {torch.cuda.get_device_name(0)}")
            else:
                print("⚠️  CUDA not available - CPU mode will be slow")
        except ImportError:
            print("⚠️  PyTorch not installed - will install with Hunyuan3D")
            
        # Check if Blender is available
        if shutil.which("blender"):
            print("✅ Blender found in PATH")
        else:
            print("⚠️  Blender not found - required for texture painting")
            print("   Installation instructions:")
            print("   ")
            print("   Ubuntu/Debian:")
            print("     # Install SSL/TLS libraries first")
            print("     sudo apt install libssl-dev ca-certificates -y")
            print("     # Then install Blender")
            print("     sudo snap install blender --classic")
            print("     # Or: sudo apt install blender")
            print("   ")
            print("   Other systems:")
            print("     Download from: https://www.blender.org/download/")
            
        return True
    
    def init_submodules(self):
        """Initialize and update git submodules"""
        print("\n📦 Initializing git submodules...")
        
        try:
            # Initialize submodules
            subprocess.run(
                ["git", "submodule", "init"],
                cwd=self.root_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            # Update submodules
            subprocess.run(
                ["git", "submodule", "update", "--recursive"],
                cwd=self.root_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            if self.hunyuan_dir.exists() and any(self.hunyuan_dir.iterdir()):
                print("✅ Hunyuan3D-2.1 submodule initialized")
                return True
            else:
                print("❌ Submodule directory is empty")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to initialize submodules: {e}")
            return False
    
    def setup_conda_env(self, env_name="hunyuan3d"):
        """Set up conda environment for Hunyuan3D"""
        print(f"\n🐍 Setting up conda environment '{env_name}'...")
        
        # Check if conda is available - try multiple common locations
        conda_cmd = None
        conda_locations = [
            shutil.which("conda"),  # In PATH
            os.path.expanduser("~/miniconda3/bin/conda"),
            os.path.expanduser("~/anaconda3/bin/conda"),
            os.path.expanduser("~/miniforge3/bin/conda"),
            os.path.expanduser("~/mambaforge/bin/conda"),
        ]
        
        for conda_path in conda_locations:
            if conda_path and os.path.exists(conda_path):
                conda_cmd = conda_path
                print(f"Found conda at: {conda_path}")
                break
        
        if not conda_cmd:
            print("⚠️  Conda not found - skipping environment setup")
            print("   Common installation locations checked:")
            print("   - ~/miniconda3, ~/anaconda3, ~/miniforge3")
            print("   Install from: https://docs.conda.io/en/latest/miniconda.html")
            return False
            
        try:
            # Check if environment already exists
            result = subprocess.run(
                [conda_cmd, "env", "list"],
                capture_output=True,
                text=True
            )
            
            if env_name in result.stdout:
                print(f"✅ Conda environment '{env_name}' already exists")
                return True
                
            # Create new environment
            print(f"Creating conda environment '{env_name}' with Python 3.10...")
            subprocess.run(
                [conda_cmd, "create", "-n", env_name, "python=3.10", "-y"],
                check=True
            )
            
            print(f"✅ Conda environment '{env_name}' created")
            print(f"   Activate with: conda activate {env_name}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to set up conda environment: {e}")
            return False
    
    def install_ssl_support(self):
        """Install SSL support in conda environment"""
        print("\n🔒 Installing SSL support...")
        
        # Check if we're in a conda environment
        if os.environ.get('CONDA_DEFAULT_ENV'):
            try:
                print("Installing SSL certificates in conda environment...")
                subprocess.run(
                    ["conda", "install", "certifi", "ca-certificates", "openssl", "-y"],
                    check=True
                )
                print("✅ SSL support installed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Failed to install SSL support: {e}")
                print("   You may need to run: conda install certifi ca-certificates openssl -y")
                return False
        else:
            print("ℹ️  Not in conda environment, skipping SSL setup")
            print("   If you encounter SSL errors, activate conda and run:")
            print("   conda install certifi ca-certificates openssl -y")
            return True
    
    def build_custom_components(self):
        """Build Hunyuan3D custom components"""
        print("\n🔨 Building custom components...")
        
        # Check if hy3dpaint directory exists
        hy3dpaint_dir = self.hunyuan_dir / "hy3dpaint"
        
        if not hy3dpaint_dir.exists():
            print("⚠️  hy3dpaint directory not found, skipping custom builds")
            return True
        
        success = True
        
        # RealESRGAN will be handled in download_model_weights()
        # It will be downloaded to ComfyUI models directory and symlinked
        
        # Build custom rasterizer
        rasterizer_dir = hy3dpaint_dir / "custom_rasterizer"
        if rasterizer_dir.exists():
            print("Building custom rasterizer...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", "."],
                    cwd=rasterizer_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ Custom rasterizer built")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to build custom rasterizer: {e}")
                print("   Error output:", e.stderr if e.stderr else "No error output")
                success = False
        
        # Compile mesh painter
        renderer_dir = hy3dpaint_dir / "DifferentiableRenderer"
        compile_script = renderer_dir / "compile_mesh_painter.sh"
        
        if compile_script.exists():
            print("Compiling mesh painter...")
            try:
                # Make script executable
                compile_script.chmod(0o755)
                
                # Run compilation
                subprocess.run(
                    ["bash", str(compile_script)],
                    cwd=renderer_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
                print("✅ Mesh painter compiled")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to compile mesh painter: {e}")
                print("   Error output:", e.stderr if e.stderr else "No error output")
                print("   You may need to manually run:")
                print(f"   cd {renderer_dir}")
                print("   bash compile_mesh_painter.sh")
                success = False
        else:
            print("⚠️  compile_mesh_painter.sh not found")
        
        return success
    
    def install_hunyuan_dependencies(self):
        """Install Hunyuan3D-2.1 dependencies"""
        print("\n📚 Installing Hunyuan3D-2.1 dependencies...")
        
        requirements_file = self.hunyuan_dir / "requirements.txt"
        
        if not requirements_file.exists():
            print("❌ Hunyuan3D requirements.txt not found")
            print("   Make sure submodule is initialized")
            return False
            
        try:
            # Install requirements
            print("Installing from requirements.txt...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True
            )
            
            print("✅ Hunyuan3D dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("   Try running in a conda environment or virtual environment")
            return False
    
    def install_comfyui_dependencies(self):
        """Install ComfyUI node dependencies"""
        print("\n📚 Installing ComfyUI node dependencies...")
        
        requirements_file = self.root_dir / "requirements.txt"
        
        # Create requirements.txt if it doesn't exist
        if not requirements_file.exists():
            print("Creating requirements.txt...")
            requirements_content = """# ComfyUI AI GameDev Dependencies
torch>=2.0.0
torchvision
numpy
Pillow
trimesh
scipy
opencv-python
"""
            requirements_file.write_text(requirements_content)
        
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                check=True
            )
            
            print("✅ ComfyUI node dependencies installed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    def download_model_weights(self):
        """Download and setup model weights"""
        print("\n🎯 Model Weights Setup...")
        
        # Determine ComfyUI models directory
        comfyui_dir = Path.home() / "src" / "ComfyUI"
        if not comfyui_dir.exists():
            comfyui_dir = Path.home() / "ComfyUI"
        
        if not comfyui_dir.exists():
            print("⚠️  ComfyUI directory not found")
            print("   Expected at: ~/src/ComfyUI or ~/ComfyUI")
            comfyui_upscale_dir = None
        else:
            comfyui_upscale_dir = comfyui_dir / "models" / "upscale_models"
            comfyui_upscale_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ ComfyUI models directory: {comfyui_dir}")
        
        # 1. Download Real-ESRGAN to ComfyUI models directory
        if comfyui_upscale_dir:
            esrgan_path = comfyui_upscale_dir / "RealESRGAN_x4plus.pth"
            if not esrgan_path.exists():
                print("📥 Downloading Real-ESRGAN model for texture upscaling...")
                try:
                    import urllib.request
                    url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
                    urllib.request.urlretrieve(url, esrgan_path)
                    print(f"✅ Real-ESRGAN model downloaded to: {esrgan_path}")
                except Exception as e:
                    print(f"⚠️  Failed to download Real-ESRGAN: {e}")
                    print("   Manual download: https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth")
            else:
                print(f"✅ Real-ESRGAN model already present: {esrgan_path}")
            
            # Create symlink in Hunyuan3D directory
            hunyuan_esrgan_path = self.hunyuan_dir / "hy3dpaint" / "ckpt" / "RealESRGAN_x4plus.pth"
            if not hunyuan_esrgan_path.exists():
                hunyuan_esrgan_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    hunyuan_esrgan_path.symlink_to(esrgan_path)
                    print(f"✅ Created symlink for Hunyuan3D")
                except Exception as e:
                    print(f"⚠️  Could not create symlink: {e}")
        
        # 2. Download Hunyuan3D models to ComfyUI directory
        print("\n📥 Downloading Hunyuan3D models...")
        print("   This requires ~13GB of disk space")
        
        if comfyui_dir and comfyui_dir.exists():
            # Create Hunyuan3D model directories in ComfyUI
            hunyuan_models_dir = comfyui_dir / "models" / "diffusion_models" / "Hunyuan3D-2.1"
            hunyuan_models_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                # Check if huggingface_hub is installed
                import huggingface_hub
                from huggingface_hub import hf_hub_download
                
                # Download shape generation model
                print("\n1️⃣  Downloading shape generation model (7GB)...")
                shape_model_dir = hunyuan_models_dir / "hunyuan3d-dit-v2-1"
                shape_model_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    # Download the model files to ComfyUI directory
                    print("   Downloading to ComfyUI models directory...")
                    shape_files = [
                        "config.json",
                        "model_index.json",
                        "scheduler/scheduler_config.json",
                        "text_encoder/config.json",
                        "text_encoder/model.safetensors",
                        "text_encoder_2/config.json",
                        "text_encoder_2/model.safetensors",
                        "tokenizer/merges.txt",
                        "tokenizer/special_tokens_map.json",
                        "tokenizer/tokenizer_config.json",
                        "tokenizer/vocab.json",
                        "tokenizer_2/merges.txt",
                        "tokenizer_2/special_tokens_map.json",
                        "tokenizer_2/tokenizer_config.json",
                        "tokenizer_2/vocab.json",
                        "transformer/config.json",
                        "transformer/diffusion_pytorch_model.safetensors",
                        "vae/config.json",
                        "vae/diffusion_pytorch_model.safetensors",
                    ]
                    
                    for file_path in shape_files:
                        local_file = shape_model_dir / file_path
                        if not local_file.exists():
                            local_file.parent.mkdir(parents=True, exist_ok=True)
                            print(f"   Downloading {file_path}...")
                            hf_hub_download(
                                repo_id="tencent/Hunyuan3D-2.1",
                                subfolder=f"hunyuan3d-dit-v2-1/{file_path}",
                                filename=Path(file_path).name,
                                local_dir=str(local_file.parent),
                                local_dir_use_symlinks=False,
                                resume_download=True
                            )
                    
                    print(f"   ✅ Shape model installed to: {shape_model_dir}")
                    
                    # Also ensure it's cached for HuggingFace
                    huggingface_hub.snapshot_download(
                        repo_id="tencent/Hunyuan3D-2.1",
                        subfolder="hunyuan3d-dit-v2-1",
                        local_dir_use_symlinks=False,
                        resume_download=True
                    )
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to download shape model: {e}")
                
                # Download texture painting model
                print("\n2️⃣  Downloading texture painting model (6GB)...")
                paint_model_dir = hunyuan_models_dir / "hunyuan3d-paintpbr-v2-1"
                paint_model_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    # For paint model, we'll keep it in HF cache as it's loaded differently
                    model_path = huggingface_hub.snapshot_download(
                        repo_id="tencent/Hunyuan3D-2.1",
                        subfolder="hunyuan3d-paintpbr-v2-1",
                        local_dir_use_symlinks=False,
                        resume_download=True
                    )
                    print(f"   ✅ Paint model cached at: {model_path}")
                    
                    # Create a symlink in ComfyUI for consistency
                    if not (paint_model_dir / "model.safetensors").exists():
                        try:
                            # Find the model file in HF cache
                            hf_cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
                            paint_cache = hf_cache_dir / "models--tencent--Hunyuan3D-2.1"
                            if paint_cache.exists():
                                # Create info file pointing to cache
                                info_file = paint_model_dir / "model_location.txt"
                                info_file.write_text(f"Model cached at: {model_path}\n")
                                print(f"   ✅ Paint model location saved")
                        except Exception:
                            pass
                            
                except Exception as e:
                    print(f"   ⚠️  Failed to download paint model: {e}")
                
                print(f"\n✅ Hunyuan3D models directory: {hunyuan_models_dir}")
                    
            except ImportError:
                print("⚠️  huggingface_hub not installed")
                print("   Install with: pip install huggingface_hub")
                print("   Models will be downloaded on first use")
            except Exception as e:
                print(f"⚠️  Could not download models: {e}")
                print("   Models will be downloaded automatically on first use")
        else:
            print("⚠️  ComfyUI directory not found - models will use default cache")
            print("   Models will be stored in: ~/.cache/huggingface/hub/")
        
        # 3. Test the setup
        print("\n🧪 Testing model setup...")
        print("   Running shape generation test...")
        
        test_script = self.root_dir / "test_shape.py"
        if test_script.exists():
            try:
                result = subprocess.run(
                    [sys.executable, str(test_script)],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.root_dir
                )
                if "Shape generation complete" in result.stdout:
                    print("   ✅ Shape generation test successful!")
                else:
                    print("   ⚠️  Shape generation test failed")
                    if result.stderr:
                        print(f"   Error: {result.stderr[:200]}")
            except subprocess.TimeoutExpired:
                print("   ⚠️  Test timed out (this is normal for first run)")
            except Exception as e:
                print(f"   ⚠️  Could not run test: {e}")
        
        print("\n📝 Model locations:")
        if comfyui_dir and comfyui_dir.exists():
            print(f"   • RealESRGAN: {comfyui_dir}/models/upscale_models/RealESRGAN_x4plus.pth")
            print(f"   • Hunyuan3D Shape: {comfyui_dir}/models/diffusion_models/Hunyuan3D-2.1/hunyuan3d-dit-v2-1/")
            print(f"   • Hunyuan3D Paint: ~/.cache/huggingface/hub/models--tencent--Hunyuan3D-2.1/")
        else:
            print("   • Models stored in default HuggingFace cache: ~/.cache/huggingface/hub/")
        print("\n💡 Models are shared between ComfyUI nodes and command-line scripts")
        
        return True
    
    def create_config(self):
        """Create default configuration"""
        print("\n⚙️  Creating configuration...")
        
        config_file = self.root_dir / "config.json"
        
        if config_file.exists():
            print("✅ config.json already exists")
            return True
            
        config = {
            "hunyuan3d": {
                "model_path": "resources/models",
                "conda_env": "hunyuan3d",
                "blender_path": "blender",
                "device": "cuda",
                "precision": "fp16"
            },
            "frame_selector": {
                "default_frames": 6,
                "distribution": "uniform"
            },
            "prompt_optimizer": {
                "models": ["flux", "wanvideo", "hunyuan3d"]
            }
        }
        
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        print("✅ Created config.json")
        return True
    
    def run_installation(self, skip_conda=False, skip_deps=False):
        """Run the complete installation process"""
        print("="*60)
        print("🚀 ComfyUI AI GameDev Installation")
        print("="*60)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites check failed")
            return False
        
        # Initialize submodules
        if not self.init_submodules():
            print("\n❌ Submodule initialization failed")
            return False
        
        # Set up conda environment (optional)
        if not skip_conda:
            self.setup_conda_env()
        
        # Install SSL support (important for conda environments)
        if not skip_deps and os.environ.get('CONDA_DEFAULT_ENV'):
            self.install_ssl_support()
        
        # Install dependencies
        if not skip_deps:
            self.install_comfyui_dependencies()
            self.install_hunyuan_dependencies()
            
            # Build custom components for Hunyuan3D painting
            self.build_custom_components()
        
        # Create configuration
        self.create_config()
        
        # Model weights info
        self.download_model_weights()
        
        print("\n" + "="*60)
        print("✅ Installation Complete!")
        print("="*60)
        
        print("\n📋 Next Steps:")
        print("1. Download model weights (see instructions above)")
        print("2. Restart ComfyUI")
        print("3. Look for 'Hunyuan3D 2.1' in the node menu")
        print("4. Try the example workflows in workflows/reference/")
        
        print("\n💡 Tips:")
        print("- Use the railgun example images for testing")
        print("- Multi-view inputs give better results")
        print("- Check CLAUDE.md for development details")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Install ComfyUI AI GameDev nodes")
    parser.add_argument("--skip-conda", action="store_true", 
                       help="Skip conda environment setup")
    parser.add_argument("--skip-deps", action="store_true",
                       help="Skip dependency installation")
    parser.add_argument("--conda-env", default="hunyuan3d",
                       help="Name for conda environment (default: hunyuan3d)")
    
    args = parser.parse_args()
    
    installer = ComfyUIGameDevInstaller()
    
    success = installer.run_installation(
        skip_conda=args.skip_conda,
        skip_deps=args.skip_deps
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()