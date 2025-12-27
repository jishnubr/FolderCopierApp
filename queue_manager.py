import queue
import os
import shutil
import threading
import hashlib
import time

class QueueManager:
    """
    Manages the operational state (IDLE, PAUSED, RUNNING) and the thread-safe task queue.
    Implements operation fingerprinting for idempotency checks.
    """
    STATE_IDLE = "IDLE"
    STATE_PAUSED = "PAUSED"
    STATE_RUNNING = "RUNNING"

    def __init__(self):
        # State management
        self.state = self.STATE_IDLE
        self._lock = threading.Lock()

        # Data structures
        self.task_queue = queue.Queue()
        self.fingerprint_set = set()  # Stores unique hashes of tasks already queued/processed

        # Communication channel for workers to report back to the main thread/GUI
        self.progress_channel = queue.Queue()
        self.current_operation = None

        # SRE Metrics
        self.total_bytes_processed = 0
        self.total_items_completed = 0

    def _generate_fingerprint(self, source: str, destination: str, op_type: str) -> str:
        """Generates a deterministic hash for an operation."""
        data = f"{source}|{destination}|{op_type}"
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def add_task(self, source: str, destination: str, op_type: str = "COPY") -> tuple[bool, str]:
        """Adds a task or a directory of tasks."""
        if os.path.isdir(source):
            return self._add_directory_task(source, destination, op_type)
        return self._add_single_file_task(source, destination, op_type)

    def _add_directory_task(self, source_dir: str, dest_dir: str, op_type: str) -> tuple[bool, str]:
        """Explodes a directory into individual file tasks."""
        count = 0
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, source_dir)
                dst_path = os.path.join(dest_dir, rel_path)
                self._add_single_file_task(src_path, dst_path, op_type)
                count += 1
        
        msg = f"Queued directory: {source_dir} ({count} files)"
        self.progress_channel.put(("LOG", msg))
        return True, msg

    def _add_single_file_task(self, source: str, destination: str, op_type: str) -> tuple[bool, str]:
        """Adds a single file task if not duplicate."""
        fp = self._generate_fingerprint(source, destination, op_type)

        with self._lock:
            if fp in self.fingerprint_set:
                msg = f"Skipped (Idempotent): {os.path.basename(source)}"
                self.progress_channel.put(("LOG", msg))
                return False, msg

            task_data = {
                "fp": fp, 
                "source": source, 
                "destination": destination, 
                "type": op_type,
                "size": os.path.getsize(source) if os.path.exists(source) else 0
            }
            self.task_queue.put(task_data)
            self.fingerprint_set.add(fp)
            self.progress_channel.put(("QUEUE_UPDATE", len(self.task_queue.queue)))
            return True, "Task added"

    def pause(self) -> bool:
        """Transitions state to PAUSED, respecting transition rules."""
        with self._lock:
            if self.state == self.STATE_RUNNING:
                self.state = self.STATE_PAUSED
                self.progress_channel.put(("STATE_CHANGE", self.STATE_PAUSED))
                self.progress_channel.put(("LOG", "Operation Paused."))
                return True
            return False

    def resume(self) -> bool:
        """Transitions state to RUNNING, respecting transition rules."""
        with self._lock:
            if self.state == self.STATE_PAUSED:
                self.state = self.STATE_RUNNING
                self.progress_channel.put(("STATE_CHANGE", self.STATE_RUNNING))
                self.progress_channel.put(("LOG", "Operation Resumed."))
                # Note: The worker loop must check this state change
                return True
            elif self.state == self.STATE_IDLE:
                # Per design: Transitioning from IDLE to RUNNING only happens if the worker loop is active
                # However, if the worker loop hasn't been started yet (no tasks submitted), we rely on the main loop to start it later.
                # For simplicity here, we transition RUNNING if the queue has items and we weren't PAUSED.
                if not self.task_queue.empty():
                    self.state = self.STATE_RUNNING
                    self.progress_channel.put(("STATE_CHANGE", self.STATE_RUNNING))
                    self.progress_channel.put(("LOG", "Operation Started (from IDLE state)."))
                    return True
            return False

    def get_next_task(self):
        """Safely retrieves the next task and checks state."""
        with self._lock:
            if self.state == self.STATE_IDLE:
                return None
            
            if self.state == self.STATE_PAUSED:
                # Worker pauses execution until state changes
                return "PAUSE_BLOCKER"

            if self.task_queue.empty():
                self.state = self.STATE_IDLE
                self.progress_channel.put(("STATE_CHANGE", self.STATE_IDLE))
                self.progress_channel.put(("LOG", "Queue empty. Operation complete."))
                return None
            
            # State is RUNNING and queue is not empty
            task = self.task_queue.get()
            self.current_operation = task['fp']
            return task

    def task_complete(self, fp: str, bytes_count: int = 0):
        """Called by worker after successful processing."""
        with self._lock:
            if self.current_operation == fp:
                self.current_operation = None
                self.total_items_completed += 1
                self.total_bytes_processed += bytes_count
                
                self.progress_channel.put(("TASK_DONE", fp))
                self.progress_channel.put(("QUEUE_UPDATE", len(self.task_queue.queue)))
                
                # Important: Re-check state after completion (might revert to IDLE/PAUSED)
                if self.state == self.STATE_RUNNING and self.task_queue.empty():
                    self.state = self.STATE_IDLE
                    self.progress_channel.put(("STATE_CHANGE", self.STATE_IDLE))
                    self.progress_channel.put(("LOG", "Queue empty. Operation complete."))

    def get_status(self):
        with self._lock:
            return self.state, len(self.task_queue.queue)

    def get_state(self):
        with self._lock:
            return self.state

    def set_state(self, new_state):
        """Allows GUI to force state transitions."""
        if new_state == self.STATE_PAUSED:
            self.pause()
        elif new_state == self.STATE_RUNNING:
            self.resume()
        elif new_state == self.STATE_IDLE:
            with self._lock:
                self.state = self.STATE_IDLE
                self.progress_channel.put(("STATE_CHANGE", self.STATE_IDLE))

# --- Worker Function (Simulating CopyManager Refactor) ---

def worker_thread_task(manager: QueueManager):
    """The main loop executed by each worker thread using REAL file operations."""
    while True:
        task = manager.get_next_task()

        if task is None:
            if manager.state == manager.STATE_IDLE:
                break
            time.sleep(0.1)
            continue

        if task == "PAUSE_BLOCKER":
            time.sleep(0.1)
            continue

        # --- Actual Production-Grade Execution ---
        fp = task['fp']
        src = task['source']
        dst = task['destination']
        size = task.get('size', 0)
        t_name = threading.current_thread().name
        
        try:
            manager.progress_channel.put(("OP_START", (fp, src, t_name))) # Pass thread name
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            
            # Perform actual copy
            shutil.copy2(src, dst)
            
            manager.progress_channel.put(("OP_PROGRESS", (fp, 100, t_name))) 
            manager.task_complete(fp, bytes_count=size)
            
        except Exception as e:
            err_msg = f"ERROR copying {os.path.basename(src)}: {e}"
            manager.progress_channel.put(("LOG", err_msg))
            # Even on failure, we mark task as done to avoid hanging the queue
            # (In SRE, we might retry, but here we log and continue)
            manager.task_complete(fp, bytes_count=0)