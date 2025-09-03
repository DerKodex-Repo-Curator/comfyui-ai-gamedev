# ComfyUI AI GameDev Nodes

Custom ComfyUI nodes for AI-powered game asset generation, focusing on 3D model creation from images and videos.

## Features

### 🎮 Implemented Nodes

#### 1. **Hunyuan3D 2.1** - Image to 3D Generation
- Generate high-quality textured 3D models from single or multiple images
- **Built-in background removal** - works with any input image
- **Built-in Real-ESRGAN upscaling** - automatic texture enhancement
- Built-in texture painting with Blender integration
- **Smart memory management**: 
  - Shape only: 10GB VRAM (untextured OBJ)
  - With texture: 21GB VRAM (only when textured_glb output is connected)
  - Automatic detection prevents wasted resources
- Support for 1-10 input images for multi-view reconstruction
- Outputs STRING paths compatible with Load3D nodes

#### 2. **Frame Extractor** - Smart Video Frame Extraction  
- Extract evenly-distributed frames from videos
- Skip intro/outro frames automatically
- Perfect for turntable videos → 3D reconstruction
- Memory-efficient batch processing

### 🚀 Planned Nodes
- **Prompt Optimizer** - Model-specific prompt enhancement
- **Text-to-Video** - Game animation generation
- **Image-to-Video**: Animate static game assets

### 🎯 Frame Selector
- Extract evenly distributed frames from videos
- Perfect for multi-view 3D reconstruction
- Configurable frame distribution strategies

### 💬 Prompt Optimizer
- Enhance prompts for specific AI models (Flux, WANVideo, etc.)
- Model-specific vocabulary optimization
- Automatic prompt extension and refinement

### 🗣️ Text-to-Speech
- Generate character voices and narration
- Multiple voice styles and languages

## Installation

### Via ComfyUI Manager
1. Open ComfyUI Manager
2. Search for "AI GameDev"
3. Click Install
4. **Important**: After installation, run the setup script:
   ```bash
   cd ComfyUI/custom_nodes/comfyui-ai-gamedev
   python install.py
   ```

### Manual Installation
```bash
# Navigate to your ComfyUI custom_nodes directory
cd ~/path/to/ComfyUI/custom_nodes/  # Replace with your ComfyUI location
git clone --recursive https://github.com/mattwilliamson/comfyui-ai-gamedev.git
cd comfyui-ai-gamedev

# Run the installation script
python install.py

# Or manually:
git submodule update --init --recursive
pip install -r requirements.txt
pip install -r external/Hunyuan3D-2.1/requirements.txt
```

### Post-Installation Setup

1. **Install Blender** (Required for texture painting):
   ```bash
   # Ubuntu/Debian:
   sudo apt install libssl-dev ca-certificates -y  # SSL/TLS libraries
   sudo snap install blender --classic              # Install via snap
   # Or: sudo apt install blender                   # Install via apt
   
   # Verify installation:
   blender --version
   ```
   Other systems: [Download Blender](https://www.blender.org/download/)

2. **Download Model Weights**: Follow instructions in `external/Hunyuan3D-2.1/README.md`

3. **Optional - Conda Environment** (Recommended for isolation): 
   ```bash
   conda create -n hunyuan3d python=3.10
   conda activate hunyuan3d
   python install.py --skip-conda
   ```

## Directory Structure

```
comfyui-ai-gamedev/
├── nodes/                    # Custom node implementations
│   ├── hunyuan3d/           # Hunyuan3D 2.1 nodes
│   ├── frame_selector/      # Frame selection nodes
│   └── prompt_optimizer/    # Prompt enhancement nodes
├── examples/                 # Example files and samples
│   ├── input_images/        # Sample input images
│   │   ├── single_view/    # Single reference images
│   │   └── multi_view/     # Multiple view sets
│   └── output_samples/      # Generated samples
├── workflows/               # Example ComfyUI workflows
│   └── reference/          # Reference implementations
├── resources/              # Model weights and configs
└── docs/                   # Documentation
```

## Usage Examples

### Basic Image-to-3D
1. Load an image using ComfyUI's Image Loader
2. Connect to Hunyuan3D 2.1 node
3. Configure resolution and quality settings
4. Choose output format (textured GLB recommended for game engines)
5. Run the workflow - get a fully textured 3D model!

### Multi-View 3D Reconstruction
1. Load multiple views of your object (4-10 images work best)
2. Connect to Hunyuan3D 2.1 node
3. The node automatically detects multi-view input
4. Get higher quality 3D models with better geometry
5. Export as textured GLB for Unity, Unreal, or Godot

### Frame Selection for 3D
1. Load a video file
2. Connect to Frame Selector node
3. Set number of frames to extract (e.g., 5)
4. Connect output to Hunyuan3D for multi-view reconstruction

## Example Input Images

The repository includes sample images for testing:

### Included Examples
- **Single View**: `examples/input_images/single_view/railgun/frame_001_4x.png`
  - High-resolution railgun model for single-view 3D generation
  
- **Multi-View Set**: `examples/input_images/multi_view/frame_*_4x.png`
  - 10 frames showing a railgun from different angles (frames 001-081)
  - Perfect for testing multi-view 3D reconstruction
  - Demonstrates how video frames can be used for better 3D generation

### Adding Your Own Images
- **Single View Images**: Place in `examples/input_images/single_view/`
- **Multi-View Sets**: Place in `examples/input_images/multi_view/`
  - Best results with 4-10 views from different angles
  - Evenly distributed viewing angles work best

## Workflow References

Included reference workflows in `workflows/reference/`:
- `default_3d_hunyuan3d_image_to_model.json` - Example Hunyuan3D 2.0 workflow
- `default_3d_hunyuan3d_image_to_model_API.json` - API version for automation

These demonstrate the current Hunyuan3D 2.0 pipeline which our 2.1 nodes enhance with texture support.

## Requirements

- ComfyUI (latest version)
- Python 3.10
- PyTorch 2.5.1+ with CUDA 12.4
- Blender (for texture painting in Hunyuan3D)
- CUDA-capable GPU with 21GB+ VRAM for texture generation (or CPU mode)
- SSL certificates (installed via conda)

## Performance Tips

- The Hunyuan3D 2.1 node only generates outputs that are connected in your workflow
- Use lower resolutions (512) for faster prototyping, higher (1024+) for production
- Multi-view reconstruction provides significantly better quality
- Single view: ~2-3 minutes | Multi-view: ~5-7 minutes (varies by GPU)
- Texture generation adds ~1-2 minutes but eliminates manual texturing work

## Contributing

Contributions are welcome! Please read our contributing guidelines and submit pull requests to the main repository.

## License

This project is licensed under the MIT License. Individual model weights may have their own licenses.

## Acknowledgments

- Tencent Hunyuan team for Hunyuan3D 2.1
- ComfyUI community
- All AI model creators whose work powers these nodes

## Support

For issues, questions, or feature requests, please open an issue on [GitHub](https://github.com/mattwilliamson/comfyui-ai-gamedev/issues).
