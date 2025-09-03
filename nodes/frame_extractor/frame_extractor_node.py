import numpy as np
import torch
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class VideoFrameExtractorNode:
    """
    Extract frames from video at specified intervals
    Takes VIDEO output from LoadVideo node
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("VIDEO",),  # Takes VIDEO output from LoadVideo
                "frame_count": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "skip_start_frames": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "skip_end_frames": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("frames", "total_frames", "extracted_count")
    FUNCTION = "extract_frames"
    CATEGORY = "🎮 AI GameDev/Video"
    OUTPUT_NODE = False

    def extract_frames(self, video, frame_count: int, skip_start_frames: int, skip_end_frames: int) -> Tuple[torch.Tensor]:
        """
        Extract frames from video at specified intervals
        
        Args:
            video: Video object from LoadVideo containing frames, audio, and metadata
            frame_count: Number of frames to extract (0 = all frames)
            skip_start_frames: Number of frames to skip at the start
            skip_end_frames: Number of frames to skip at the end
        
        Returns:
            Tuple containing batch of frames as tensor
        """
        # Extract components from VideoInput object
        components = video.get_components()
        images = components.images
        
        # Get dimensions from frames tensor
        if len(images.shape) == 4:
            total_frames, height, width, channels = images.shape
        elif len(images.shape) == 3:
            # Single frame
            total_frames = 1
            height, width, channels = images.shape
            images = images.unsqueeze(0)
        else:
            raise ValueError(f"Expected 3D or 4D tensor, got shape {images.shape}")
        
        logger.info(f"Processing video frames tensor: {total_frames} frames, {height}x{width}")
        
        usable_start = skip_start_frames
        usable_end = total_frames - skip_end_frames
        usable_frame_count = usable_end - usable_start
        
        if usable_frame_count <= 0:
            raise ValueError(f"No frames remaining after skipping {skip_start_frames} start and {skip_end_frames} end frames from {total_frames} total")
        
        # If frame_count is 0, extract all available frames
        if frame_count == 0:
            frame_count = usable_frame_count
            logger.info(f"frame_count=0, extracting all {frame_count} available frames")
        
        if frame_count > usable_frame_count:
            logger.warning(f"Requested {frame_count} frames but only {usable_frame_count} available. Using all available frames.")
            frame_count = usable_frame_count
        
        # Calculate which frames to extract
        if frame_count == usable_frame_count:
            frame_indices = list(range(usable_start, usable_end))
        else:
            step = (usable_frame_count - 1) / (frame_count - 1) if frame_count > 1 else 0
            frame_indices = [int(usable_start + i * step) for i in range(frame_count)]
        
        logger.info(f"Extracting {len(frame_indices)} frames from tensor")
        
        # Extract the selected frames from the tensor
        selected_frames = images[frame_indices]
        
        return (selected_frames, total_frames, len(frame_indices))
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # This could be optimized to detect when frame selection actually changes
        return float("nan")