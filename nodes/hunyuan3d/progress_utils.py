"""
Progress tracking and parsing utilities for Hunyuan3D execution
"""

import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    seconds = int(seconds)  # Round down to nearest second
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds}s"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    return f"{hours}h {remaining_minutes}m {remaining_seconds}s"


class ProgressTracker:
    """Track progress through Hunyuan3D generation stages"""
    
    @dataclass
    class Progress:
        """Progress information for a specific point in time"""
        stage: str
        percent: int
        elapsed_seconds: float
        estimated_total_seconds: Optional[float]
        message: str
        timestamp: str
        
        @property
        def remaining_seconds(self) -> Optional[float]:
            """Calculate remaining seconds based on estimates"""
            if self.estimated_total_seconds is None:
                return None
            return max(0, self.estimated_total_seconds - self.elapsed_seconds)
        
        def format_pretty(self) -> str:
            """Format progress as a pretty string"""
            elapsed_str = format_duration(self.elapsed_seconds)
            
            if self.remaining_seconds is not None:
                remaining_str = format_duration(self.remaining_seconds)
                eta_info = f" | ETA: {remaining_str}"
            else:
                eta_info = ""
            
            return f"[{self.stage.upper()}] {self.percent}% - {self.message} | Elapsed: {elapsed_str}{eta_info}"
        
        def get_eta(self) -> Optional[datetime]:
            """Get estimated time of arrival (completion)"""
            if self.remaining_seconds is None:
                return None
            
            # Parse timestamp and add remaining seconds
            try:
                current_time = datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
                return current_time + timedelta(seconds=self.remaining_seconds)
            except (ValueError, AttributeError):
                # If timestamp parsing fails, use current time
                return datetime.now() + timedelta(seconds=self.remaining_seconds)
    
    def __init__(self):
        """Initialize progress tracker"""
        self.stage = "starting"
        self.percent = 0
        self.start_time = time.time()
        self.estimated_total_seconds: Optional[float] = None
        self.message = "Initializing"
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed seconds since start"""
        return time.time() - self.start_time
    
    def update_progress(self, stage: str, percent: int, message: str, estimated_total: Optional[float] = None):
        """Update progress information"""
        self.stage = stage
        self.percent = percent
        self.message = message
        
        if estimated_total is not None:
            self.estimated_total_seconds = estimated_total
    
    def to_json(self) -> str:
        """Convert current progress to JSON string"""
        data = {
            "type": "progress",
            "stage": self.stage,
            "percent": self.percent,
            "elapsed_seconds": self.elapsed_seconds,
            "estimated_total_seconds": self.estimated_total_seconds,
            "message": self.message,
            "timestamp": datetime.now().isoformat()
        }
        return json.dumps(data)
    
    def get_progress(self) -> Progress:
        """Get current progress as Progress object"""
        return self.Progress(
            stage=self.stage,
            percent=self.percent,
            elapsed_seconds=self.elapsed_seconds,
            estimated_total_seconds=self.estimated_total_seconds,
            message=self.message,
            timestamp=datetime.now().isoformat()
        )


class ProgressParser:
    """Parse JSON progress messages from Hunyuan3D output"""
    
    def parse_line(self, line: str) -> Optional[ProgressTracker.Progress]:
        """
        Parse a line of output for JSON progress information
        
        Args:
            line: Raw output line
            
        Returns:
            Progress object if line contains valid JSON progress, None otherwise
        """
        line = line.strip()
        if not line:
            return None
        
        # Try to parse as JSON
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            # Not JSON, ignore
            return None
        
        # Check if it's a progress message
        if not isinstance(data, dict) or data.get("type") != "progress":
            return None
        
        # Extract required fields
        try:
            stage = data["stage"]
            percent = int(data["percent"])
            elapsed_seconds = float(data["elapsed_seconds"])
            message = data["message"]
            
            # Timestamp is optional - use current time if not provided
            timestamp = data.get("timestamp", datetime.now().isoformat())
            
            # Optional field
            estimated_total_seconds = data.get("estimated_total_seconds")
            if estimated_total_seconds is not None:
                estimated_total_seconds = float(estimated_total_seconds)
            
            return ProgressTracker.Progress(
                stage=stage,
                percent=percent,
                elapsed_seconds=elapsed_seconds,
                estimated_total_seconds=estimated_total_seconds,
                message=message,
                timestamp=timestamp
            )
            
        except (KeyError, ValueError, TypeError):
            # Missing required fields or invalid types
            return None


class LoggingProgressTracker(ProgressTracker):
    """Progress tracker that logs JSON to stdout and saves raw logs"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        """
        Initialize logging progress tracker
        
        Args:
            log_file_path: Optional path to save raw logs
        """
        super().__init__()
        self.log_file_path = log_file_path
        self.raw_logs = []
    
    def log_progress(self):
        """Log current progress as JSON to stdout"""
        json_str = self.to_json()
        print(json_str, flush=True)
        
        # Also save to raw logs
        self.raw_logs.append({
            "timestamp": datetime.now().isoformat(),
            "type": "progress_json",
            "content": json_str
        })
    
    def log_raw(self, content: str, log_type: str = "stdout"):
        """Log raw content (for debugging)"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": log_type,
            "content": content
        }
        
        self.raw_logs.append(log_entry)
        
        # Optionally write to file
        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{log_entry['timestamp']}] [{log_type}] {content}\n")
            except Exception as e:
                # Don't let logging errors break execution
                print(f"Warning: Failed to write to log file: {e}")
    
    def update_progress(self, stage: str, percent: int, message: str, estimated_total: Optional[float] = None, log_immediately: bool = True):
        """Update progress and optionally log immediately"""
        super().update_progress(stage, percent, message, estimated_total)
        
        if log_immediately:
            self.log_progress()
    
    def save_raw_logs(self) -> bool:
        """Save all raw logs to file"""
        if not self.log_file_path:
            return False
        
        try:
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                for log_entry in self.raw_logs:
                    f.write(f"[{log_entry['timestamp']}] [{log_entry['type']}] {log_entry['content']}\n")
            return True
        except Exception as e:
            print(f"Error saving raw logs: {e}")
            return False


# Constants for stage timing estimates (in seconds)
STAGE_ESTIMATES = {
    "shape_generation": 180,    # 3 minutes for shape generation
    "texture_painting": 240,    # 4 minutes for texture painting  
    "exporting": 30,           # 30 seconds for export
    "total": 450               # 7.5 minutes total
}

# Stage percentage ranges
STAGE_PERCENTAGES = {
    "starting": (0, 0),
    "shape_generation": (0, 50),
    "texture_painting": (50, 90), 
    "exporting": (90, 99),
    "complete": (100, 100)
}


def create_progress_tracker(log_file_path: Optional[str] = None) -> LoggingProgressTracker:
    """
    Create a progress tracker with logging
    
    Args:
        log_file_path: Optional path to save raw logs
        
    Returns:
        LoggingProgressTracker instance
    """
    return LoggingProgressTracker(log_file_path)


def parse_hunyuan3d_output(output_lines: list) -> list[ProgressTracker.Progress]:
    """
    Parse Hunyuan3D output lines for progress information
    
    Args:
        output_lines: List of output lines from subprocess
        
    Returns:
        List of Progress objects found in the output
    """
    parser = ProgressParser()
    progress_updates = []
    
    for line in output_lines:
        progress = parser.parse_line(line)
        if progress:
            progress_updates.append(progress)
    
    return progress_updates