# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
ComfyUI custom nodes for AI-powered game asset generation.
Repository URL: https://github.com/mattwilliamson/comfyui-ai-gamedev

## Core Features & Documentation

### Implemented Nodes
1. **Hunyuan3D 2.1** (`nodes/hunyuan3d/`) - Image-to-3D generation
   - **Unified Node**: Generates 3D mesh with optional texture painting
   - Shape generation: 10GB VRAM required
   - Texture painting: 11GB VRAM required (Blender required)
   - Texture can be enabled/disabled in node settings
   - Outputs: GLB, OBJ, and STL formats
   - See: `docs/nodes/hunyuan3d.md` for implementation details
   - Key: Wraps `external/Hunyuan3D-2.1/` submodule (DO NOT MODIFY)

2. **Video Frame Extractor** (`nodes/frame_extractor/`) - Smart video frame extraction
   - Extract evenly-distributed frames from videos
   - Skip start/end frames (intros, credits, etc.)
   - Preserves full motion range while reducing frame count
   - **Takes VIDEO input from LoadVideo node** (not IMAGE)
   - Uses ComfyUI's native `VideoInput.get_components()` API
   - See: `docs/nodes/frame_extractor.md` for implementation details
   - No additional requirements (uses ComfyUI's video system)

### Planned Nodes
3. **Prompt Optimizer** (`nodes/prompt_optimizer/`) - Model-specific prompt enhancement
4. **Text-to-Video** - Game animation generation
5. **Text-to-Speech** - Character voice generation

## Project Structure

```
comfyui-ai-gamedev/
├── nodes/                  # All custom node implementations
├── external/               # Git submodules (DO NOT MODIFY)
│   └── Hunyuan3D-2.1/     # Upstream Hunyuan3D code
├── examples/              # Test images and samples
├── docs/                  # Detailed documentation
│   ├── installation.md    # Setup instructions
│   └── nodes/            # Node-specific docs
├── resources/models/      # Model weights location
└── install.py            # Automated setup script
```

## 🚨 CRITICAL REQUIREMENTS - NEVER FORGET

### Prove Problems Before Proposing Fixes
**ALWAYS investigate and prove the root cause before suggesting solutions**
- Don't guess about causes - investigate first
- Provide diagnostic code to understand the actual problem
- Only propose fixes after confirming what's actually wrong
- Test hypotheses with evidence before treating them as facts
- Delete temporary investigation files immediately after finding conclusions

### Hunyuan3D 2.1 REQUIRES Blender
**BLENDER IS MANDATORY FOR HUNYUAN3D 2.1 - NO EXCEPTIONS**
- Texture painting REQUIRES Blender (`blender --background --python`)
- Without Blender, you only get untextured gray models (OBJ files)
- Install: `sudo snap install blender --classic` or `sudo apt install blender`
- Verify: `blender --version`
- Blender 3.0.1+ required for texture painting pipeline
- **For debugging**: Run Python scripts in Blender's environment with `blender --background --python script.py`
- **Known issue**: Blender crashes/segfaults on exit after texture painting - this is a Blender bug and should be ignored. The texture painting completes successfully before the crash. Silence/suppress these errors.

#### Texture Troubleshooting
If textures are not appearing:
1. **Check Blender is installed**: Node prints status on initialization
2. **Check console output**: Look for "🎨 Texture generation enabled" messages
3. **Verify output**: Textured models are GLB files, untextured are OBJ files
4. **File location**: Check `ComfyUI/output/mesh/` for `hunyuan3d_textured_*.glb` files
5. **Enable texture**: Ensure "enable_texture" is True in the node parameters

### Never Modify External Submodules
**NEVER modify code in `external/` directories**
- `external/Hunyuan3D-2.1/` is an upstream submodule (DO NOT EDIT)
- All customizations go in `nodes/` wrappers only
- Update submodules only: `cd external/Hunyuan3D-2.1 && git pull origin main`

### Built-in Features (No Separate Nodes Needed)
Hunyuan3D 2.1 includes these features built-in:
- **Background Removal** - Works with any input image automatically
- **Real-ESRGAN Upscaling** - Automatic texture enhancement
- **Texture Painting** - Via Blender integration (REQUIRED)
- **Multi-view Support** - Accepts 1-10 images for better quality

### Import Pattern for Hunyuan3D
Always use this exact pattern to import from submodule:
```python
import sys
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
```

### System Requirements (Hunyuan3D 2.1)
- **21GB+ VRAM** for texture generation (10GB for shape only)
- **PyTorch 2.5.1** with CUDA 12.4
- **Python 3.10**
- **Blender 3.0.1+** (REQUIRED)
- **~50GB disk space** for models
- **Conda environment**: Configurable (default: "hunyuan3d")

### Configuration
The Hunyuan3D nodes support flexible configuration:

#### Using Configuration Script
```bash
# Show current configuration
python configure_hunyuan3d.py --show

# Set conda environment name
python configure_hunyuan3d.py --conda-env my_custom_env

# Set custom paths
python configure_hunyuan3d.py --conda-path /path/to/conda --blender-path /usr/bin/blender
```

#### Using Environment Variables
```bash
export HUNYUAN3D_CONDA_ENV=my_env
export HUNYUAN3D_CONDA_PATH=/path/to/conda
export HUNYUAN3D_BLENDER_PATH=/usr/bin/blender
```

#### Configuration File
Settings are saved to `hunyuan3d_config.json` in the project root.

Priority order: Environment Variables > Config File > Defaults

### Model Storage
Models are automatically downloaded to shared cache:
- `~/.cache/hy3dgen/tencent/Hunyuan3D-2.1/hunyuan3d-dit-v2-1/` - Shape model (7GB)
- `~/.cache/hy3dgen/tencent/Hunyuan3D-2.1/hunyuan3d-paintpbr-v2-1/` - Paint model (6GB)
- `~/src/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth` - Upscaler (64MB)

## Key Development Patterns

### ComfyUI Node Registration
All nodes follow standard pattern in `__init__.py`:
```python
NODE_CLASS_MAPPINGS = {"NodeName": NodeClass}
NODE_DISPLAY_NAME_MAPPINGS = {"NodeName": "Display Name"}
```

### Node Architecture
- `INPUT_TYPES`: Define required/optional inputs
- `RETURN_TYPES`: Output types tuple
- `FUNCTION`: Main processing method name
- `CATEGORY`: Menu location (e.g., "gamedev/3d")

### ComfyUI Type System
- **MESH**: Object with `.vertices` and `.faces` tensors (from `comfy_extras.nodes_hunyuan3d`)
- **VIDEO**: VideoInput object with `.get_components()` method
- **IMAGE**: Tensor batch of images
- **STRING**: File paths for Preview3D node

### Multi-View Detection Pattern
```python
def _determine_multi_view(batch_size: int, mode: str) -> bool:
    if mode == "single": return False
    elif mode == "multi": return batch_size > 1
    else:  # auto
        return batch_size > 1 and batch_size <= 10
```

### Smart Output Generation
Only generate formats that are connected in ComfyUI workflow:
```python
def _get_connected_outputs() -> dict:
    # Query ComfyUI graph API to check connections
    # Only export formats that have downstream nodes
```

## Testing Resources

### Example Images
- Single view: `examples/input_images/single_view/railgun/frame_001_4x.png`
- Multi-view: `examples/input_images/multi_view/frame_*_4x.png` (10 frames)
- Sample video: `examples/ship.mp4` - Test video for frame extraction

### Development Mode
- No `requirements.txt` currently exists - create when adding dependencies
- Config stored in `config.json` after first run
- Logs and temp files in respective directories

## Installation & Setup

**IMPORTANT**: Different nodes have different requirements!
See `docs/installation.md` for complete instructions.

### Installation Strategy:
1. **Base install** - Required for all nodes (basic Python deps)
2. **Node-specific** - Only install what you need:
   - Hunyuan3D: Needs Blender, CUDA 12.4, 21GB VRAM, submodule
   - Frame Extractor: Just OpenCV (`pip install opencv-python`)
   - Prompt Optimizer: Just transformers library (planned)
   - Others: TBD as implemented

### Key Point:
When implementing new nodes, check existing docs first:
```bash
ls docs/nodes/  # Node-specific docs
cat docs/installation.md  # Installation requirements
```

## Node-Specific Documentation

**ALWAYS check documentation before implementing!**

When working on specific nodes:
1. Check `docs/nodes/<node_name>.md` for implementation details
2. Check `docs/installation.md` for that node's section
3. Update both when adding features/requirements

Current docs:
- **Hunyuan3D**: `docs/nodes/hunyuan3d.md` - Full implementation details
- **Frame Extractor**: `docs/nodes/frame_extractor.md` - Full implementation details
- **Prompt Optimizer**: `docs/nodes/prompt_optimizer.md` (TODO)

## Important Caveats

1. **Path Handling**: Use relative paths, no hardcoded absolute paths
2. **Conda Detection**: Installer checks common locations automatically
3. **Submodule Updates**: Only pull, never push to submodules
4. **Output Generation**: Only create formats that are connected in workflow
5. **Memory Management**: Large models require significant VRAM

## Quick Commands

```bash
# Update submodule
cd external/Hunyuan3D-2.1 && git pull origin main

# Run installation
python install.py

# Test in ComfyUI
python ~/path/to/ComfyUI/main.py
```

## ComfyUI Template Workflows

**Example workflows are shown in ComfyUI's Browse Templates section**

### Making Workflows Appear in Templates Browser
Custom node workflows appear in ComfyUI's template browser when placed in:
- `workflow_examples/` directory in the custom node folder (standard naming)
- Each workflow `.json` file should include `id` and `revision` fields at the top level:

```json
{
  "id": "unique-workflow-id",
  "revision": 0,
  "last_node_id": 10,
  "last_link_id": 15,
  "nodes": [...],
  "links": [...],
  "groups": [],
  "config": {},
  "extra": {},
  "version": 0.4
}
```

### Current Example Workflows
Located in `/example_workflows/`:
1. **image_to_3d_model.json** - Single image to textured 3D using Hunyuan3D
2. **video_frame_preview.json** - Extract and preview all frames from video
3. **video_to_3d_model.json** - Extract 8 frames from video for 3D reconstruction

### Important Integration Notes

#### Preview3D Node Requirements
- **Preview3D expects STRING input** (file path), not MESH objects
- Connect Hunyuan3D's `mesh_filepath` output (slot 1) to Preview3D's `model_file` input
- Do NOT connect the MESH output directly to Preview3D

#### File Storage Locations
- **Hunyuan3D outputs**: Saved to `ComfyUI/output/mesh/` (same as SaveGLB node)
- **Load3D looks in**: `ComfyUI/input/3d/` (recursively)
- **SaveGLB default**: `ComfyUI/output/mesh/` (with "mesh/" prefix)
- Files are named with timestamp: `hunyuan3d_textured_YYYYMMDD_HHMMSS_[uuid].glb`
- **To use with Load3D**: Copy files from `output/mesh/` to `input/3d/`

#### VideoFrameExtractor Updates
- **Takes VIDEO input from LoadVideo node** (not IMAGE)
- Uses ComfyUI's native `VideoInput.get_components()` API
- Node class renamed from `FrameExtractor` to `VideoFrameExtractor`
- Removed fps output (not needed)
- Returns: frames (IMAGE), total_frames (INT), extracted_count (INT)