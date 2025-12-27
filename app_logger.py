import logging
import sys

def setup_logger():
    """Sets up the primary application logger for runtime debugging and errors."""
    logger = logging.getLogger('AppRuntime')
    logger.setLevel(logging.DEBUG)

    # Prevent propagation if this logger is imported into a system that already has handlers configured
    logger.propagate = False
    if logger.hasHandlers():
        return logger

    # 1. Console Handler (StreamHandler) - Outputs INFO and above to stderr
    ch = logging.StreamHandler(sys.stderr)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # 2. File Handler (For detailed debugging, simulating a local debug log file)
    fh = logging.FileHandler('runtime_debug.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

# Initialize and export the default logger instance
logger = setup_logger()

if __name__ == '__main__':
    # Example usage if run directly
    logger.debug("App Logger: Debug message.")
    logger.info("App Logger: Application started successfully.")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.error("App Logger: Encountered an unexpected division by zero error.", exc_info=True)