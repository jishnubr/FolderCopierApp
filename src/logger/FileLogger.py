import logging
import logging.handlers
import os

class FileLogger:
    """Handles writing verbose debug logs to a file."""
    
    LOG_FILE = "debug.log"
    
    def __init__(self, max_bytes=10*1024*1024, backup_count=5):
        """
        Initializes the file logger using RotatingFileHandler.
        Logs DEBUG level and higher to this file.
        """
        self.file_handler = logging.handlers.RotatingFileHandler(
            self.LOG_FILE, 
            maxBytes=max_bytes, 
            backupCount=backup_count
        )
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)
        self.file_handler.setLevel(logging.DEBUG)
        
        logger = logging.getLogger()
        logger.addHandler(self.file_handler)
        
        logging.info(f"File logger initialized. Target: {self.LOG_FILE}")

    def close(self):
        """Cleanup handler resources."""
        if self.file_handler:
            self.file_handler.close()
            logging.getLogger().removeHandler(self.file_handler)
