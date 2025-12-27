import sys
import os
import time
import shutil
import stat
from pathlib import Path

# Add FolderCopierApp to sys.path
sys.path.append(os.getcwd())

from queue_manager import QueueManager
from copy_manager import CopyExecutorController

def run_failure_verification():
    workspace = Path(os.getcwd())
    src = workspace / "fail_test_src"
    dst = workspace / "fail_test_dst"
    
    # Cleanup
    if src.exists(): shutil.rmtree(src)
    if dst.exists(): shutil.rmtree(dst)
    
    src.mkdir(parents=True, exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)
    
    # Create a protected file
    protected_file = src / "forbidden.bin"
    protected_file.write_text("Secret Data")
    
    # Create a normal file
    normal_file = src / "normal.bin"
    normal_file.write_text("Normal Data")

    print("\n--- Verifying Permission Failure Path ---")
    
    controller = CopyExecutorController(max_workers=1)
    manager = controller.manager
    
    # Make destination read-only (simulated permission error)
    # Actually, better to just chmod the destination file after creation if it existed, 
    # but for a clean test we'll chmod the folder.
    os.chmod(dst, stat.S_IREAD | stat.S_IEXEC) 
    
    try:
        manager.add_task(str(src), str(dst))
        controller.start()
        
        start_time = time.time()
        error_found = False
        while time.time() - start_time < 5:
            try:
                msg_type, data = manager.progress_channel.get(timeout=1.0)
                if msg_type == "LOG" and "ERROR" in data:
                    print(f"Captured Expected Error: {data}")
                    error_found = True
                    break
                if msg_type == "STATE_CHANGE" and data == "IDLE":
                    break
            except: pass
            
        if error_found:
            print("SUCCESS: Permission failure path verified.")
        else:
            print("FAILURE: System did not report permission error.")
            
    finally:
        os.chmod(dst, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        controller.stop()
        time.sleep(1) # Allow worker to stop
        if src.exists():
            try: shutil.rmtree(src)
            except: pass
        if dst.exists():
            try: shutil.rmtree(dst)
            except: pass

if __name__ == "__main__":
    run_failure_verification()
