from app_logger import logger
from audit_logger import AUDIT_LOGGER
import time
import sys

def perform_critical_task(data_source):
    # Simulates a key operational milestone.
    logger.info(f"Task processing for {data_source}.")
    AUDIT_LOGGER.info(f"MISSION_START: Initializing task for source {data_source}.")
    
    if not data_source:
        logger.error(f"Runtime Error during processing: Data source cannot be empty.")
        AUDIT_LOGGER.error(f"MISSION_FAILURE: Task aborted due to ValueError in source {data_source}.")
        raise ValueError("Data source cannot be empty.")
    
    time.sleep(0.1)
    AUDIT_LOGGER.info(f"MISSION_COMPLETE: Processed {data_source} successfully.")

if __name__ == '__main__':
    logger.info("--- Starting Main Execution ---")
    
    # MISSION-007: Handle Context Menu Arguments
    source_path = "Default_Folder"
    if len(sys.argv) > 1:
        source_path = sys.argv[1]
        logger.info(f"Launched with arguments: {source_path}")
    else:
        logger.info("No arguments provided. Running in default mode.")

    try:
        perform_critical_task(source_path)
    except Exception as e:
        logger.error(f"Execution failed: {e}")

    logger.info("--- Execution Finished ---")
