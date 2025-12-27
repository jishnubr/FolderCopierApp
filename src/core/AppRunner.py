import logging
from src.logger.LoggerConfig import LoggerConfig

# Get a logger specific to this module
app_logger = logging.getLogger(__name__)

def setup_environment():
    """Initializes logging and other environment dependencies."""
    print("--- Setting up AI-DevKit Environment ---")
    LoggerConfig.initialize()
    app_logger.info("Environment setup initiated.")

def execute_mission():
    """Simulates the core execution loop."""
    app_logger.info("Starting Mission Execution.")
    
    # Example of verbose debugging (goes only to debug.log)
    app_logger.debug("Internal state check: Buffer is at 45% capacity.")
    app_logger.debug("Calculating trajectory vectors...")

    try:
        # Simulate a successful operation (goes to both debug.log and history.sqlite)
        result = "Task_A_Completed"
        app_logger.info(f"Operation Successful: {result}", context={"mission_step": 101})
        
        # Simulate a configuration change (goes to both)
        app_logger.warning("Configuration file checksum mismatch detected.", context={"config_file": "settings.yaml"})

        # Simulate a serious internal failure (goes to both)
        1 / 0 
        
    except ZeroDivisionError:
        # Error level goes to both, but error stack trace goes to debug.log only
        app_logger.error("Critical runtime failure encountered during Step 2.", exc_info=True, context={"error_code": 500})

    app_logger.info("Mission execution finished.")

def main():
    setup_environment()
    execute_mission()
    LoggerConfig.shutdown()
    print("--- Execution Complete. Check debug.log and history.sqlite ---")

if __name__ == "__main__":
    main()