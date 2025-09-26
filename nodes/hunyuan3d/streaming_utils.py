"""
Utilities for streaming subprocess progress from Hunyuan3D generation
"""

import subprocess
import threading
import re
import time
from typing import Callable, Optional, Dict, Any
from pathlib import Path


class ProgressParser:
    """Parse Hunyuan3D output for progress information"""
    
    # Progress patterns to match
    PATTERNS = {
        'shape_start': r'🔨 Step 1: Shape Generation',
        'shape_progress': r'Diffusion Sampling::\s*(\d+)%',
        'volume_progress': r'Volume Decoding:\s*(\d+)%',
        'texture_start': r'🎨 Step 2: Texture Painting',
        'pipeline_progress': r'Loading pipeline components\.\.\.\:\s*(\d+)%',
        'export_start': r'📦 Step 3: Exporting Formats',
        'complete': r'✅ GENERATION COMPLETE',
        'error': r'❌|ERROR|Error|Failed|failed',
    }
    
    def __init__(self):
        self.current_stage = "starting"
        self.last_progress = 0
        
    def parse_line(self, line: str) -> Dict[str, Any]:
        """Parse a line of output and return progress information"""
        line = line.strip()
        
        # Check for stage transitions
        if re.search(self.PATTERNS['shape_start'], line):
            self.current_stage = "shape_generation"
            return {'stage': 'shape_generation', 'progress': 0, 'message': 'Starting shape generation...'}
            
        elif re.search(self.PATTERNS['texture_start'], line):
            self.current_stage = "texture_painting"
            return {'stage': 'texture_painting', 'progress': 0, 'message': 'Starting texture painting...'}
            
        elif re.search(self.PATTERNS['export_start'], line):
            self.current_stage = "exporting"
            return {'stage': 'exporting', 'progress': 0, 'message': 'Exporting 3D models...'}
            
        elif re.search(self.PATTERNS['complete'], line):
            self.current_stage = "complete"
            return {'stage': 'complete', 'progress': 100, 'message': 'Generation complete!'}
        
        # Check for progress within current stage
        if self.current_stage == "shape_generation":
            # Diffusion sampling progress
            match = re.search(self.PATTERNS['shape_progress'], line)
            if match:
                progress = int(match.group(1))
                self.last_progress = progress
                return {'stage': 'shape_generation', 'progress': progress, 'message': f'Shape generation: {progress}%'}
            
            # Volume decoding progress
            match = re.search(self.PATTERNS['volume_progress'], line)
            if match:
                progress = int(match.group(1))
                # Volume decoding comes after diffusion, so add to base progress
                adjusted_progress = min(50 + (progress // 2), 99)  # Scale to 50-99%
                self.last_progress = adjusted_progress
                return {'stage': 'shape_generation', 'progress': adjusted_progress, 'message': f'Volume decoding: {progress}%'}
                
        elif self.current_stage == "texture_painting":
            # Pipeline loading progress
            match = re.search(self.PATTERNS['pipeline_progress'], line)
            if match:
                progress = int(match.group(1))
                self.last_progress = progress
                return {'stage': 'texture_painting', 'progress': progress, 'message': f'Loading paint pipeline: {progress}%'}
        
        # Check for errors
        if re.search(self.PATTERNS['error'], line):
            return {'stage': 'error', 'progress': -1, 'message': f'Error: {line}'}
        
        # Return current state if no specific progress found
        return {'stage': self.current_stage, 'progress': self.last_progress, 'message': line}


def execute_with_streaming_progress(
    cmd: list, 
    progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    timeout: int = 600,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Execute subprocess with real-time progress streaming
    
    Args:
        cmd: Command to execute
        progress_callback: Function to call with progress updates
        timeout: Timeout in seconds
        **kwargs: Additional arguments for subprocess.Popen
        
    Returns:
        CompletedProcess-like object with returncode, stdout, stderr
    """
    
    parser = ProgressParser()
    stdout_lines = []
    stderr_lines = []
    
    def read_stdout(process):
        """Read stdout in real-time and parse for progress"""
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            line = line.strip()
            if line:
                stdout_lines.append(line)
                
                # Parse for progress
                if progress_callback:
                    try:
                        progress_info = parser.parse_line(line)
                        progress_callback(progress_info)
                    except Exception as e:
                        # Don't let progress parsing errors break execution
                        progress_callback({
                            'stage': 'error', 
                            'progress': -1, 
                            'message': f'Progress parsing error: {e}'
                        })
    
    def read_stderr(process):
        """Read stderr in real-time"""
        while True:
            line = process.stderr.readline()
            if not line:
                break
            line = line.strip()
            if line:
                stderr_lines.append(line)
                # Also check stderr for progress (some tools output there)
                if progress_callback and line:
                    try:
                        progress_info = parser.parse_line(line)
                        if progress_info.get('progress', 0) > 0:  # Only callback if meaningful progress
                            progress_callback(progress_info)
                    except Exception:
                        pass  # Ignore stderr parsing errors
    
    # Set default subprocess options for streaming
    popen_kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE,
        'text': True,
        'bufsize': 1,  # Line buffered
        'universal_newlines': True,
    }
    popen_kwargs.update(kwargs)
    
    # Start process
    process = subprocess.Popen(cmd, **popen_kwargs)
    
    # Start reading threads
    stdout_thread = threading.Thread(target=read_stdout, args=(process,))
    stderr_thread = threading.Thread(target=read_stderr, args=(process,))
    
    stdout_thread.start()
    stderr_thread.start()
    
    # Wait for completion with timeout
    try:
        returncode = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        returncode = -1
        if progress_callback:
            progress_callback({
                'stage': 'error', 
                'progress': -1, 
                'message': f'Process timed out after {timeout} seconds'
            })
    
    # Wait for reading threads to finish
    stdout_thread.join()
    stderr_thread.join()
    
    # Create CompletedProcess-like result
    class StreamingResult:
        def __init__(self, returncode, stdout_lines, stderr_lines):
            self.returncode = returncode
            self.stdout = '\n'.join(stdout_lines)
            self.stderr = '\n'.join(stderr_lines)
    
    return StreamingResult(returncode, stdout_lines, stderr_lines)


def default_progress_callback(progress_info: Dict[str, Any]):
    """Default progress callback that prints to console"""
    stage = progress_info.get('stage', 'unknown')
    progress = progress_info.get('progress', 0)
    message = progress_info.get('message', '')
    
    if progress >= 0:
        print(f"[{stage.upper()}] {progress}% - {message}")
    else:
        print(f"[ERROR] {message}")


# Example usage function
def demo_streaming_execution():
    """Demo function showing how to use streaming execution"""
    
    def my_progress_callback(progress_info):
        """Custom progress callback"""
        stage = progress_info['stage']
        progress = progress_info['progress']
        message = progress_info['message']
        
        print(f"🔄 [{stage}] {progress}% - {message}")
        
        # You could also:
        # - Update a progress bar in ComfyUI
        # - Send WebSocket updates to frontend
        # - Log to a file
        # - Cancel operation based on user input
    
    # Example: Execute Hunyuan3D with streaming progress
    cmd = [
        "conda", "run", "-n", "hunyuan3d",
        "blender", "--background", "--python", "hunyuan3d_execute.py",
        "--", "config.json"
    ]
    
    print("Starting Hunyuan3D generation with streaming progress...")
    result = execute_with_streaming_progress(
        cmd, 
        progress_callback=my_progress_callback,
        timeout=600  # 10 minutes
    )
    
    print(f"Generation completed with return code: {result.returncode}")
    
    return result


if __name__ == "__main__":
    # Run demo
    demo_streaming_execution()