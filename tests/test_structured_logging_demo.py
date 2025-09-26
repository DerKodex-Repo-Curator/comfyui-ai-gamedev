"""
Demo test showing how structured logging works end-to-end
"""

import unittest
import sys
from pathlib import Path
import tempfile
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.hunyuan3d.progress_utils import create_progress_tracker, parse_hunyuan3d_output, format_duration


class TestStructuredLoggingDemo(unittest.TestCase):
    """Demo of structured logging functionality"""
    
    def test_progress_tracking_demo(self):
        """Demo showing complete progress tracking workflow"""
        print("\n🎬 Structured Logging Demo")
        print("=" * 50)
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            log_file_path = f.name
        
        try:
            # Initialize progress tracker
            progress_tracker = create_progress_tracker(log_file_path)
            
            print("📊 Simulating Hunyuan3D execution with structured logging...")
            
            # Simulate the execution stages
            stages = [
                ("starting", 0, "Initializing Hunyuan3D execution", 0.1),
                ("shape_generation", 5, "Loading 3D shape generation model", 1.0),
                ("shape_generation", 10, "Generating 3D shape with 30 steps", 2.0),
                ("shape_generation", 50, "3D shape generation completed successfully", 3.0),
                ("texture_painting", 55, "Initializing texture painting pipeline", 0.5),
                ("texture_painting", 85, "Texture painting completed successfully", 2.5),
                ("exporting", 90, "Exporting 3D models to GLB, OBJ, and STL formats", 0.3),
                ("complete", 100, "Hunyuan3D generation completed successfully", 0.1)
            ]
            
            collected_json_lines = []
            
            for stage, percent, message, duration in stages:
                # Update progress (this outputs JSON to stdout)
                progress_tracker.update_progress(
                    stage=stage, 
                    percent=percent, 
                    message=message, 
                    estimated_total=450  # 7.5 minutes total
                )
                
                # Capture the JSON that would be output
                json_line = progress_tracker.to_json()
                collected_json_lines.append(json_line)
                
                # Show formatted progress
                progress = progress_tracker.get_progress()
                formatted = progress.format_pretty()
                print(f"  {formatted}")
                
                # Simulate time passing
                time.sleep(duration)
            
            print(f"\n📁 Raw log file created: {log_file_path}")
            
            # Save logs
            progress_tracker.save_raw_logs()
            
            # Demo parsing the JSON output
            print("\n🔍 Parsing JSON progress from output...")
            mixed_output = [
                "Script starting...",
                "Loading models...",
            ] + collected_json_lines + [
                "Some non-JSON output",
                "✅ GENERATION COMPLETE",
                "Blender quit"
            ]
            
            progress_updates = parse_hunyuan3d_output(mixed_output)
            
            print(f"\n📈 Extracted {len(progress_updates)} progress updates:")
            for i, progress in enumerate(progress_updates, 1):
                elapsed_str = format_duration(progress.elapsed_seconds)
                if progress.remaining_seconds:
                    remaining_str = format_duration(progress.remaining_seconds)
                    eta_info = f" (ETA: {remaining_str})"
                else:
                    eta_info = ""
                
                print(f"  {i}. [{progress.stage.upper()}] {progress.percent}% - {progress.message}")
                print(f"     Elapsed: {elapsed_str}{eta_info}")
            
            # Show log file contents
            log_content = Path(log_file_path).read_text()
            print(f"\n📋 Log file contains {len(log_content.splitlines())} lines")
            print("Sample log entries:")
            for line in log_content.splitlines()[:3]:
                print(f"  {line}")
            if len(log_content.splitlines()) > 3:
                print(f"  ... and {len(log_content.splitlines()) - 3} more lines")
            
            print("\n✅ Demo completed successfully!")
            
            # Assertions to make it a proper test
            self.assertEqual(len(progress_updates), 8)
            self.assertEqual(progress_updates[0].stage, "starting")
            self.assertEqual(progress_updates[-1].stage, "complete")
            self.assertEqual(progress_updates[-1].percent, 100)
            
        finally:
            # Cleanup
            Path(log_file_path).unlink(missing_ok=True)
    
    def test_json_output_format(self):
        """Test and display the JSON output format"""
        print("\n📋 JSON Output Format Demo")
        print("=" * 40)
        
        progress_tracker = create_progress_tracker()
        
        # Show different stages of JSON output
        test_cases = [
            ("starting", 0, "Initializing"),
            ("shape_generation", 25, "Generating 3D shape"),
            ("texture_painting", 75, "Painting textures"),
            ("complete", 100, "Generation complete")
        ]
        
        for stage, percent, message in test_cases:
            progress_tracker.update_progress(
                stage=stage,
                percent=percent, 
                message=message,
                estimated_total=300
            )
            
            json_output = progress_tracker.to_json()
            print(f"\n{stage.upper()} ({percent}%):")
            print(f"  JSON: {json_output}")
            
            # Show how it would be parsed
            from nodes.hunyuan3d.progress_utils import ProgressParser
            parser = ProgressParser()
            parsed = parser.parse_line(json_output)
            
            if parsed:
                print(f"  Parsed: {parsed.format_pretty()}")
            
            time.sleep(0.1)  # Small delay to show time progression
    
    def test_error_scenarios(self):
        """Test how errors are handled in structured logging"""
        print("\n❌ Error Handling Demo")
        print("=" * 30)
        
        from nodes.hunyuan3d.progress_utils import ProgressParser
        parser = ProgressParser()
        
        # Test various error scenarios
        error_cases = [
            ("Invalid JSON", '{"invalid": json}'),
            ("Missing fields", '{"type": "progress", "stage": "test"}'),
            ("Wrong type", '{"type": "not_progress", "stage": "test", "percent": 50}'),
            ("Invalid percent", '{"type": "progress", "stage": "test", "percent": "not_a_number", "elapsed_seconds": 0, "message": "test"}'),
            ("Empty string", ""),
            ("Non-JSON", "This is not JSON at all"),
        ]
        
        for error_name, error_input in error_cases:
            result = parser.parse_line(error_input)
            status = "✅ Handled" if result is None else "❌ Failed"
            print(f"  {error_name}: {status}")
            
            # All should return None (properly handled)
            self.assertIsNone(result, f"Should handle error: {error_name}")
        
        print("  All error cases handled correctly!")


if __name__ == '__main__':
    # Run the demo with verbose output
    unittest.main(verbosity=2)