import sys
import os
import time
import shutil
from pathlib import Path

# Add FolderCopierApp to sys.path
sys.path.append(os.getcwd())

from queue_manager import QueueManager
from copy_manager import CopyExecutorController

def setup_test_data(src_dir: Path, count=100):
    src_dir.mkdir(parents=True, exist_ok=True)
    for i in range(count):
        (src_dir / f"test_{i}.bin").write_bytes(os.urandom(1024)) # 1KB files
    print(f"Created {count} test files in {src_dir}")

def run_verification():
    workspace = Path(os.getcwd())
    src = workspace / "test_src"
    dst = workspace / "test_dst"
    
    # Cleanup
    if src.exists(): shutil.rmtree(src)
    if dst.exists(): shutil.rmtree(dst)
    
    setup_test_data(src, count=500)
    
    controller = CopyExecutorController(max_workers=4)
    manager = controller.manager
    
    print("Starting verification (T-016.6)...")
    start_time = time.time()
    
    # Add files to queue
    success, msg = manager.add_task(str(src), str(dst))
    print(f"Queue Status: {msg}")
    
    # Start execution
    controller.start()
    
    # Monitor metrics for a few seconds
    try:
        while True:
            msg_type, data = manager.progress_channel.get(timeout=2.0)
            if msg_type == "METRICS_UPDATE":
                print(f"[METRICS] Speed: {data['byte_rate']/1024:.2f} KB/s | Items/s: {data['item_rate']:.2f} | Active Threads: {data['active_threads']}")
            elif msg_type == "STATE_CHANGE" and data == "IDLE":
                print("Transfer complete.")
                break
            
            if time.time() - start_time > 30: # Max timeout
                print("Verification timeout.")
                break
    except Exception as e:
        print(f"Monitor caught: {e}")
    finally:
        controller.stop()
        # Cleanup
        if src.exists(): shutil.rmtree(src)
        if dst.exists(): shutil.rmtree(dst)

if __name__ == "__main__":
    run_verification()
