import logging
# Note: This service now relies on the GLOBAL_LOGGER provided by LoggerConfig

system_logger = logging.getLogger(__name__)

def check_status(system_id: str):
    """Checks system health and logs relevant events."""
    
    system_logger.debug(f"System {system_id}: Performing deep memory check.") # Only debug.log
    
    if system_id == "HEALTHY_UNIT_01":
        # This is an INFO level event, intended for audit tracking
        system_logger.info(f"System {system_id} reported operational status: OK", 
                           context={"unit_id": system_id, "uptime_hours": 48.5})
        return True
    else:
        # This is a WARNING level event, intended for audit tracking
        system_logger.warning(f"System {system_id} reported degraded performance.", 
                              context={"unit_id": system_id, "latency_ms": 550})
        return False

# Example usage would be integrated into AppRunner/Execution flow for testing purposes.
# For strict adherence to the prompt, this file serves as the location for modification example.