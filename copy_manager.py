import os
import time
import threading
import queue
from utils import hash_file, normalize_path, format_bytes
from app_logger import logger

class CopyManager:
    def __init__(self, update_callback=None):
        self.task_queue = queue.Queue() 
        self.file_queue = queue.Queue() 
        self.verify_queue = queue.Queue()
        self.update_callback = update_callback 
        
        self.total_bytes = 0
        self.bytes_copied = 0
        self.start_time = None
        
        self.files_copied_count = 0
        self.total_files = 0

        self.pause_event = threading.Event()
        
        self.active = True
        self.threads = []
        self.lock = threading.Lock()
        
        self.worker_status = {}
        self.speed_history = [] 
        self.last_bytes_copied = 0
        self.last_files_done = 0
        self.last_check_time = time.time()

        # Dynamic Worker Config
        cpu_count = os.cpu_count() or 4
        self.max_workers = min(max(4, cpu_count), 16) 
        self.active_workers = 0

        # Start with just 2 workers (Elastic Threading)
        self._spawn_workers(2)
            
        # Start Scanner Thread
        threading.Thread(target=self.scanner_loop, name="Scanner", daemon=True).start()
            
        # Background Speed Calc
        threading.Thread(target=self._speed_monitor_loop, name="Monitor", daemon=True).start()

    def _spawn_workers(self, count):
        """Spawns up to the max_workers limit."""
        with self.lock:
            to_spawn = min(count, self.max_workers - self.active_workers)
            for _ in range(to_spawn):
                idx = self.active_workers
                t = threading.Thread(target=self.worker, args=(idx,), name=f"Worker-{idx}", daemon=True)
                t.start()
                self.threads.append(t)
                self.active_workers += 1
            if to_spawn > 0:
                logger.info(f"Spawned {to_spawn} new workers. Total: {self.active_workers}")

    def enqueue_task(self, source, destination):
        """No longer needs pre-scan counts. Starts immediately."""
        with self.lock:
            if self.start_time is None:
                self.start_time = time.time()
                
        self.task_queue.put((source, destination))
        msg = f"Task added: {source}"
        logger.info(msg)
        self.log(msg)

    def log(self, message):
        if self.update_callback:
            self.update_callback("log", message)

    def update_worker_status(self, worker_id, filename, status, progress, speed=0):
        with self.lock:
            self.worker_status[worker_id] = {
                "file": filename,
                "status": status,
                "progress": progress,
                "speed": speed
            }
        if self.update_callback:
            self.update_callback("connections", self.worker_status)

    def _speed_monitor_loop(self):
        while self.active:
            time.sleep(1)
            with self.lock:
                current_bytes = self.bytes_copied
                current_files = self.files_copied_count
                now = time.time()
                
                time_diff = now - self.last_check_time
                if time_diff > 0:
                    speed = (current_bytes - self.last_bytes_copied) / time_diff
                    items_speed = (current_files - self.last_files_done) / time_diff
                else:
                    speed = 0
                    items_speed = 0
                
                self.last_bytes_copied = current_bytes
                self.last_files_done = current_files
                self.last_check_time = now
                
                percentage = (self.bytes_copied / self.total_bytes * 100) if self.total_bytes > 0 else 0
                remaining = self.total_bytes - self.bytes_copied
                eta = remaining / speed if speed > 0 else None
                
            if self.update_callback:
                self.update_callback("global_stats", {
                    "bytes_copied": current_bytes,
                    "total_bytes": self.total_bytes,
                    "percentage": percentage,
                    "speed": speed,
                    "items_speed": items_speed,
                    "eta": eta,
                    "total_files": self.total_files,
                    "files_done": self.files_copied_count
                })

            # ELASTIC CHECK: If queue is large, spawn more workers
            q_size = self.file_queue.qsize()
            if q_size > 10 and self.active_workers < self.max_workers:
                self._spawn_workers(2)

    def scanner_loop(self):
        """Pulls folder tasks and fills file_queue. Calculates sizes on-the-fly."""
        while self.active:
            try:
                task = self.task_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            source, destination = task
            logger.info(f"Scanning structure: {source}")
            self.log(f"Scanning structure: {source}")
            
            try:
                if not os.path.exists(destination):
                    os.makedirs(destination)
                    
                for foldername, subfolders, filenames in os.walk(source):
                    # PAUSE Check in Scanner
                    if self.pause_event.is_set():
                        while self.pause_event.is_set():
                            time.sleep(0.5)
                        if not self.active: break
                            
                    current_dest_folder = foldername.replace(source, destination, 1)
                    if not os.path.exists(current_dest_folder):
                        os.makedirs(current_dest_folder)
                    
                    for filename in filenames:
                        src_file = os.path.join(foldername, filename)
                        dst_file = os.path.join(current_dest_folder, filename)
                        
                        # Calculate size on the fly to update UI
                        try:
                            f_size = os.path.getsize(src_file)
                            with self.lock:
                                self.total_bytes += f_size
                                self.total_files += 1
                        except: pass

                        self.file_queue.put((src_file, dst_file, filename))
                        
                        # THROTTLE: Small breather to prevent disk thrashing
                        if self.total_files % 100 == 0:
                            time.sleep(0.01)
                        
                self.log(f"Scan complete. Found {self.total_files} files.")
            except Exception as e:
                logger.error(f"Scan failed: {e}", exc_info=True)
                self.log(f"Scan failed: {e}")
            finally:
                self.task_queue.task_done()

    def worker(self, worker_id):
        while self.active:
            try:
                # Wait for file tasks
                task = self.file_queue.get(timeout=1)
            except queue.Empty:
                self.update_worker_status(worker_id, "--", "Idle", 0)
                continue

            src_file, dst_file, filename = task
            self.update_worker_status(worker_id, filename, "Starting", 0)
            
            try:
                self._smart_copy_file(src_file, dst_file, worker_id, filename)
                
                with self.lock:
                    self.files_copied_count += 1
                
                # We could enqueue verify here if needed
                # self.verify_queue.put((src_file, dst_file)) 
            except Exception as e:
                logger.error(f"Error copying {filename}: {e}", exc_info=True)
                self.log(f"Error copying {filename}: {e}")
            finally:
                self.file_queue.task_done()
                self.update_worker_status(worker_id, "--", "Idle", 0)

    # Removed old copy_recursive as it is replaced by scanner_loop logic

    def _smart_copy_file(self, src, dst, worker_id, filename):
        """Copies file with Resume support (.part) and chunked updates."""
        part_file = dst + ".part"
        
        file_size = os.path.getsize(src)
        existing_size = 0
        
        # RESUME CHECK
        mode = 'wb'
        if os.path.exists(part_file):
            existing_size = os.path.getsize(part_file)
            if existing_size < file_size:
                mode = 'ab' # Append
                self.log(f"Resuming {filename} from {format_bytes(existing_size)}")
                with self.lock:
                    self.bytes_copied += existing_size 
            else:
                # Corrupt or larger? Reset.
                existing_size = 0
                self.log(f"Restarting {filename} (Invalid Part File)")
        
        # Don't copy if already done (simple check)
        if os.path.exists(dst):
            d_size = os.path.getsize(dst)
            if d_size == file_size:
                with self.lock:
                    self.bytes_copied += file_size
                return # Already exists.

        chunk_size = 1024 * 1024 # 1MB chunks
        
        try:
            with open(src, 'rb') as fsrc, open(part_file, mode) as fdst:
                if existing_size > 0:
                    fsrc.seek(existing_size)
                
                while True:
                    # PAUSE Handling
                    if self.pause_event.is_set():
                        self.update_worker_status(worker_id, filename, "Paused", (existing_size/file_size)*100)
                        while self.pause_event.is_set():
                            time.sleep(0.5)
                    
                    if not self.active: break

                    buf = fsrc.read(chunk_size)
                    if not buf:
                        break
                    
                    fdst.write(buf)
                    size = len(buf)
                    existing_size += size
                    
                    with self.lock:
                        self.bytes_copied += size
                    
                    # Connection Level Status
                    pct = (existing_size / file_size) * 100
                    # Note: We don't calc per-thread speed here to save CPU, 
                    # can assume global speed / Active threads roughly or just show Progress.
                    self.update_worker_status(worker_id, filename, "Copying", pct)

            # Finalize
            if os.path.exists(dst):
                os.remove(dst)
            os.rename(part_file, dst)

        except Exception as e:
            self.log(f"Failed to copy {filename}: {e}")
            self.update_worker_status(worker_id, filename, "Failed", 0)

    def verify_worker(self, worker_id):
         # Simplified for brevity - normally would verify hashes similarly
         while self.active:
            try:
                task = self.verify_queue.get(timeout=1)
                # Just consuming to keep queue clean for now as focus is on Copy features
                self.verify_queue.task_done()
            except queue.Empty:
                continue

    def pause(self):
        self.pause_event.set()
        self.log("Operations paused.")

    def resume(self):
        self.pause_event.clear()
        self.log("Operations resumed.")
