import cv2
import numpy as np
import torch
from typing import Tuple
import os
import logging

logger = logging.getLogger(__name__)


class FrameExtractorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video": ("STRING", {"default": "", "multiline": False}),
                "frame_count": ("INT", {"default": 10, "min": 1, "max": 100, "step": 1}),
                "skip_start_frames": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
                "skip_end_frames": ("INT", {"default": 0, "min": 0, "max": 1000, "step": 1}),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("frames",)
    FUNCTION = "extract_frames"
    CATEGORY = "gamedev/video"
    OUTPUT_NODE = False

    def extract_frames(self, video: str, frame_count: int, skip_start_frames: int, skip_end_frames: int) -> Tuple[torch.Tensor]:
        if not video or not os.path.exists(video):
            raise ValueError(f"Video file not found: {video}")
        
        cap = cv2.VideoCapture(video)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video}")
        
        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames <= 0:
                raise ValueError("Could not determine video frame count")
            
            usable_start = skip_start_frames
            usable_end = total_frames - skip_end_frames
            usable_frame_count = usable_end - usable_start
            
            if usable_frame_count <= 0:
                raise ValueError(f"No frames remaining after skipping {skip_start_frames} start and {skip_end_frames} end frames from {total_frames} total")
            
            if frame_count > usable_frame_count:
                logger.warning(f"Requested {frame_count} frames but only {usable_frame_count} available. Using all available frames.")
                frame_count = usable_frame_count
            
            if frame_count == usable_frame_count:
                frame_indices = list(range(usable_start, usable_end))
            else:
                step = (usable_frame_count - 1) / (frame_count - 1) if frame_count > 1 else 0
                frame_indices = [int(usable_start + i * step) for i in range(frame_count)]
            
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Could not read frame {idx}")
                    continue
                
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame_normalized = frame_rgb.astype(np.float32) / 255.0
                frames.append(frame_normalized)
            
            if not frames:
                raise ValueError("No frames could be extracted from the video")
            
            frames_tensor = torch.from_numpy(np.stack(frames, axis=0))
            
            logger.info(f"Extracted {len(frames)} frames from video (skipped {skip_start_frames} start, {skip_end_frames} end)")
            logger.info(f"Frame indices used: {frame_indices[:5]}{'...' if len(frame_indices) > 5 else ''}")
            
            return (frames_tensor,)
            
        finally:
            cap.release()