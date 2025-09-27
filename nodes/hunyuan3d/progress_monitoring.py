"""
Advanced progress monitoring for Hunyuan3D that hooks into actual pipeline progress
Monitors tqdm progress bars and pipeline internals for accurate progress tracking
"""

import time
import threading
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
try:
    from .progress_utils import LoggingProgressTracker, STAGE_ESTIMATES, STAGE_PERCENTAGES
except ImportError:
    # Fallback for direct script execution (e.g., via Blender)
    from progress_utils import LoggingProgressTracker, STAGE_ESTIMATES, STAGE_PERCENTAGES


class PipelineCallbackHook:
    """Hooks into diffusion pipeline callbacks to monitor real progress"""
    
    def __init__(self, callback: Callable[[int, int, str], None]):
        """
        Initialize callback hook
        
        Args:
            callback: Function called with (current_step, total_steps, description)
        """
        self.callback = callback
        self.current_stage = "unknown"
        self.total_steps = 0
    
    def set_stage_info(self, stage: str, total_steps: int):
        """Set stage information for progress calculation"""
        self.current_stage = stage
        self.total_steps = total_steps
    
    def create_callback(self, stage_name: str):
        """Create a callback function for the specific stage"""
        def pipeline_callback(pipeline, step, timestep, callback_kwargs):
            """Callback function for pipeline progress"""
            # Get total steps from pipeline if available
            total_steps = getattr(pipeline, '_num_timesteps', self.total_steps)
            try:
                self.callback(step + 1, total_steps, f"{stage_name} diffusion")
            except Exception as e:
                # Don't let callback errors break the pipeline
                print(f"Warning: Progress callback error: {e}")
            
            # Return callback_kwargs as required by diffusers pipeline
            return callback_kwargs
        
        return pipeline_callback


class ProgressMonitor:
    """Advanced progress monitor that tracks actual pipeline progress"""
    
    def __init__(self, progress_tracker: LoggingProgressTracker):
        """
        Initialize progress monitor
        
        Args:
            progress_tracker: Tracker to update with progress
        """
        self.progress_tracker = progress_tracker
        self.current_stage = None
        self.stage_start_time = None
        self.stage_substeps = {}
        self.callback_hook = None
    
    def start_stage(self, stage: str, message: str):
        """Start a new stage"""
        self.current_stage = stage
        self.stage_start_time = time.time()
        self.stage_substeps = {}
        
        # Get stage percentage range
        start_percent, end_percent = STAGE_PERCENTAGES.get(stage, (0, 0))
        
        self.progress_tracker.update_progress(
            stage=stage,
            percent=start_percent,
            message=message,
            estimated_total=STAGE_ESTIMATES["total"]
        )
        
        print(f"🔄 [{stage.upper()}] {message}")
    
    def update_stage_progress(self, stage: str, substep_percent: int, message: str):
        """Update progress within a stage"""
        if stage != self.current_stage:
            return
        
        # Calculate global percentage based on stage range
        start_percent, end_percent = STAGE_PERCENTAGES.get(stage, (0, 0))
        stage_range = end_percent - start_percent
        global_percent = start_percent + (stage_range * substep_percent // 100)
        
        self.progress_tracker.update_progress(
            stage=stage,
            percent=global_percent,
            message=message,
            estimated_total=STAGE_ESTIMATES["total"]
        )
        
        print(f"📊 [{stage.upper()}] {global_percent}% - {message}")
    
    def complete_stage(self, stage: str, message: str):
        """Complete a stage"""
        # Get final percentage for stage
        start_percent, end_percent = STAGE_PERCENTAGES.get(stage, (0, 0))
        
        self.progress_tracker.update_progress(
            stage=stage,
            percent=end_percent,
            message=message,
            estimated_total=STAGE_ESTIMATES["total"]
        )
        
        if self.stage_start_time:
            elapsed = time.time() - self.stage_start_time
            print(f"✅ [{stage.upper()}] {message} (took {elapsed:.1f}s)")
        else:
            print(f"✅ [{stage.upper()}] {message}")
        
        self.current_stage = None
        self.stage_start_time = None
    
    def monitor_shape_generation(self, pipeline, total_steps: int):
        """Monitor shape generation pipeline progress using callbacks"""
        def on_diffusion_progress(current: int, total: int, desc: str):
            if self.current_stage != "shape_generation":
                return
            
            # Calculate progress within shape generation stage (20% to 100% of stage)
            if total > 0:
                diffusion_percent = 20 + (current * 80) // total  # 20% to 100% of stage
                self.update_stage_progress(
                    "shape_generation",
                    diffusion_percent,
                    f"Diffusion sampling: {current}/{total} steps"
                )
        
        # Create callback hook for shape generation
        self.callback_hook = PipelineCallbackHook(on_diffusion_progress)
        self.callback_hook.set_stage_info("shape_generation", total_steps)
        
        return self.callback_hook.create_callback("shape_generation")
    
    def monitor_texture_painting(self, paint_pipeline):
        """Monitor texture painting pipeline progress using callbacks"""
        def on_texture_progress(current: int, total: int, desc: str):
            if self.current_stage != "texture_painting":
                return
            
            # Main diffusion sampling for texture painting (10-90% of texture stage)
            if total > 0:
                diffusion_percent = 10 + (current * 80) // total
                self.update_stage_progress(
                    "texture_painting",
                    diffusion_percent,
                    f"Texture diffusion: {current}/{total} steps"
                )
        
        # Create a NEW callback hook specifically for texture painting
        texture_callback_hook = PipelineCallbackHook(on_texture_progress)
        texture_callback_hook.set_stage_info("texture_painting", 15)  # Default steps
        
        return texture_callback_hook.create_callback("texture_painting")
    
    def cleanup(self):
        """Clean up monitoring hooks"""
        # No cleanup needed for callback approach
        self.callback_hook = None


@contextmanager
def monitor_pipeline_progress(progress_tracker: LoggingProgressTracker):
    """Context manager for pipeline progress monitoring"""
    monitor = ProgressMonitor(progress_tracker)
    try:
        yield monitor
    finally:
        monitor.cleanup()