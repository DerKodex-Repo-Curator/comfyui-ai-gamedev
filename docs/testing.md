# Testing Guide

This document describes the testing strategy and how to run tests for the ComfyUI AI GameDev nodes.

## Test Structure

Tests are located in the `/tests` directory:
- `test_hunyuan3d_node.py` - Tests for Hunyuan3D 2.1 node
- `test_frame_extractor.py` - Tests for Frame Extractor node

## Running Tests

### Run All Tests
```bash
python -m pytest tests/
```

### Run Specific Test File
```bash
python -m pytest tests/test_hunyuan3d_node.py
```

### Run with Verbose Output
```bash
python -m pytest tests/ -v
```

### Run Specific Test
```bash
python -m pytest tests/test_hunyuan3d_node.py::TestHunyuan3DNode::test_conditional_texture_generation_disconnected
```

## Test Coverage

### Hunyuan3D Node Tests

The Hunyuan3D node has comprehensive tests covering:

1. **Conditional Texture Generation** - CRITICAL TEST
   - `test_conditional_texture_generation_disconnected` - Verifies texture is NOT generated when output is disconnected (saves 11GB VRAM)
   - `test_conditional_texture_generation_connected` - Verifies texture IS generated when output is connected
   - `test_texture_disabled_by_parameter` - Verifies enable_texture parameter works

2. **Multi-View Detection**
   - Tests auto-detection of multi-view mode based on batch size
   - Tests forced single/multi modes
   - Validates batch size limits (1-10 images)

3. **Script Generation**
   - Tests that shape generation scripts are created correctly
   - Tests that texture painting scripts include proper parameters
   - Validates seed handling

4. **Node Configuration**
   - Tests INPUT_TYPES and RETURN_TYPES
   - Tests output format (STRING paths for Load3D compatibility)
   - Tests conda environment checking

### Frame Extractor Node Tests

The Frame Extractor node tests cover:

1. **Frame Distribution**
   - Tests that frames are extracted evenly across video duration
   - Tests skip_start_frames and skip_end_frames parameters

2. **Error Handling**
   - Tests handling of non-existent video files
   - Tests handling of corrupted/invalid videos
   - Tests frame count validation

3. **Output Format**
   - Tests tensor output format (batch, height, width, channels)
   - Tests value range normalization [0, 1]
   - Tests batch size matches requested frame count

## Important Test Cases

### Memory Management Test
The most critical test ensures texture generation only happens when needed:

```python
def test_conditional_texture_generation_disconnected(self):
    """Test that texture is NOT generated when textured_glb output is disconnected"""
    # This test verifies the 11GB VRAM saving optimization
```

This ensures the node respects ComfyUI's connection graph and doesn't waste resources.

### Integration Tests
Integration tests with real files are included but skipped if test assets don't exist:

```python
@unittest.skipUnless(
    Path("examples/input_images/single_view/railgun/frame_001_4x.png").exists(),
    "Test image not found"
)
def test_with_real_image(self):
    """Test with real image file (if available)"""
```

## Mocking Strategy

Tests use mocking to avoid dependencies on:
- Conda environment (mocked with `unittest.mock`)
- External Hunyuan3D models (script generation tested without execution)
- OpenCV/video files (mocked for unit tests, real files for integration)

## Adding New Tests

When adding new nodes, create corresponding test files:

1. Create `tests/test_<node_name>.py`
2. Test critical functionality:
   - Input/output types
   - Core processing logic
   - Error handling
   - Edge cases
3. Add integration tests with real data (use skipUnless)
4. Document any special requirements

## Continuous Integration

Currently tests are run manually. To add CI:
1. Add `.github/workflows/test.yml`
2. Install dependencies in CI
3. Run `pytest tests/` in workflow

## Test Requirements

```bash
pip install pytest pytest-mock
```

For integration tests:
- OpenCV: `pip install opencv-python`
- Test assets in `/examples/` directory