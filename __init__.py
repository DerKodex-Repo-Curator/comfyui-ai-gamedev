"""
ComfyUI AI GameDev Nodes
Main entry point for ComfyUI custom nodes
"""

import sys
import os
from pathlib import Path

# Add paths for submodule if needed
root_dir = Path(__file__).parent
hunyuan_path = root_dir / "external" / "Hunyuan3D-2.1"

# Check if Hunyuan3D is initialized
if not hunyuan_path.exists() or not any(hunyuan_path.iterdir()):
    print("⚠️  ComfyUI AI GameDev: Hunyuan3D-2.1 submodule not initialized")
    print("   Please run: python custom_nodes/comfyui-ai-gamedev/install.py")
    print("   Or manually: git submodule update --init --recursive")
else:
    # Add Hunyuan3D to path if it exists
    if hunyuan_path.exists():
        sys.path.insert(0, str(hunyuan_path))

# Import nodes (only if they exist)
try:
    from .nodes.hunyuan3d import NODE_CLASS_MAPPINGS as HUNYUAN_MAPPINGS
    from .nodes.hunyuan3d import NODE_DISPLAY_NAME_MAPPINGS as HUNYUAN_DISPLAY
except ImportError as e:
    print(f"Warning: Could not import Hunyuan3D nodes: {e}")
    HUNYUAN_MAPPINGS = {}
    HUNYUAN_DISPLAY = {}

try:
    from .nodes.frame_extractor import NODE_CLASS_MAPPINGS as FRAME_MAPPINGS
    from .nodes.frame_extractor import NODE_DISPLAY_NAME_MAPPINGS as FRAME_DISPLAY
except ImportError as e:
    print(f"Warning: Could not import Frame Extractor nodes: {e}")
    FRAME_MAPPINGS = {}
    FRAME_DISPLAY = {}

# Combine all node mappings
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

# Add all node mappings
NODE_CLASS_MAPPINGS.update(HUNYUAN_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(HUNYUAN_DISPLAY)
NODE_CLASS_MAPPINGS.update(FRAME_MAPPINGS)
NODE_DISPLAY_NAME_MAPPINGS.update(FRAME_DISPLAY)

# Check for first run
config_file = root_dir / "config.json"
if not config_file.exists():
    print("=" * 60)
    print("🎮 ComfyUI AI GameDev - First Run Detected")
    print("=" * 60)
    print("Please complete setup by running:")
    print(f"  cd {root_dir.name}")
    print(f"  python install.py")
    print("")
    print("This will:")
    print("  • Initialize Hunyuan3D-2.1 submodule")
    print("  • Install required dependencies")
    print("  • Create configuration files")
    print("  • Set up conda environment (optional)")
    print("=" * 60)

# Add web directory for UI components and workflows
WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']