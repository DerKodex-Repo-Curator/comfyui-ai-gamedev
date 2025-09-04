#!/usr/bin/env python3
"""
Permanent script for texture painting using Hunyuan3D
This script is executed inside Blender's Python environment
"""

import sys
import os
import json
import argparse
from pathlib import Path
from PIL import Image

def main():
    # When run in Blender, sys.argv includes Blender's args before the double dash
    # Find the double dash and only parse args after it
    import sys
    if "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        argv = sys.argv[1:]
    
    parser = argparse.ArgumentParser(description="Paint textures on 3D mesh")
    parser.add_argument("--mesh", required=True, help="Path to input mesh file")
    parser.add_argument("--images", required=True, help="JSON array of image paths")
    parser.add_argument("--output", required=True, help="Path to output GLB file")
    parser.add_argument("--resolution", type=int, default=1024, help="Texture resolution")
    parser.add_argument("--steps", type=int, default=50, help="Inference steps")
    args = parser.parse_args(argv)
    
    # Use offline mode for HuggingFace to avoid SSL issues
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    
    # Setup paths
    sys.path.insert(0, 'external/Hunyuan3D-2.1')
    sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dshape')
    sys.path.insert(0, 'external/Hunyuan3D-2.1/hy3dpaint')
    
    # Apply torchvision compatibility fix
    try:
        from hy3dpaint.utils.torchvision_fix import fix_torchvision_functional_tensor
        fix_torchvision_functional_tensor()
    except ImportError:
        try:
            from torchvision_fix import fix_torchvision_functional_tensor
            fix_torchvision_functional_tensor()
        except ImportError:
            pass
    
    from textureGenPipeline import Hunyuan3DPaintPipeline, Hunyuan3DPaintConfig
    import tempfile
    import shutil
    
    # Parse image paths
    image_paths = json.loads(args.images)
    is_multi_view = len(image_paths) > 1
    
    print(f"\n🎨 Starting texture painting process...")
    print(f"  📷 Input images: {len(image_paths)} views")
    print(f"  📐 Resolution: {args.resolution}x{args.resolution}")
    print(f"  🔢 Inference steps: {args.steps}")
    print(f"  📁 Mesh path: {args.mesh}")
    
    print(f"\n⏳ Loading texture painting model...")
    paint_config = Hunyuan3DPaintConfig(
        max_num_view=len(image_paths),
        resolution=args.resolution
    )
    
    # Set config paths explicitly
    paint_config.multiview_cfg_path = "external/Hunyuan3D-2.1/hy3dpaint/cfgs/hunyuan-paint-pbr.yaml"
    paint_config.custom_pipeline = "external/Hunyuan3D-2.1/hy3dpaint/hunyuanpaintpbr"
    paint_config.realesrgan_ckpt_path = "external/Hunyuan3D-2.1/hy3dpaint/ckpt/RealESRGAN_x4plus.pth"
    
    paint_pipeline = Hunyuan3DPaintPipeline(paint_config)
    print(f"  ✅ Model loaded successfully")
    
    print(f"\n🎨 Starting texture painting with Blender...")
    print(f"  ⚙️  Running Blender in background mode...")
    
    # Use a temp directory for intermediate files
    temp_dir = tempfile.mkdtemp(prefix="hunyuan_paint_")
    try:
        # Run texture painting
        print(f"  🖌️  Painting textures (this may take several minutes)...")
        temp_glb_path = os.path.join(temp_dir, "textured_mesh.glb")
        
        textured_mesh = paint_pipeline(
            mesh_path=args.mesh,
            image_path=image_paths if is_multi_view else image_paths[0],
            output_mesh_path=temp_glb_path,
            use_remesh=True,
            save_glb=True
        )
        print(f"  ✅ Done painting textures!")
        print(f"  ✅ Texture painting completed successfully")
        
        # Copy the generated GLB file to final location
        if os.path.exists(temp_glb_path):
            print(f"  📁 Exporting GLB to output directory...")
            shutil.copy(temp_glb_path, args.output)
            print(f"  ✅ Saved textured GLB: {args.output}")
            # Get file size for verification
            size_mb = os.path.getsize(args.output) / (1024 * 1024)
            print(f"  📊 File size: {size_mb:.2f} MB")
            print(f"  ✅ Export completed successfully!")
        else:
            print("  ❌ Warning: No GLB file generated")
    finally:
        # Clean up temp directory
        print(f"  🧹 Cleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    print(f"\n✨ Texture painting workflow complete!")
    print("="*50)
    print("Note: Blender may crash on exit - this is a known bug.")
    print("The texture painting has already completed successfully.")
    print("="*50)

if __name__ == "__main__":
    main()