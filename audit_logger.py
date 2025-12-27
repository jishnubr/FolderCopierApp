import logging
import sys

def setup_audit_logger():
    """Sets up the dedicated logger for immutable audit records."""
    audit_logger = logging.getLogger('AppAudit')
    audit_logger.setLevel(logging.INFO)

    # Audit logs should generally not propagate to other handlers
    audit_logger.propagate = False
    if audit_logger.hasHandlers():
        return audit_logger

    # Audit Formatter: Focus on structured data, minimal overhead
    audit_formatter = logging.Formatter(
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "event": "%(message)s"}'
    )

    # 1. Audit File Handler (Simulating DB write or dedicated audit file)
    # In a real system, this handler would be a custom DatabaseHandler.
    ah = logging.FileHandler('audit_trail.log')
    ah.setLevel(logging.INFO)
    ah.setFormatter(audit_formatter)
    audit_logger.addHandler(ah)

    # Optional: Console output for auditing during development (can be removed later)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(audit_formatter)
    audit_logger.addHandler(ch)

    return audit_logger

# Initialize and export the dedicated audit logger instance
AUDIT_LOGGER = setup_audit_logger()