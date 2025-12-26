import logging
import platform
import sys
import os
import datetime

# Configure Logging
log_file = "folder_copier_debug.log"

# Custom handler to keep last 20 records in memory
class MemoryHandler(logging.Handler):
    def __init__(self, capacity=20):
        super().__init__()
        self.capacity = capacity
        self.records = []

    def emit(self, record):
        self.records.append(self.format(record))
        if len(self.records) > self.capacity:
            self.records.pop(0)

memory_handler = MemoryHandler()
memory_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='w'),
        logging.StreamHandler(sys.stdout),
        memory_handler
    ]
)

logger = logging.getLogger("FolderCopier")

def get_system_info():
    """Returns basic system info for debugging context."""
    return {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Python Version": sys.version.split()[0],
        "Architecture": platform.machine(),
        "CPUs": os.cpu_count()
    }

def generate_report_content(copy_manager):
    """
    Creates a human-readable summary of the current session.
    """
    info = get_system_info()
    
    report = []
    report.append("="*40)
    report.append("  FOLDER COPIER - DIAGNOSTIC REPORT")
    report.append("="*40)
    report.append(f"Date: {datetime.datetime.now()}")
    report.append("")
    
    report.append("--- SYSTEM INFORMATION ---")
    for k, v in info.items():
        report.append(f"{k}: {v}")
    report.append("")
    
    report.append("--- SESSION STATISTICS ---")
    report.append(f"Total Files Queued: {copy_manager.total_files}")
    report.append(f"Files Copied: {copy_manager.files_copied_count}")
    report.append(f"Total Bytes Processed: {copy_manager.bytes_copied}")
    report.append(f"Active Threads: {len(copy_manager.threads)}")
    report.append("")
    
    report.append("--- RECENT ERRORS / ACTIVITY (Last 20) ---")
    if memory_handler.records:
        report.extend(memory_handler.records)
    else:
        report.append("No logs captured yet.")
    
    return "\n".join(report)
