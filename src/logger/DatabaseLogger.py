import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseLogger:
    """Handles writing structured audit events to an SQLite database."""
    
    DB_NAME = "history.sqlite"

    def __init__(self):
        self._init_db()

    def _init_db(self):
        """Ensures the SQLite database and the audit table exist."""
        try:
            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"Database logger initialized. Target: {self.DB_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    def write_audit(self, level: str, message: str, context: dict = None):
        """Writes a structured record to the audit trail."""
        timestamp = datetime.now().isoformat()
        
        context_str = str(context) if context else None
        
        try:
            conn = sqlite3.connect(self.DB_NAME)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO audit_trail (timestamp, level, message, context) VALUES (?, ?, ?, ?)",
                (timestamp, level, message, context_str)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            # Critical fallback: log the database failure to standard error/file logger if available
            logger.error(f"CRITICAL: Failed to write audit entry to DB: {e} | Data: {message}")
