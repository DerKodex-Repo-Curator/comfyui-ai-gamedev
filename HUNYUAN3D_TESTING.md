# Hunyuan3D Integration Testing Guide

## Prerequisites
1. Backend service running: `cd assets/backend && python main.py`
2. ComfyUI running: `sudo systemctl status comfyui`
3. Test images available in `/tmp/`

## Method 1: Direct Bash Script (Fastest, Always Works)

```bash
# Single image
./comfyui-hunyuan3d-shell/generate_3d.sh \
  /tmp/bomber_dev_1755660969_00.png \
  --output-dir /tmp/test_output \
  --quality enhanced \
  --views-per-model 1

# Multiple images for better quality (multi-view reconstruction)
./comfyui-hunyuan3d-shell/generate_3d.sh \
  /tmp/bomber_dev_1755660969_00.png \
  /tmp/bomber_krea_1755663881_03.png \
  /tmp/bomber_dev_1755661189_04.png \
  /tmp/bomber_dev_1755661408_08.png \
  /tmp/bomber_krea_1755663826_02.png \
  /tmp/bomber_krea_1755663990_05.png \
  --output-dir /tmp/multi_view_output \
  --quality enhanced \
  --views-per-model 6
```

Expected output:
- GLB file in output directory
- ~1.6MB file size
- Generation time: ~2 minutes

## Method 2: Backend HTTP Service (For Integration)

```bash
# Test backend is running
curl http://localhost:8000/api/hunyuan3d/status

# Generate via HTTP API
curl -X POST http://localhost:8000/api/hunyuan3d/generate \
  -F "files=@/tmp/bomber_dev_1755660969_00.png" \
  -F "quality=enhanced" \
  -F "output_name=test_http" \
  -F "views_per_model=1" \
  | python -m json.tool

# Download the generated GLB
curl http://localhost:8000/api/hunyuan3d/download/{glb_path} -o model.glb
```

## Method 3: ComfyUI Workflow (Full Pipeline)

### Step 1: Create workflow JSON
```json
{
  "1": {
    "inputs": {
      "image": "/tmp/bomber_dev_1755660969_00.png",
      "upload": "image"
    },
    "class_type": "LoadImage"
  },
  "2": {
    "inputs": {
      "images": ["1", 0],
      "resolution": 768,
      "num_inference_steps": 50,
      "output_name": "test_model",
      "backend_url": "http://localhost:8000"
    },
    "class_type": "Hunyuan3DHTTP"
  },
  "3": {
    "inputs": {
      "glb_path": ["2", 0],
      "destination_dir": "/tmp/comfyui_output",
      "filename": "final_model"
    },
    "class_type": "CopyGLBHTTP"
  }
}
```

### Step 2: Submit to ComfyUI
```python
import requests
import json

# Load workflow
with open('workflow.json', 'r') as f:
    workflow = json.load(f)

# Submit to ComfyUI
response = requests.post(
    'http://hugger:8188/prompt',
    json={'prompt': workflow}
)

prompt_id = response.json()['prompt_id']
print(f"Submitted: {prompt_id}")

# Monitor progress
import time
for i in range(60):
    time.sleep(5)
    history = requests.get(f'http://hugger:8188/history/{prompt_id}').json()
    if prompt_id in history:
        status = history[prompt_id]['status']['status_str']
        print(f"Status: {status}")
        if status in ['success', 'error']:
            break
```

## Quality Settings

| Quality | Shape Resolution | Inference Steps | Texture Resolution | Time | Use Case |
|---------|-----------------|-----------------|-------------------|------|----------|
| fast | 256px | 20 | 512px | ~1 min | Quick preview |
| standard | 512px | 30 | 768px | ~3 min | Testing |
| enhanced | 768px | 40 | 1024px | ~5 min | Production |
| high | 1024px | 50 | 1024px | ~7 min | High quality |
| ultra | 2048px | 60 | 2048px | ~10 min | Maximum quality |

Note: Only inference steps affect shape generation. Texture painting has no configurable steps.

## Troubleshooting

### Issue: "No GLB file generated"
- Check if conda environment is activated: `conda activate hunyuan3d`
- Verify models are cached: `ls ~/.cache/hy3dgen/`
- Check Blender installation: `blender --version`

### Issue: "Connection refused" from ComfyUI
- Ensure backend is running: `curl http://localhost:8000/api/hunyuan3d/status`
- Check ComfyUI has HTTP nodes: `curl http://hugger:8188/object_info | grep HTTP`
- Restart ComfyUI if needed: `sudo systemctl restart comfyui`

### Issue: "Segmentation fault" at end
- This is benign - happens after GLB is saved
- Check if GLB was generated: `ls -la /tmp/*/output/*.glb`

## Viewing Generated Models

```bash
# Find recent GLB files
find /tmp -name "*.glb" -mmin -10 -ls

# View with Blender
blender model.glb

# Or serve with HTTP server
python -m http.server 8080
# Then open http://localhost:8080 and use three.js viewer
```