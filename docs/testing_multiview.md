# Multiview Testing Guide

This guide explains how to test and compare single view vs multiview 3D generation results using Hunyuan3D 2.1.

## Overview

The multiview comparison test (`test_hunyuan3d_multiview_comparison.py`) allows you to:

1. **Compare single view vs 4-frame multiview generation**
2. **Analyze file size differences** between single and multiview results  
3. **Validate multiview detection logic** in the node
4. **Test with different frame selections** for multiview input

## Available Test Images

### Single View
- `examples/input_images/single_view/railgun/frame_001_4x.png` - Front view of a sci-fi railgun

### Multiview Set (10 frames total)
Located in `examples/input_images/multi_view/`:
- `frame_001_4x.png` - Front view (0°)
- `frame_006_4x.png` - ~54° rotation
- `frame_010_4x.png` - ~90° rotation 
- `frame_025_4x.png` - ~225° rotation
- `frame_033_4x.png` - ~297° rotation
- `frame_044_4x.png` - ~396° rotation (≈36°)
- `frame_053_4x.png` - ~477° rotation (≈117°)
- `frame_060_4x.png` - ~540° rotation (≈180°)
- `frame_069_4x.png` - ~621° rotation (≈261°)
- `frame_081_4x.png` - ~729° rotation (≈9°)

## Selected 4-Frame Test Set

The test uses these 4 evenly distributed frames:
```python
multiview_frames = [
    "frame_001_4x.png",  # Front view (0°)
    "frame_025_4x.png",  # Side view (~90°)
    "frame_044_4x.png",  # Back view (~180°) 
    "frame_069_4x.png"   # Side view (~270°)
]
```

This provides good 360° coverage with 4 views.

## Running the Tests

### Quick Validation (No GPU Required)
```bash
# Test that frames exist and are valid
python -m pytest tests/test_hunyuan3d_multiview_comparison.py::TestHunyuan3DMultiviewComparison::test_multiview_frame_validation -v

# Test multiview detection logic
python -m pytest tests/test_hunyuan3d_multiview_comparison.py::TestHunyuan3DMultiviewComparison::test_multiview_detection_logic -v
```

### Full Comparison Test (Requires 21GB VRAM + 10+ minutes)

1. **Enable the test** by removing the `@unittest.skip` decorator:
   ```python
   # In tests/test_hunyuan3d_multiview_comparison.py
   # Comment out or remove this line:
   # @unittest.skip("Enable manually for comparison testing - requires 21GB VRAM and 10+ minutes")
   def test_single_vs_multiview_comparison(self):
   ```

2. **Run the comparison**:
   ```bash
   python -m pytest tests/test_hunyuan3d_multiview_comparison.py::TestHunyuan3DMultiviewComparison::test_single_vs_multiview_comparison -v -s
   ```

3. **Results will be saved to**: `test_output/multiview_comparison/`

## Expected Results

### Performance Differences
- **Single view**: ~2-3 minutes generation time
- **Multiview (4 frames)**: ~5-7 minutes generation time
- **Memory usage**: Similar VRAM requirements

### Quality Differences
- **Single view**: Limited perspective, may miss details
- **Multiview**: Better 360° geometry, more complete reconstruction
- **File sizes**: Multiview models may be larger due to better detail

### Example Output Structure
```
test_output/multiview_comparison/
├── single_view_1737123456.glb     # Single view GLB
├── single_view_1737123456.obj     # Single view OBJ  
├── single_view_1737123456.stl     # Single view STL
├── multiview_4frames_1737123789.glb  # Multiview GLB
├── multiview_4frames_1737123789.obj  # Multiview OBJ
└── multiview_4frames_1737123789.stl  # Multiview STL
```

## Customizing the Test

### Using Different Frames
Edit the `multiview_frames` list in the test:
```python
# Try different frame combinations
multiview_frames = [
    "frame_001_4x.png",  # Front
    "frame_010_4x.png",  # Right side
    "frame_060_4x.png",  # Back  
    "frame_081_4x.png"   # Left side
]
```

### Testing Different Frame Counts
Modify the test to use 2, 3, 5, or more frames:
```python
# 2-frame test (front + back)
multiview_frames = ["frame_001_4x.png", "frame_060_4x.png"]

# 6-frame test (more coverage)
multiview_frames = [
    "frame_001_4x.png", "frame_010_4x.png", "frame_025_4x.png",
    "frame_044_4x.png", "frame_060_4x.png", "frame_069_4x.png"
]
```

## Analysis Tips

### Visual Comparison
1. **Load models in Blender/MeshLab** to compare geometry quality
2. **Check texture detail** - multiview should have better coverage
3. **Examine silhouettes** from different angles

### File Analysis
```bash
# Compare file sizes
ls -la test_output/multiview_comparison/

# Check model statistics with mesh tools
meshlab # Load and compare vertex/face counts
```

### Performance Monitoring
The test outputs timing information:
```
⏱️ single_view execution time: 156.7s
⏱️ multiview_4frames execution time: 387.2s
```

## Troubleshooting

### VRAM Issues
- Reduce resolution: `resolution="128"`, `texture_resolution="128"`
- Use fewer frames for multiview testing
- Close other GPU applications

### Long Execution Times  
- Reduce `inference_steps` to 5-8 for faster testing
- Use smaller resolutions for quick comparisons
- Test multiview detection without full generation

### Missing Dependencies
```bash
# Check requirements
conda env list | grep hunyuan3d
blender --version
```

## Expected Insights

After running the comparison, you should see:

1. **Geometry Quality**: Multiview models have better 360° shape accuracy
2. **Texture Coverage**: Multiview textures cover more of the model surface
3. **Detail Preservation**: Single view may miss details not visible in that angle
4. **File Size**: Multiview models are typically 10-30% larger
5. **Processing Time**: Multiview takes ~2-3x longer than single view

This comparison helps understand when to use single vs multiview generation based on your quality vs speed requirements.