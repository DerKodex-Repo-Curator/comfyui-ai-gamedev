"""
Test subprocess buffering behavior with Blender to determine if we can stream progress reports
"""

import unittest
import subprocess
import threading
import time
import queue
import os
from pathlib import Path
import sys

class TestSubprocessBuffering(unittest.TestCase):
    """Test buffering behavior of subprocess execution with Blender"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.project_root = Path(__file__).parent.parent
        self.test_script_path = self.project_root / "tests" / "test_buffering_script.py"
        
    def test_subprocess_run_buffering(self):
        """Test if subprocess.run buffers output (baseline test)"""
        print("\n🔍 Testing subprocess.run buffering behavior...")
        
        # Create a simple test script that prints with delays
        test_script = '''
import time
import sys
print("Line 1: Starting", flush=True)
sys.stderr.write("STDERR 1: Starting\\n")
sys.stderr.flush()
time.sleep(1)
print("Line 2: Middle", flush=True)
sys.stderr.write("STDERR 2: Middle\\n")
sys.stderr.flush()
time.sleep(1)
print("Line 3: Ending", flush=True)
sys.stderr.write("STDERR 3: Ending\\n")
sys.stderr.flush()
'''
        
        with open(self.test_script_path, 'w') as f:
            f.write(test_script)
        
        start_time = time.time()
        
        # Test with subprocess.run (should be fully buffered)
        result = subprocess.run(
            ["python", str(self.test_script_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"📊 subprocess.run completed in {duration:.1f}s")
        print("STDOUT received:")
        for i, line in enumerate(result.stdout.strip().split('\n'), 1):
            print(f"  {i}: {line}")
        print("STDERR received:")
        for i, line in enumerate(result.stderr.strip().split('\n'), 1):
            print(f"  {i}: {line}")
        
        # Should get all output at once after ~2 seconds
        self.assertGreaterEqual(duration, 2.0, "Script should take at least 2 seconds")
        self.assertIn("Line 1: Starting", result.stdout)
        self.assertIn("Line 3: Ending", result.stdout)
        self.assertIn("STDERR 1: Starting", result.stderr)
        self.assertIn("STDERR 3: Ending", result.stderr)
        
        # Cleanup
        self.test_script_path.unlink(missing_ok=True)
        
    def test_popen_realtime_streaming(self):
        """Test if Popen can stream output in real-time"""
        print("\n🔍 Testing Popen real-time streaming...")
        
        # Create a test script that outputs with timestamps
        test_script = '''
import time
import sys
import datetime

def log(msg):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print(f"[{timestamp}] {msg}", flush=True)
    sys.stderr.write(f"[{timestamp}] STDERR: {msg}\\n")
    sys.stderr.flush()

log("Starting script")
time.sleep(1)
log("Progress: 25%")
time.sleep(1)
log("Progress: 50%")
time.sleep(1)
log("Progress: 75%")
time.sleep(1)
log("Progress: 100% - Complete")
'''
        
        with open(self.test_script_path, 'w') as f:
            f.write(test_script)
        
        # Track when we receive each line
        stdout_lines = []
        stderr_lines = []
        receive_times = []
        
        start_time = time.time()
        
        def read_stdout(process, lines_list, times_list):
            """Read stdout in real-time"""
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                current_time = time.time() - start_time
                lines_list.append((current_time, line.strip()))
                times_list.append(current_time)
                print(f"📥 STDOUT at {current_time:.1f}s: {line.strip()}")
        
        def read_stderr(process, lines_list):
            """Read stderr in real-time"""
            while True:
                line = process.stderr.readline()
                if not line:
                    break
                current_time = time.time() - start_time
                lines_list.append((current_time, line.strip()))
                print(f"📥 STDERR at {current_time:.1f}s: {line.strip()}")
        
        # Start process with Popen for streaming
        process = subprocess.Popen(
            ["python", str(self.test_script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Start threads to read output
        stdout_thread = threading.Thread(target=read_stdout, args=(process, stdout_lines, receive_times))
        stderr_thread = threading.Thread(target=read_stderr, args=(process, stderr_lines))
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Wait for process to complete
        process.wait()
        stdout_thread.join()
        stderr_thread.join()
        
        total_duration = time.time() - start_time
        
        print(f"📊 Popen streaming completed in {total_duration:.1f}s")
        print(f"📊 Received {len(stdout_lines)} stdout lines, {len(stderr_lines)} stderr lines")
        
        # Analyze timing - should receive lines roughly every second
        if len(receive_times) >= 2:
            intervals = [receive_times[i] - receive_times[i-1] for i in range(1, len(receive_times))]
            avg_interval = sum(intervals) / len(intervals)
            print(f"📊 Average interval between stdout lines: {avg_interval:.1f}s")
            
            # Should be close to 1 second intervals if streaming works
            self.assertGreater(len(stdout_lines), 3, "Should receive multiple stdout lines")
            self.assertLess(avg_interval, 2.0, "Lines should arrive roughly every second")
        
        # Cleanup
        self.test_script_path.unlink(missing_ok=True)
        
    def test_blender_subprocess_buffering(self):
        """Test actual Blender subprocess buffering with a minimal script"""
        print("\n🔍 Testing Blender subprocess buffering...")
        
        # Create a minimal Blender script that prints with delays
        blender_script = '''
import time
import sys

print("🔨 Blender script starting", flush=True)
sys.stderr.write("STDERR: Blender script starting\\n")
sys.stderr.flush()

for i in range(1, 6):
    print(f"🔄 Progress step {i}/5", flush=True)
    sys.stderr.write(f"STDERR: Progress step {i}/5\\n")
    sys.stderr.flush()
    time.sleep(1)

print("✅ Blender script complete", flush=True)
sys.stderr.write("STDERR: Blender script complete\\n")
sys.stderr.flush()
'''
        
        blender_script_path = self.project_root / "tests" / "test_blender_buffering.py"
        with open(blender_script_path, 'w') as f:
            f.write(blender_script)
        
        try:
            # Test 1: subprocess.run (should be buffered)
            print("\n📋 Test 1: subprocess.run with Blender")
            start_time = time.time()
            
            result = subprocess.run(
                ["blender", "--background", "--python", str(blender_script_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            run_duration = time.time() - start_time
            print(f"📊 subprocess.run duration: {run_duration:.1f}s")
            print("STDOUT lines:")
            for i, line in enumerate(result.stdout.split('\n'), 1):
                if line.strip():
                    print(f"  {i}: {line.strip()}")
            
            # Test 2: Popen streaming with Blender
            print("\n📋 Test 2: Popen streaming with Blender")
            
            stdout_lines = []
            stderr_lines = []
            receive_times = []
            
            start_time = time.time()
            
            def read_blender_stdout(process, lines_list, times_list):
                """Read Blender stdout in real-time"""
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    current_time = time.time() - start_time
                    if line.strip():  # Only log non-empty lines
                        lines_list.append((current_time, line.strip()))
                        times_list.append(current_time)
                        print(f"📥 STDOUT at {current_time:.1f}s: {line.strip()}")
            
            def read_blender_stderr(process, lines_list):
                """Read Blender stderr in real-time"""
                while True:
                    line = process.stderr.readline()
                    if not line:
                        break
                    current_time = time.time() - start_time
                    if line.strip() and not line.strip().startswith("Color management"):
                        lines_list.append((current_time, line.strip()))
                        print(f"📥 STDERR at {current_time:.1f}s: {line.strip()}")
            
            # Start Blender with Popen
            process = subprocess.Popen(
                ["blender", "--background", "--python", str(blender_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Start reading threads
            stdout_thread = threading.Thread(target=read_blender_stdout, args=(process, stdout_lines, receive_times))
            stderr_thread = threading.Thread(target=read_blender_stderr, args=(process, stderr_lines))
            
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for completion
            process.wait()
            stdout_thread.join()
            stderr_thread.join()
            
            popen_duration = time.time() - start_time
            
            print(f"\n📊 Popen streaming duration: {popen_duration:.1f}s")
            print(f"📊 Progress lines received: {len([l for l in stdout_lines if 'Progress step' in l[1]])}")
            
            if len(receive_times) >= 2:
                intervals = [receive_times[i] - receive_times[i-1] for i in range(1, len(receive_times))]
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"📊 Average interval between lines: {avg_interval:.1f}s")
                    
                    # Report findings
                    if avg_interval < 2.0 and len(stdout_lines) > 3:
                        print("✅ RESULT: Blender output appears to be STREAMABLE!")
                        print("   💡 We can use Popen for real-time progress updates")
                    else:
                        print("❌ RESULT: Blender output appears to be BUFFERED")
                        print("   💡 Progress updates will only appear after completion")
            
        finally:
            # Cleanup
            blender_script_path.unlink(missing_ok=True)
            
    def test_conda_blender_buffering(self):
        """Test buffering with conda run + blender (the actual command we use)"""
        print("\n🔍 Testing 'conda run -n hunyuan3d blender' buffering...")
        
        # Create the same test script
        blender_script = '''
import time
import sys

print("🔨 Conda+Blender script starting", flush=True)
for i in range(1, 4):
    print(f"🔄 Step {i}/3", flush=True)
    sys.stderr.write(f"STDERR: Step {i}/3\\n")
    sys.stderr.flush()
    time.sleep(1)
print("✅ Conda+Blender script complete", flush=True)
'''
        
        blender_script_path = self.project_root / "tests" / "test_conda_blender.py"
        with open(blender_script_path, 'w') as f:
            f.write(blender_script)
        
        try:
            stdout_lines = []
            receive_times = []
            
            start_time = time.time()
            
            def read_conda_stdout(process, lines_list, times_list):
                """Read conda+blender stdout in real-time"""
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    current_time = time.time() - start_time
                    if line.strip() and not any(skip in line for skip in ["Color management", "Blender quit"]):
                        lines_list.append((current_time, line.strip()))
                        times_list.append(current_time)
                        print(f"📥 at {current_time:.1f}s: {line.strip()}")
            
            # Test the actual command we use in production
            process = subprocess.Popen(
                ["conda", "run", "-n", "hunyuan3d", "blender", "--background", "--python", str(blender_script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            stdout_thread = threading.Thread(target=read_conda_stdout, args=(process, stdout_lines, receive_times))
            stdout_thread.start()
            
            process.wait()
            stdout_thread.join()
            
            duration = time.time() - start_time
            
            print(f"\n📊 Total duration: {duration:.1f}s")
            print(f"📊 Lines received: {len(stdout_lines)}")
            
            if len(receive_times) >= 2:
                intervals = [receive_times[i] - receive_times[i-1] for i in range(1, len(receive_times))]
                if intervals:
                    avg_interval = sum(intervals) / len(intervals)
                    print(f"📊 Average interval: {avg_interval:.1f}s")
                    
                    print("\n🎯 FINAL RECOMMENDATION:")
                    if avg_interval < 2.0 and len(stdout_lines) >= 3:
                        print("✅ Real-time streaming IS POSSIBLE with conda+blender!")
                        print("   💡 Use subprocess.Popen with threading for progress updates")
                        print("   💡 Set bufsize=1 and text=True for line buffering")
                    else:
                        print("❌ Real-time streaming is NOT reliable with conda+blender")
                        print("   💡 Stick with subprocess.run and batch output processing")
            
        finally:
            blender_script_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)