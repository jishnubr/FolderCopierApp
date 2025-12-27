import logging
import logging.config
from src.logger.DatabaseLogger import DatabaseLogger
from src.logger.FileLogger import FileLogger

# Setup the root logger configuration globally once
GLOBAL_LOGGER = logging.getLogger()
GLOBAL_LOGGER.setLevel(logging.INFO) # Default application level

class LoggerConfig:
    
    _db_logger: DatabaseLogger = None
    _file_logger: FileLogger = None
    _initialized: bool = False

    @classmethod
    def initialize(cls):
        """Initializes both the file and database logging systems."""
        if cls._initialized:
            return

        # 1. Initialize the File Logger (Handles DEBUG and higher)
        cls._file_logger = FileLogger()
        
        # 2. Initialize the Database Logger (Handles structured audit output)
        cls._db_logger = DatabaseLogger()

        # 3. Setup custom handler for audit logging (INFO/WARN/ERROR only)
        class AuditHandler(logging.Handler):
            def emit(self, record):
                # Only push INFO, WARNING, ERROR, CRITICAL to the database
                if record.levelno >= logging.INFO and record.levelno < logging.CRITICAL:
                    context = getattr(record, 'context', None)
                    cls._db_logger.write_audit(
                        level=record.levelname,
                        message=self.format(record),
                        context=context
                    )
                elif record.levelno == logging.CRITICAL:
                    # Critical errors might still warrant an audit trail entry
                    context = getattr(record, 'context', None)
                    cls._db_logger.write_audit(
                        level=record.levelname,
                        message=record.getMessage(),
                        context=context
                    )
                    
        audit_handler = AuditHandler()
        audit_handler.setLevel(logging.INFO)
        
        # Format for the audit handler must match what we want stored in the DB message column
        audit_formatter = logging.Formatter('%(levelname)s: %(message)s')
        audit_handler.setFormatter(audit_formatter)
        
        GLOBAL_LOGGER.addHandler(audit_handler)

        cls._initialized = True
        logging.info("Logger Configuration complete: Debug file and Audit DB active.")


    @classmethod
    def shutdown(cls):
        """Cleanly shuts down all loggers."""
        if cls._file_logger:
            cls._file_logger.close()
        # Database connection is handled within the write method, but stopping ensures no new writes happen
        cls._initialized = False
