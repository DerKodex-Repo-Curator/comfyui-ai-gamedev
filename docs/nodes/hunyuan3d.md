# Hunyuan3D 2.1 Node Documentation

## Overview
ComfyUI node for image-to-3D generation with automatic texture painting.
Outputs both untextured mesh (OBJ) and textured model (GLB with embedded textures).

## Features
- **All-in-one**: Background removal, upscaling, and texture painting built-in
- **Multi-view support**: Accepts 1-10 images for better reconstruction
- **Smart texture generation**: Only runs Blender painting if textured_glb output is connected
- **No preprocessing needed**: Direct image input without RemBG or upscaling nodes

## Node Outputs

### mesh (MESH)
- Untextured OBJ file
- Always generated (10GB VRAM)
- Use for custom texturing or further processing

### textured_glb (MESH) 
- GLB file with embedded PBR textures
- **Only generated if this output is connected** (saves 11GB VRAM if not needed)
- Textures are embedded in the GLB file (no separate texture files)
- Ready for game engines (Unity, Unreal, Godot)

### preview (IMAGE)
- Rendered preview of the model
- Shows textured version if texture painting was performed

## Technical Details

### Pipeline Architecture
1. **Shape Generation**: Converts image(s) to 3D mesh using Hunyuan3D-Shape-v2-1
2. **Texture Painting**: Applies textures using Hunyuan3D-Paint-v2-1 with Blender

### System Requirements
- 21GB+ VRAM for texture generation (10GB for shape only)
- PyTorch 2.5.1 with CUDA 12.4
- Blender 3.0.1+ (installed via snap or apt)
- Python 3.10

### Model Weights & Storage

Models are automatically downloaded on first use to:
- **Shape Model** (~7GB): `~/.cache/hy3dgen/tencent/Hunyuan3D-2.1/hunyuan3d-dit-v2-1/`
  - Main file: `model.fp16.ckpt`
- **Paint Model** (~6GB): `~/.cache/hy3dgen/tencent/Hunyuan3D-2.1/hunyuan3d-paintpbr-v2-1/`
  - Distributed across: `unet/`, `vae/`, `text_encoder/`, `image_encoder/`
- **Real-ESRGAN** (64MB): Downloaded by install.py to `external/Hunyuan3D-2.1/hy3dpaint/ckpt/`

Total disk space required: ~14GB for models + cache

## Implementation Notes

### Directory Structure
```
nodes/hunyuan3d/
├── __init__.py           # Node registration
├── hunyuan3d_node.py     # Main node (Hunyuan3D21Node class)
├── core/
│   ├── shape_gen.py      # Wraps Hunyuan3DDiTFlowMatchingPipeline
│   ├── texture_paint.py  # Wraps Hunyuan3DPaintPipeline
│   └── export.py         # Format exporters (OBJ, GLB, STL)
├── utils/
│   ├── blender_bridge.py # Blender subprocess management
│   ├── mesh_utils.py     # Mesh processing utilities
│   └── image_utils.py    # Multi-view handling
└── config/
    └── default.yaml      # Node configuration
```

### Using the Hunyuan3D Submodule
The actual Hunyuan3D code is at `external/Hunyuan3D-2.1/` (DO NOT MODIFY).

Import pattern:
```python
import sys
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')

from hy3dshape.pipelines import Hunyuan3DDiTFlowMatchingPipeline
from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
```

### Multi-View Detection
```python
def _determine_multi_view(batch_size: int, mode: str) -> bool:
    if mode == "single": return False
    elif mode == "multi": return batch_size > 1
    else:  # auto
        return batch_size > 1 and batch_size <= 10
```

### Output Generation Strategy
Only generate formats that are connected in the ComfyUI workflow:
```python
def _get_connected_outputs() -> dict:
    # TODO: Query ComfyUI graph API
    # For now, check which outputs have connections
```

## Blender Integration

### Command Structure
```bash
blender --background --python paint_texture.py
```

### Key Options
- `--background`: Headless mode
- `--python <script>`: Execute Python script
- `--python-console`: Interactive Python console (for debugging)
- `--debug-python`: Enable debugging
- `-t <threads>`: Thread count

### Interactive Debugging
For debugging texture painting issues:
```bash
blender --background --python-console
```
This opens an interactive Python console with Blender's API available, useful for:
- Testing Blender Python (bpy) commands
- Debugging mesh import/export issues
- Troubleshooting texture painting pipeline
- Inspecting Blender scene state

### Texture Painting Workflow
1. Launch Blender in background mode
2. Execute Hunyuan3D painting script
3. Process mesh and apply textures
4. Save textured output
5. Exit with status code

## Testing

### Test Images
- Single view: `examples/input_images/single_view/railgun/frame_001_4x.png`
- Multi-view: `examples/input_images/multi_view/frame_*_4x.png` (10 frames)

### Performance
- Single view: ~2-3 minutes
- Multi-view: ~5-7 minutes
- Texture generation: +1-2 minutes

## Troubleshooting

### Common Issues
1. **SSL Errors**: Run `conda install certifi ca-certificates openssl -y`
2. **Blender Not Found**: Install with `sudo snap install blender --classic`
3. **VRAM Issues**: Reduce resolution or use CPU mode
4. **Build Failures**: Check CUDA version and compiler compatibility
5. **Blender Segfault on Exit**: Normal behavior after texture painting - check if output files were created successfully
6. **ModuleNotFoundError 'functional_tensor'**: Applied automatically via torchvision_fix.py