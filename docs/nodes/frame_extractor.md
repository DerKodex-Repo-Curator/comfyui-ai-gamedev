# Frame Extractor Node

## Overview
The Frame Extractor node extracts evenly-spaced frames from video files, useful for creating multi-view inputs for 3D reconstruction or animation analysis. It intelligently samples frames while preserving the full range of motion by excluding specified start/end frames and distributing extraction points evenly across the remaining video.

## Features
- **Smart Frame Distribution**: Evenly samples frames across the video duration
- **Range Preservation**: Maintains full motion range while reducing frame count
- **Flexible Trimming**: Skip unwanted frames at start/end (logos, credits, etc.)
- **Batch Output**: Returns frames as ComfyUI IMAGE batch tensor
- **Memory Efficient**: Reads frames sequentially without loading entire video

## Installation

### Requirements
- Python 3.8+
- OpenCV (cv2): `pip install opencv-python>=4.8.0`
- NumPy (usually included with ComfyUI)
- PyTorch (usually included with ComfyUI)

### Quick Install
```bash
pip install opencv-python
```

## Node Parameters

### Inputs
| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `video` | STRING | "" | - | Path to video file (absolute or relative) |
| `frame_count` | INT | 10 | 1-100 | Number of frames to extract |
| `skip_start_frames` | INT | 0 | 0-1000 | Frames to skip at video start |
| `skip_end_frames` | INT | 0 | 0-1000 | Frames to skip at video end |

### Outputs
| Name | Type | Description |
|------|------|-------------|
| `frames` | IMAGE | Batch tensor of extracted frames (B, H, W, C) |

## Usage Examples

### Basic Frame Extraction
Extract 10 evenly-spaced frames from entire video:
```
video: "path/to/video.mp4"
frame_count: 10
skip_start_frames: 0
skip_end_frames: 0
```

### Skip Intro/Outro
Extract frames excluding 30-frame intro and 60-frame outro:
```
video: "path/to/video.mp4"
frame_count: 8
skip_start_frames: 30
skip_end_frames: 60
```

### Multi-View for 3D
Extract frames for Hunyuan3D multi-view reconstruction:
```
video: "turntable_video.mp4"
frame_count: 10  # Hunyuan3D accepts up to 10 views
skip_start_frames: 5  # Skip acceleration
skip_end_frames: 5    # Skip deceleration
```

## Frame Distribution Algorithm

The node uses intelligent frame distribution:

1. **Calculate usable range**: `total_frames - skip_start - skip_end`
2. **Compute step size**: `(usable_frames - 1) / (frame_count - 1)`
3. **Select frame indices**: Evenly distributed across usable range
4. **Extract frames**: Read only selected frames (memory efficient)

Example with 100-frame video, extracting 5 frames, skipping 10 start/end:
- Usable range: frames 10-89 (80 frames)
- Step size: 80/4 = 20
- Extracted indices: [10, 30, 50, 70, 89]

## Integration with Other Nodes

### Hunyuan3D Multi-View Pipeline
```
Frame Extractor → Hunyuan3D Shape → Hunyuan3D Paint
```

### Animation Analysis
```
Frame Extractor → Image Grid → Save Image
```

### Batch Processing
```
Frame Extractor → Image Batch → [Various Processing Nodes]
```

## Supported Video Formats

The node supports all formats readable by OpenCV:
- **Common**: MP4, AVI, MOV, MKV, WebM
- **Professional**: ProRes, DNxHD (with appropriate codecs)
- **Image Sequences**: Numbered frame sequences

## Performance Considerations

### Memory Usage
- Only loads one frame at a time during extraction
- Output tensor size: `frame_count × height × width × 3 × 4 bytes`
- Example: 10 frames @ 1920×1080 = ~250MB

### Processing Speed
- Depends on video codec and resolution
- Sequential frame seeking may be slow for some codecs
- Consider pre-converting to efficient codec (H.264) for repeated use

## Troubleshooting

### Common Issues

**"Video file not found"**
- Check file path is correct
- Use absolute paths when possible
- Ensure file permissions allow reading

**"Could not open video file"**
- Video codec may not be supported
- Install additional codecs: `pip install opencv-contrib-python`
- Try converting video to standard format (MP4/H.264)

**"No frames remaining after skipping"**
- Reduce `skip_start_frames` and `skip_end_frames`
- Check total video frame count
- Ensure video has sufficient frames

**Extracted frames appear corrupted**
- Video file may be damaged
- Try re-encoding: `ffmpeg -i input.mp4 -c:v libx264 output.mp4`
- Check source video plays correctly

### Debug Logging

Enable detailed logging to diagnose issues:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Logs will show:
- Total frames in video
- Frame indices being extracted  
- Warnings for failed frame reads

## Advanced Usage

### Custom Frame Selection
While the node automatically distributes frames evenly, you can achieve custom patterns by chaining multiple extractors:

```
Extractor1 (first half) → 
                          → Combine → Process
Extractor2 (second half) →
```

### Pre-processing for Quality
For best results with 3D reconstruction:
1. Ensure stable camera motion (no shake)
2. Use consistent lighting
3. Avoid motion blur (higher shutter speed)
4. Maintain subject in frame throughout

## Limitations

- Maximum 100 frames per extraction (adjustable in code)
- No built-in video stabilization
- Sequential frame access (may be slow for some codecs)
- Requires video file path (no direct video upload in ComfyUI)

## Future Enhancements

Planned improvements:
- [ ] Direct video upload support
- [ ] GPU-accelerated decoding
- [ ] Motion-based frame selection (select frames with most change)
- [ ] Automatic quality assessment
- [ ] Built-in stabilization option
- [ ] Frame interpolation for smooth slow-motion

## Example Workflow

See `workflows/frame_extractor_example.json` for a complete example that:
1. Loads ship.mp4 sample video
2. Extracts 10 frames skipping start/end
3. Displays frames in preview
4. Saves extracted frames to disk