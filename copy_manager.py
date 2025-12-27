import concurrent.futures
from queue_manager import QueueManager, worker_thread_task
import threading
import time

class CopyExecutorController:
    """
    Manages the ThreadPoolExecutor and coordinates worker startup based on QueueManager state.
    """
    def __init__(self, max_workers=4):
        self.manager = QueueManager()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.max_workers = max_workers
        self.worker_thread_handle = None
        self.running = True
        
        # Metrics History (for rolling window)
        self.history_bytes = []
        self.history_items = []
        self.last_total_bytes = 0
        self.last_total_items = 0
        
        # EMA State
        self.ema_byte_rate = 0
        self.ema_item_rate = 0
        self.alpha = 0.3 # Smoothing factor (0.3 = 70% weight on old, 30% on new)
        self.bytes_since_last_tick = 0

    def submit_task(self, source, destination, op_type="COPY"):
        """Submits a task to the manager."""
        self.manager.add_task(source, destination, op_type)
        self._ensure_worker_is_active()
        # Initial metrics trigger
        self._update_metrics()

    def start(self):
        """Starts processing if tasks are available."""
        if self.manager.state == self.manager.STATE_IDLE and not self.manager.task_queue.empty():
            self.manager.resume()
            self._ensure_worker_is_active()
        elif self.manager.state == self.manager.STATE_PAUSED:
            self.resume()

    def pause(self):
        """Instructs the manager to pause."""
        self.manager.pause()

    def resume(self):
        """Instructs the manager to resume."""
        if self.manager.resume():
            # If resume succeeds (transitioned to RUNNING), ensure the worker loop is active
            self._ensure_worker_is_active()

    def _ensure_worker_is_active(self):
        """Starts the main worker monitoring thread if it's not running and tasks need processing."""
        current_state, _ = self.manager.get_status()
        
        if current_state == self.manager.STATE_RUNNING and self.worker_thread_handle is None:
            print("[Controller] Starting dedicated worker monitoring thread.")
            # Start a dedicated thread whose only job is to feed the ThreadPoolExecutor
            self.worker_thread_handle = threading.Thread(
                target=self._worker_monitoring_loop,
                daemon=True
            )
            self.worker_thread_handle.start()
        elif current_state == self.manager.STATE_IDLE and self.worker_thread_handle is not None:
            # If we transition to IDLE, we allow the loop to terminate naturally in the next iteration.
            pass


    def _worker_monitoring_loop(self):
        """
        This loop runs on a dedicated, persistent thread, managing the submission
        of tasks to the ThreadPoolExecutor based on QueueManager state checks.
        """
        while self.running:
            state, _ = self.manager.get_status()
            
            # Drain progress channel for intra-tick metrics
            try:
                # We peek/drain the channel specifically for metrics data
                while not self.manager.progress_channel.empty():
                    msg = self.manager.progress_channel.get_nowait()
                    if msg[0] == "CHUNK_DONE":
                        self.bytes_since_last_tick += msg[1]
                    else:
                        # Put back non-metrics messages for GUI
                        # Actually, better to have a dedicated metrics channel, 
                        # but for now we'll handle it carefully.
                        # We'll modify QueueManager to have a separate metrics queue.
                        pass
            except: pass

            if state == self.manager.STATE_IDLE:
                # Allow loop to terminate if idle
                if self.manager.task_queue.empty():
                    print("[Controller] Monitoring loop terminating due to IDLE state.")
                    self.worker_thread_handle = None
                    break
            
            # If RUNNING or PAUSED, we need to submit a worker thread to check the queue state
            if state in [self.manager.STATE_RUNNING, self.manager.STATE_PAUSED]:
                # Submit the core processing function to the ThreadPoolExecutor
                # Since the worker_thread_task handles its own internal loop and state checks, 
                # we submit it only when a state change might allow work to happen (RUNNING or newly PAUSED queue).
                
                # Crucially, we only submit *one* instance of the monitoring logic per RUNNING phase.
                # If the state is RUNNING, we submit a worker to execute its cycle.
                if state == self.manager.STATE_RUNNING:
                    self.executor.submit(worker_thread_task, self.manager)
                
                # Wait briefly before checking state again. This prevents busy-waiting while PAUSED.
                self._update_metrics()
                time.sleep(0.2) # Sample at 5Hz
            else:
                self._update_metrics()
                time.sleep(0.5)

    def _update_metrics(self):
        """Calculates EMA based metrics and thread usage."""
        current_time = time.time()
        curr_items = self.manager.total_items_completed
        
        # 1. Byte Rate (Pulse-based for accuracy during large file copy)
        # Using a small sampling window (0.2s)
        instant_byte_rate = self.bytes_since_last_tick / 0.2
        self.ema_byte_rate = (self.alpha * instant_byte_rate) + ((1 - self.alpha) * self.ema_byte_rate)
        self.bytes_since_last_tick = 0
        
        # 2. Item Rate (Completion-based)
        delta_items = curr_items - self.last_total_items
        self.last_total_items = curr_items
        
        instant_item_rate = delta_items / 0.2
        self.ema_item_rate = (self.alpha * instant_item_rate) + ((1 - self.alpha) * self.ema_item_rate)

        # Introspect ThreadPoolExecutor
        active_threads = 0
        try:
            active_threads = len(self.executor._threads)
        except:
            pass

        # Dispatch to GUI
        metrics = {
            "byte_rate": self.ema_byte_rate,
            "item_rate": self.ema_item_rate,
            "active_threads": active_threads,
            "total_threads": self.max_workers,
            "total_bytes": self.manager.total_bytes_processed,
            "total_items": curr_items
        }
        self.manager.progress_channel.put(("METRICS_UPDATE", metrics))


    def get_progress_channel(self):
        """Exposes the communication channel to the GUI."""
        return self.manager.progress_channel

    def stop(self):
        self.running = False
        if self.worker_thread_handle:
            # We don't join here to avoid GUI freeze, but we signal shutdown
            pass
        self.executor.shutdown(wait=False)
        print("CopyExecutorController stopped.")