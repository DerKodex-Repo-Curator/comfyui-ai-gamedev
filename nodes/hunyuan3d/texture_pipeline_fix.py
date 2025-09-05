"""
Fix for Hunyuan3D texture pipeline bug where image_prompt is referenced before assignment
"""
import torch
from PIL import Image
from typing import List

def fixed_texture_pipeline_call(self, mesh_path=None, image_path=None, output_mesh_path=None, use_remesh=True, save_glb=True):
    """Fixed version of Hunyuan3DPaintPipeline.__call__ that properly handles image_path"""
    import os
    from hy3dpaint.utils.mesh_remesh import remesh_mesh
    
    # Fix the image_prompt bug
    if isinstance(image_path, str):
        # Single image path string
        image_prompt = Image.open(image_path)
    elif isinstance(image_path, Image.Image):
        # Single PIL Image
        image_prompt = image_path
    elif isinstance(image_path, list):
        # List of paths or images
        if len(image_path) > 0 and isinstance(image_path[0], str):
            # List of paths - load them
            image_prompt = [Image.open(p) if isinstance(p, str) else p for p in image_path]
        else:
            # List of PIL Images
            image_prompt = image_path
    else:
        # Fallback
        image_prompt = image_path
    
    # Ensure image_prompt is a list
    if not isinstance(image_prompt, list):
        image_prompt = [image_prompt]
    
    # Process mesh
    path = os.path.dirname(mesh_path)
    if use_remesh:
        processed_mesh_path = os.path.join(path, "white_mesh_remesh.obj")
        remesh_mesh(mesh_path, processed_mesh_path)
    else:
        processed_mesh_path = mesh_path
    
    # Output path
    if output_mesh_path is None:
        base = os.path.splitext(os.path.basename(mesh_path))[0]
        output_mesh_path = os.path.join(path, f"{base}_texture.glb" if save_glb else f"{base}_texture.obj")
    
    # Call the original texture generation method
    return self._original_generate_texture(
        processed_mesh_path, 
        image_prompt, 
        output_mesh_path,
        save_glb=save_glb
    )

def apply_texture_pipeline_fix():
    """Apply the fix by monkey-patching the buggy method"""
    try:
        from textureGenPipeline import Hunyuan3DPaintPipeline
        
        # Save the original generate_texture method
        if not hasattr(Hunyuan3DPaintPipeline, '_original_generate_texture'):
            # Find the actual texture generation method
            # The __call__ method delegates to internal methods
            # We need to preserve the original logic after our fix
            original_call = Hunyuan3DPaintPipeline.__call__
            
            def wrapped_call(self, mesh_path=None, image_path=None, output_mesh_path=None, use_remesh=True, save_glb=True):
                """Wrapper that fixes the image_path handling"""
                # Apply our fix
                import os
                from hy3dpaint.utils.mesh_remesh import remesh_mesh
                
                # Fix the image_prompt bug
                if isinstance(image_path, str):
                    image_prompt = Image.open(image_path)
                elif isinstance(image_path, Image.Image):
                    image_prompt = image_path
                elif isinstance(image_path, list):
                    if len(image_path) > 0 and isinstance(image_path[0], str):
                        image_prompt = [Image.open(p) if isinstance(p, str) else p for p in image_path]
                    else:
                        image_prompt = image_path
                else:
                    image_prompt = image_path
                
                if not isinstance(image_prompt, list):
                    image_prompt = [image_prompt]
                
                # Process mesh
                path = os.path.dirname(mesh_path)
                if use_remesh:
                    processed_mesh_path = os.path.join(path, "white_mesh_remesh.obj")
                    remesh_mesh(mesh_path, processed_mesh_path)
                else:
                    processed_mesh_path = mesh_path
                
                # Output path
                if output_mesh_path is None:
                    base = os.path.splitext(os.path.basename(mesh_path))[0]
                    output_mesh_path = os.path.join(path, f"{base}_texture.glb" if save_glb else f"{base}_texture.obj")
                
                # Call the texture generation
                return self.generate_texture(processed_mesh_path, image_prompt, output_mesh_path, save_glb=save_glb)
            
            # Replace the buggy __call__ with our fixed version
            wrapped_call = torch.no_grad()(wrapped_call)
            Hunyuan3DPaintPipeline.__call__ = wrapped_call
            
        print("✓ Applied texture pipeline image_path fix")
        return True
    except Exception as e:
        print(f"⚠️ Could not apply texture pipeline fix: {e}")
        return False