"""
Model path configuration for Hunyuan3D nodes
Handles model locations in ComfyUI directory structure
"""

import os
from pathlib import Path
from typing import Optional, Dict

def get_comfyui_dir() -> Optional[Path]:
    """Find ComfyUI installation directory"""
    
    # First, check if we're running inside ComfyUI (best method)
    try:
        import folder_paths
        # Get the actual models directory from ComfyUI
        models_dir = folder_paths.models_dir
        if models_dir:
            comfyui_dir = Path(models_dir).parent
            if comfyui_dir.exists():
                return comfyui_dir
    except (ImportError, AttributeError):
        pass
    
    # Try to find from current file location
    current_file = Path(__file__).resolve()
    # Go up from nodes/hunyuan3d/utils/model_paths.py to find ComfyUI root
    for parent in current_file.parents:
        if (parent / "models").exists() and (parent / "main.py").exists():
            return parent
        # Also check if we're in custom_nodes
        if parent.name == "custom_nodes":
            comfyui_dir = parent.parent
            if (comfyui_dir / "models").exists():
                return comfyui_dir
    
    # Fallback to common locations
    candidates = [
        Path.home() / "src" / "ComfyUI",
        Path.home() / "ComfyUI",
        Path("/opt/ComfyUI"),
    ]
    
    for path in candidates:
        if path.exists() and (path / "models").exists():
            return path
    
    return None

def get_model_paths() -> Dict[str, str]:
    """Get paths to all required models"""
    paths = {}
    
    comfyui_dir = get_comfyui_dir()
    
    if comfyui_dir:
        # RealESRGAN in upscale_models
        realesrgan = comfyui_dir / "models" / "upscale_models" / "RealESRGAN_x4plus.pth"
        if realesrgan.exists():
            paths["realesrgan"] = str(realesrgan)
        
        # Hunyuan3D shape model in diffusion_models
        shape_model = comfyui_dir / "models" / "diffusion_models" / "Hunyuan3D-2.1" / "hunyuan3d-dit-v2-1"
        if shape_model.exists():
            paths["shape_model"] = str(shape_model)
        
        # Check for paint model location file
        paint_info = comfyui_dir / "models" / "diffusion_models" / "Hunyuan3D-2.1" / "hunyuan3d-paintpbr-v2-1" / "model_location.txt"
        if paint_info.exists():
            paths["paint_model_info"] = paint_info.read_text().strip()
    
    # Fallback to HuggingFace cache
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    hf_model = hf_cache / "models--tencent--Hunyuan3D-2.1"
    if hf_model.exists():
        paths["hf_cache"] = str(hf_model)
    
    return paths

def setup_model_env():
    """Set up environment variables for model loading"""
    paths = get_model_paths()
    
    # Set environment variable for ComfyUI models if found
    if "shape_model" in paths:
        os.environ["HUNYUAN3D_SHAPE_MODEL"] = paths["shape_model"]
    
    if "realesrgan" in paths:
        os.environ["REALESRGAN_MODEL"] = paths["realesrgan"]
    
    # Always use offline mode to avoid SSL issues
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    
    return paths