# Installation Guide

## Base Installation (Required for All Nodes)

### Prerequisites
- Python 3.10+
- ComfyUI (latest version)
- Git

### Quick Install
```bash
# Navigate to ComfyUI custom_nodes
cd ~/path/to/ComfyUI/custom_nodes/

# Clone repository
git clone https://github.com/mattwilliamson/comfyui-ai-gamedev.git
cd comfyui-ai-gamedev

# Install base dependencies
pip install -r requirements.txt
```

## Node-Specific Installation

Different nodes have different requirements. Install only what you need:

---

### 🎨 Hunyuan3D 2.1 Node

**Requirements**: 
- 21GB+ VRAM (10GB for shape only)
- Blender 3.0.1+
- CUDA 12.4
- ~50GB disk space for models

**Quick Install**:
```bash
# From comfyui-ai-gamedev directory
git submodule update --init --recursive
python install.py  # Automated installation
```

**Manual Install**:
<details>
<summary>Click for detailed steps</summary>

1. **Setup Environment**:
```bash
conda create -n hunyuan3d python=3.10
conda activate hunyuan3d
conda install certifi ca-certificates openssl -y
```

2. **Install PyTorch**:
```bash
pip install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124
```

3. **Install Dependencies**:
```bash
pip install -r external/Hunyuan3D-2.1/requirements.txt
```

4. **Build Components**:
```bash
cd external/Hunyuan3D-2.1/hy3dpaint/custom_rasterizer
pip install -e .
cd ../DifferentiableRenderer
bash compile_mesh_painter.sh
cd ../../../../
```

5. **Install Blender**:
```bash
# Ubuntu/Debian
sudo apt install libssl-dev ca-certificates -y
sudo snap install blender --classic
```

6. **Download Models**:
- Real-ESRGAN: Auto-downloads via install.py
- Hunyuan3D models: Download from [Hugging Face](https://huggingface.co/tencent/Hunyuan3D-2.1)

</details>

---

### 🎯 Frame Extractor Node

**Requirements**: 
- OpenCV (cv2)
- NumPy (usually included with ComfyUI)
- PyTorch (usually included with ComfyUI)

**Install**:
```bash
pip install opencv-python>=4.8.0
# Optional: For additional codec support
pip install opencv-contrib-python
```

**Features**:
- Extract evenly-spaced frames from videos
- Skip unwanted start/end frames
- Preserve full motion range
- Memory-efficient sequential processing

**Verify Installation**:
```bash
python -c "import cv2; print(f'OpenCV {cv2.__version__} installed')"
```

---

### 💬 Prompt Optimizer Node

**Requirements**:
- Ollama server running locally
- Ollama Python client
- Vision-capable model (recommended: qwen2.5vl:7b)
- ~8GB RAM for model inference

**Install Ollama**:
```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Install Ollama (Windows)
# Download from https://ollama.com/download/windows

# Start Ollama server
ollama serve  # Usually starts automatically

# Pull recommended model
ollama pull qwen2.5vl:7b
```

**Install Python Dependencies**:
```bash
pip install ollama>=0.1.0
pip install Pillow>=10.0.0  # For image handling
```

**Features**:
- Optimizes prompts for 9+ different AI models
- Supports image context integration
- Generates both positive and negative prompts
- Model-specific optimization strategies

**Verify Installation**:
```bash
# Check Ollama is running
curl http://localhost:11434

# Check Python client
python -c "import ollama; print('Ollama client installed')"
```

---

### 🎬 Text-to-Video Node (Planned)

**Requirements**: TBD
- Likely will need specific video generation models
- Expected 24GB+ VRAM

---

### 🗣️ Text-to-Speech Node (Planned)

**Requirements**: TBD
- Likely will use Coqui TTS or similar
- ~4GB for voice models

---

## Installation Script Options

The `install.py` script handles Hunyuan3D setup automatically:

```bash
python install.py --help

Options:
  --skip-conda     Skip conda environment setup
  --skip-deps      Skip dependency installation
  --conda-env NAME Custom environment name
```

## Verification

1. **Check Base Installation**:
```bash
python -c "import numpy, PIL, cv2; print('Base deps OK')"
```

2. **Check Node in ComfyUI**:
- Restart ComfyUI
- Look for nodes under "gamedev" category

3. **Node-Specific Tests**:
- Hunyuan3D: Check for "Hunyuan3D 2.1 Shape" and "Hunyuan3D 2.1 Paint" nodes
- Frame Extractor: Check for "Frame Extractor" node under "gamedev/video" category
- Prompt Optimizer: Check for "Prompt Optimizer" node (planned)

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Ensure submodules are initialized (for Hunyuan3D)
git submodule update --init --recursive
```

**SSL Certificate Errors** (Hunyuan3D):
```bash
conda activate hunyuan3d
conda install certifi ca-certificates openssl -y
```

**Build Failures** (Hunyuan3D):
- Ensure CUDA toolkit matches PyTorch version (12.4)
- Check gcc/g++ compiler version

**Memory Issues**:
- Reduce batch size or resolution
- Use CPU mode (slower) if GPU memory insufficient

## Conda Environment Detection

The installer automatically checks for conda in:
- System PATH
- `~/miniconda3/bin/conda`
- `~/anaconda3/bin/conda`  
- `~/miniforge3/bin/conda`
- `~/mambaforge/bin/conda`