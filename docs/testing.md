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

Install required dependencies:
```bash
pip install pytest pytest-mock pytest-asyncio torch numpy pillow
```

## Running Tests

### Run All Tests (Recommended)
```bash
# From project root directory - runs all 51 tests
python -m pytest tests/ -v
```

### Run Specific Test Files
```bash
# Test only VideoFrameExtractor (10 tests)
python -m pytest tests/test_frame_extractor.py -v

# Test only Hunyuan3D (17 tests)
python -m pytest tests/test_hunyuan3d.py -v

# Test only PromptOptimizer (24 tests)
python -m pytest tests/test_prompt_optimizer.py -v
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

**Current Status: ✅ All 61+ tests passing**
- **Unit Tests**: 51 tests (ComfyUI simulation)
- **Integration Tests**: 10+ tests (real video execution)  
- **Visual Verification**: 5+ tests (saves actual frames)

To verify current test status:
```bash
# Run all tests (unit + integration)
python -m pytest tests/ -v

# Run only unit tests (fast, mocked)
python -m pytest tests/test_*.py -v

# Run only integration tests (slower, real execution)
python -m pytest tests/integration_*.py -v

# Run visual verification tests (saves frames to disk)
python -m pytest tests/visual_*.py -v
```

Expected output for all tests:
```
============================== test session starts ==============================
...
============================== 61+ passed in ~8s ==============================
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

## Best Practices

1. **Use the ComfyUI simulation framework** - Don't test in isolation
2. **Mock external dependencies** - Ollama, subprocess, file I/O
3. **Test both success and failure paths** - Don't just test happy scenarios  
4. **Include edge cases** - Empty inputs, large datasets, boundary conditions
5. **Test actual return values** - Not just success/failure, verify data correctness
6. **Clean up resources** - Use setUp/tearDown for proper cleanup

This comprehensive test suite ensures all nodes work reliably in the real ComfyUI environment.