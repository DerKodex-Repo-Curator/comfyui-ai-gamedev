# Testing Guide

This document explains how to run and work with the comprehensive unit tests for the ComfyUI AI GameDev custom nodes.

## Overview

The test suite includes **51 comprehensive tests** that simulate ComfyUI calling the nodes directly, ensuring they work correctly in the real ComfyUI environment.

### Test Coverage
- **VideoFrameExtractor**: 10 tests (frame extraction, tensor handling, edge cases)
- **Hunyuan3D 2.1**: 17 tests (3D generation, subprocess handling, file I/O)
- **PromptOptimizer**: 24 tests (Ollama integration, model configs, image processing)

## Test Structure

Tests are located in the `/tests` directory:
- `comfyui_mock.py` - ComfyUI simulation framework
- `test_frame_extractor.py` - VideoFrameExtractor node tests
- `test_hunyuan3d.py` - Hunyuan3D 2.1 node tests  
- `test_prompt_optimizer.py` - PromptOptimizer node tests

## Prerequisites

Install testing dependencies:
```bash
pip install -r requirements-test.txt
```

This installs:
- **Core Testing**: pytest, pytest-mock, pytest-asyncio
- **Node Dependencies**: torch, numpy, pillow, opencv-python, ollama
- **Development Tools**: pytest-cov, pytest-xdist, pytest-html

> **Note**: For basic conda testing setup, see the Testing section in the main README.md. This document covers advanced testing scenarios.

## Running Tests

### Run All Tests (Recommended)
```bash
# Unit tests only (51 tests) - fast, mocked dependencies
python -m pytest tests/ -v

# All tests including integration (72+ tests) - requires external services
python -m pytest tests/ tests/integration_*.py tests/visual_*.py -v
```

### Run Specific Test Categories
```bash
# Unit tests only (fast, mocked)
python -m pytest tests/test_*.py -v

# Integration tests only (requires Ollama service, real video files)
python -m pytest tests/integration_*.py -v

# Visual verification tests only (saves frames to disk)
python -m pytest tests/visual_*.py -v
```

### Run Specific Test Files
```bash
# Test only VideoFrameExtractor (10 unit tests)
python -m pytest tests/test_frame_extractor.py -v

# Test only Hunyuan3D (17 unit tests)
python -m pytest tests/test_hunyuan3d.py -v

# Test only PromptOptimizer (24 unit tests)
python -m pytest tests/test_prompt_optimizer.py -v

# VideoFrameExtractor integration tests (10 tests with real video)
python -m pytest tests/test_frame_extractor_integration.py -v

# PromptOptimizer integration tests (11 tests with real Ollama)
python -m pytest tests/test_prompt_optimizer_integration.py -v

# Hunyuan3D integration tests (4 tests with real conda/Blender execution)
python -m pytest tests/test_hunyuan3d_integration.py -v

# Visual verification tests (saves 75 frames to disk)
python -m pytest tests/test_frame_extractor_visual.py -v

# AI visual verification tests (AI analyzes extracted frames)
python -m pytest tests/test_frame_extractor_ai.py -v
```

### Integration Test Requirements

**IMPORTANT**: Integration tests FAIL (not skip) if dependencies are missing. This is intentional.

#### PromptOptimizer Integration Tests
**Requirements:**
- Ollama service running: `sudo systemctl start ollama` or `ollama serve`
- qwen2.5vl:7b model installed: `ollama pull qwen2.5vl:7b`
- Ollama Python client: `pip install ollama`

**Test what they do:**
- Real API calls to Ollama service (not mocked)
- Actual prompt optimization with different models and settings
- Performance benchmarking (~7-15s response times)
- Image processing with real tensor data

```bash
# Check Ollama is ready
curl http://localhost:11434/api/version

# Run integration tests
python -m pytest tests/test_prompt_optimizer_integration.py -v
```

#### VideoFrameExtractor Integration Tests
**Requirements:**
- Real video file: `examples/ship.mp4` (included in repo)
- OpenCV: `pip install opencv-python`

**Test what they do:**
- Load and process actual video files (not mocked)
- Extract real frames and verify count/resolution
- Performance testing (3000+ fps extraction speed)

```bash
# Run integration tests
python -m pytest tests/test_frame_extractor_integration.py -v
```

#### Visual Verification Tests
**Requirements:**
- Real video file: `examples/ship.mp4`
- Write permissions in `test_output/` directory

**Test what they do:**
- Save 75 actual extracted frames to disk for manual inspection
- **Automated quantitative validation**: frame count, resolution, tensor format, file validity
- Verify frame distribution, quality, and sequence continuity
- Output location: `test_output/frame_extraction_visual/`

```bash
# Run visual tests (creates files on disk + quantitative validation)
python -m pytest tests/test_frame_extractor_visual.py -v

# View saved frames
ls test_output/frame_extraction_visual/
```

#### AI Visual Verification Tests
**Requirements:**
- Ollama service running: `sudo systemctl start ollama` or `ollama serve`
- qwen2.5vl:7b model installed: `ollama pull qwen2.5vl:7b`
- Real video file: `examples/ship.mp4`

**Test what they do:**
- **AI-powered content validation** using qwen2.5vl:7b model (same as PromptOptimizer)
- Automated analysis of 1, 3, and 5 extracted frames
- Verify frame quality, clarity, motion progression, and content
- No manual inspection needed - AI provides detailed descriptions

```bash
# Check Ollama is ready
curl http://localhost:11434/api/version

# Run AI visual verification tests
python -m pytest tests/test_frame_extractor_ai.py -v
```

#### Hunyuan3D Integration Tests
**Requirements:**
- Conda environment named `hunyuan3d`: `conda create -n hunyuan3d python=3.10`
- Hunyuan3D dependencies installed: `conda run -n hunyuan3d pip install -r external/Hunyuan3D-2.1/requirements.txt`
- Blender installed: `sudo snap install blender --classic`
- Test image: `examples/input_images/single_view/railgun/frame_001_4x.png` (included)
- **21GB+ VRAM** for textured generation (shape-only test uses ~10GB)

**Test what they do:**
- **Real subprocess execution**: Actual `conda run -n hunyuan3d blender --background --python` calls
- **File generation verification**: Creates and validates OBJ, STL, and GLB files
- **Shape-only generation**: Fast test (~2-5 min) that generates OBJ/STL files
- **Textured generation**: Full pipeline test (skipped by default due to time/memory requirements)
- **Dependency validation**: Verifies conda environment and import capabilities

```bash
# Check dependencies
conda env list | grep hunyuan3d
blender --version

# Run integration tests (shape-only, fast)
python -m pytest tests/test_hunyuan3d_integration.py -v

# Run specific shape-only test
python -m pytest tests/test_hunyuan3d_integration.py::TestHunyuan3D21Integration::test_shape_only_generation_real_execution -v

# Check generated files
ls test_output/hunyuan3d_integration/
```

**IMPORTANT**: The textured generation test is skipped by default because it:
- Requires 21GB+ VRAM
- Takes 10-30 minutes to complete  
- To enable: Remove `@unittest.skip` decorator from `test_textured_generation_real_execution`

### Advanced Conda Testing

#### Testing Conda Integration (Mocked)
```bash
# Test conda detection and validation (mocked)
python -m pytest tests/test_hunyuan3d.py::TestHunyuan3D21Node::test_conda_environment_validation -v

# Test conda command execution (mocked subprocess calls)
python -m pytest tests/test_hunyuan3d.py::TestHunyuan3D21Node::test_successful_3d_generation -v
```

#### Conda-Specific Test Features

The Hunyuan3D tests include conda-aware functionality:

**Environment Separation**:
- **ComfyUI Environment**: Your actual ComfyUI conda environment for running tests and ComfyUI simulation
- **Subprocess Environment**: `hunyuan3d` for simulating actual Hunyuan3D execution via `conda run`
- **Why Subprocess**: ComfyUI's virtual environment often conflicts with Hunyuan3D's PyTorch/CUDA requirements, so subprocess execution escapes ComfyUI's environment constraints
- Tests run from ComfyUI environment but simulate subprocess calls to hunyuan3d environment

**Conda Environment Detection**:
- Tests validate conda environment configuration
- Mocks `conda run -n hunyuan3d` command execution
- Verifies proper conda path and environment name handling

**Blender Integration Testing**:
- Simulates `conda run -n hunyuan3d blender --background --python script.py`
- Tests script execution and output file generation
- Handles expected segfault behavior (normal for Blender texture painting)

**Environment Variable Testing**:
```bash
# Test custom conda configuration
HUNYUAN3D_CONDA_ENV=my_env HUNYUAN3D_CONDA_PATH=/custom/conda python -m pytest tests/test_hunyuan3d.py -v

# Test custom Ollama server configuration
OLLAMA_HOST=192.168.1.100:11434 python -m pytest tests/test_prompt_optimizer.py -v

# Test both custom configurations
HUNYUAN3D_CONDA_ENV=my_env OLLAMA_HOST=localhost:11435 python -m pytest tests/ -v
```

### Run Specific Test Classes or Methods
```bash
# Run a specific test class
python -m pytest tests/test_frame_extractor.py::TestVideoFrameExtractorNode -v

# Run a specific test method
python -m pytest tests/test_hunyuan3d.py::TestHunyuan3D21Node::test_successful_3d_generation -v
```

### Test Output Options
```bash
# Minimal output (quiet mode)
python -m pytest tests/ -q

# Detailed failure information
python -m pytest tests/ -v --tb=long

# Stop on first failure
python -m pytest tests/ -x
```

## ComfyUI Simulation Framework

The tests use a custom simulation framework (`tests/comfyui_mock.py`) that properly simulates ComfyUI's execution environment:

### Key Features
- **MockVideoInput**: Simulates ComfyUI's VideoInput objects with `get_components()` method
- **MockFolderPaths**: Provides temporary output directories matching ComfyUI structure  
- **Tensor Creation**: Creates properly formatted ComfyUI tensors `(batch, height, width, channels)` in float32 [0,1]
- **Context Management**: Handles test environment setup/cleanup automatically
- **Node Execution Simulation**: `simulate_comfyui_execution()` calls node methods exactly as ComfyUI would

### Usage in Tests
```python
from tests.comfyui_mock import ComfyUIMockContext, MockComfyUINode

class TestMyNode(unittest.TestCase, MockComfyUINode):
    def setUp(self):
        self.context = self.setup_test_environment()
        self.context.__enter__()
        
    def test_node_execution(self):
        result = self.simulate_comfyui_execution(
            node_instance, "method_name", **kwargs
        )
```

## Test Coverage by Node

### VideoFrameExtractor Tests (25+ tests)
**Unit Tests (10 tests)**:
- **Frame Extraction Logic**: Evenly distributed frame sampling, skip parameters
- **Tensor Handling**: ComfyUI VIDEO input processing, proper tensor output format
- **Edge Cases**: Single frame videos, invalid parameters, large datasets
- **Error Handling**: Invalid tensor shapes, parameter validation
- **Integration**: Node registration, ComfyUI compatibility

**Integration Tests (10 tests)** - Real video execution:
- **Actual Frame Extraction**: Loads real video file (`examples/ship.mp4`)
- **Count Verification**: Ensures correct number of frames extracted (81 total frames)
- **Resolution Verification**: Confirms 640x640 resolution maintained
- **Quality Verification**: Validates frame content and variation
- **Performance Testing**: Measures extraction speed (3000+ fps)
- **Edge Case Handling**: First/last frames, large requests, invalid parameters

**Visual Verification Tests (5 tests)** - Saves frames to disk:
- **Frame Distribution**: Saves 5, 10, 20 evenly distributed frames
- **Skip Comparison**: Saves frames with/without start/end skipping
- **Sequence Continuity**: Saves 16 frames to verify motion continuity  
- **Resolution Verification**: Saves frames with resolution info in filename
- **Edge Cases**: First frame, last frame, middle frames

All extracted frames saved to: `test_output/frame_extraction_visual/`

### Hunyuan3D Tests (17 tests) 
- **Subprocess Execution**: Conda environment handling, Blender execution simulation
- **File I/O**: Image saving, output file generation, cleanup operations
- **Configuration**: Environment variables, custom conda paths, parameter validation
- **Error Scenarios**: Timeout handling, failed generation, segmentation fault handling  
- **Integration**: Node registration, execution script validation

### PromptOptimizer Tests (24 tests)
- **Ollama Integration**: API calls, response handling, error scenarios
- **Model Configurations**: Config file loading, negative prompt support validation
- **Image Processing**: Tensor format handling, temporary file management
- **ComfyUI Simulation**: Complete workflow execution with all parameters
- **Edge Cases**: Empty responses, connection failures, unknown models

## Test Status

**Current Status: ✅ All 85+ tests passing**
- **Unit Tests**: 51 tests (ComfyUI simulation) - discovered by `python -m pytest tests/`
- **Integration Tests**: 25+ tests (real execution - 10 Frame Extractor + 11 Prompt Optimizer + 4 Hunyuan3D) - require explicit pattern
- **Visual Verification**: 5+ tests (saves frames + quantitative validation) - require explicit pattern
- **AI Visual Verification**: 4 tests (AI-powered content analysis) - require explicit pattern

**Key Point**: All tests now follow standard pytest naming (`test_*.py`) and are discovered automatically. Integration and visual tests are distinguished by descriptive suffixes.

To verify current test status:
```bash
# All tests (85+ tests) - now discovers everything automatically
python -m pytest tests/ -v

# Unit tests only (fast, 51 tests)
python -m pytest tests/test_frame_extractor.py tests/test_hunyuan3d.py tests/test_prompt_optimizer.py -v

# Integration tests only (requires external services)
python -m pytest tests/test_*_integration.py -v

# Visual verification tests only (saves frames to disk + quantitative validation)
python -m pytest tests/test_*_visual.py -v

# AI visual verification tests only (AI-powered analysis)
python -m pytest tests/test_*_ai.py -v
```

Expected output for unit tests only:
```
============================== test session starts ==============================
...
============================== 51 passed in ~4s ==============================
```

Expected output for all tests:
```
============================== test session starts ==============================
...
============================== 85+ passed in ~45s ==============================
```

## Key Test Features

### Proper ComfyUI Simulation
- Tests call node methods exactly as ComfyUI would during execution
- Uses correct tensor formats: `(batch, height, width, channels)` in float32 [0,1]
- Simulates ComfyUI's VideoInput objects with proper `get_components()` API
- Mocks ComfyUI's folder_paths for realistic file handling

### External Dependency Mocking
- **Ollama API**: Complete mock client with realistic responses and token counts
- **Subprocess Execution**: Mock Blender/conda calls with configurable success/failure
- **File I/O**: Mock file operations while testing actual logic paths
- **Network Calls**: No real network requests during testing

### Comprehensive Coverage
- **Happy Path**: Normal successful execution scenarios  
- **Error Handling**: Network failures, invalid inputs, missing dependencies
- **Edge Cases**: Empty responses, large datasets, boundary conditions
- **Integration**: Node registration, ComfyUI compatibility

## Writing New Tests

### Basic Test Structure
```python
import unittest
from tests.comfyui_mock import ComfyUIMockContext, MockComfyUINode
from nodes.your_node.your_node_file import YourNodeClass

class TestYourNode(unittest.TestCase, MockComfyUINode):
    def setUp(self):
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.node = YourNodeClass()
    
    def tearDown(self):
        self.context.__exit__(None, None, None)
    
    def test_your_functionality(self):
        result = self.simulate_comfyui_execution(
            self.node, "your_method_name", 
            param1="value1", param2="value2"
        )
        self.assertEqual(result, expected_result)
```

### Test Data Creation
```python
from tests.comfyui_mock import create_test_image_tensor, create_test_video_input

# Create ComfyUI-format test images
test_image = create_test_image_tensor(batch_size=1, height=256, width=256)

# Create ComfyUI-format test video
test_video = create_test_video_input(num_frames=30, height=480, width=640)
```

## Conda Testing Best Practices

### Development Workflow
```bash
# 1. Activate ComfyUI's conda environment (replace with your actual ComfyUI environment name)
conda activate comfyui

# 2. Install testing dependencies in ComfyUI environment
pip install -r requirements-test.txt

# 3. Set up separate Hunyuan3D environment (for subprocess simulation)
conda create -n hunyuan3d python=3.10 -y
conda run -n hunyuan3d pip install -r external/Hunyuan3D-2.1/requirements.txt

# 4. Run comprehensive tests (from ComfyUI environment)
python -m pytest tests/ -v --tb=short

# 5. Test conda-specific functionality
python -m pytest tests/test_hunyuan3d.py -v -k "conda"

# 6. Test with remote Ollama server (if available)
OLLAMA_HOST=your-ollama-server:11434 python -m pytest tests/test_prompt_optimizer.py -v
```

### CI/CD Integration
For automated testing pipelines:
```bash
# Set up ComfyUI testing environment
conda create -n comfyui-test python=3.10 -y

# Install testing dependencies
conda run -n comfyui-test pip install -r requirements-test.txt

# Set up Hunyuan3D subprocess environment
conda create -n hunyuan3d python=3.10 -y
conda run -n hunyuan3d pip install -r external/Hunyuan3D-2.1/requirements.txt

# Run tests from ComfyUI environment
conda run -n comfyui-test python -m pytest tests/ -v

# Clean up
conda env remove -n comfyui-test -y
conda env remove -n hunyuan3d -y
```

### Debugging Conda Issues
```bash
# Check conda installation and environments
conda info
conda env list

# Test conda command availability
which conda
conda --version

# Validate environment variables
echo $HUNYUAN3D_CONDA_ENV
echo $HUNYUAN3D_CONDA_PATH
echo $OLLAMA_HOST

# Test Blender availability in Hunyuan3D subprocess environment
conda run -n hunyuan3d blender --version

# Verify both environments exist
conda activate comfyui            # ComfyUI testing environment
conda activate hunyuan3d          # Subprocess simulation environment
```

## Troubleshooting

### Common Issues

**ImportError: No module named 'nodes'**
- Run from project root: `cd /home/matt/src/comfyui-ai-gamedev && python -m pytest tests/`

**Tensor shape/format errors**  
- Ensure test data uses ComfyUI format: `(batch, height, width, channels)`
- Use `create_test_image_tensor()` helper functions

**Mock not working**
- Verify patch path matches actual import path in node code
- Check mock is applied before node method execution

### Conda-Specific Issues

**"conda: command not found"**
```bash
# Add conda to PATH
export PATH="$HOME/miniconda3/bin:$PATH"
# Or use full path in tests
HUNYUAN3D_CONDA_PATH="/home/user/miniconda3/bin/conda" python -m pytest tests/
```

**pip install error (missing -r flag)**
```bash
# ❌ Wrong (tries to install package named "requirements-test.txt")
pip install requirements-test.txt

# ✅ Correct (reads requirements from file)
pip install -r requirements-test.txt
```

**Ollama connection issues**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Test with custom host
OLLAMA_HOST=localhost:11435 curl http://localhost:11435/api/version

# Test remote Ollama server
OLLAMA_HOST=192.168.1.100:11434 python -m pytest tests/test_prompt_optimizer.py::TestPromptOptimizer::test_basic_optimization -v

# Debug connection issues
export OLLAMA_HOST=your-server:11434
python -c "import os; print(f'OLLAMA_HOST: {os.getenv(\"OLLAMA_HOST\", \"localhost:11434\")}')"
```

**"Environment 'hunyuan3d' not found"**
```bash
# Create the subprocess environment
conda create -n hunyuan3d python=3.10 -y
conda run -n hunyuan3d pip install -r external/Hunyuan3D-2.1/requirements.txt
# Or test with custom environment name
HUNYUAN3D_CONDA_ENV=my-test-env python -m pytest tests/
```

**"ComfyUI environment not found"**
```bash
# If you don't have ComfyUI in conda, create a test environment
conda create -n comfyui python=3.10 -y
conda activate comfyui
pip install -r requirements-test.txt

# Install ComfyUI dependencies (if needed)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Blender segfault errors**
- This is expected behavior in Hunyuan3D texture painting
- Tests verify output files are created before segfault
- Use mocked tests to avoid actual Blender execution during development

## Best Practices

1. **Use the ComfyUI simulation framework** - Don't test in isolation
2. **Mock external dependencies** - Ollama, subprocess, file I/O
3. **Test both success and failure paths** - Don't just test happy scenarios  
4. **Include edge cases** - Empty inputs, large datasets, boundary conditions
5. **Test actual return values** - Not just success/failure, verify data correctness
6. **Clean up resources** - Use setUp/tearDown for proper cleanup

This comprehensive test suite ensures all nodes work reliably in the real ComfyUI environment.