import logging
import sys
from pythonjsonlogger import jsonlogger
from backend.config import get_settings

settings = get_settings()

def setup_logging():
    """
    Configures structured JSON logging for the application.
    
    If APP_ENV is 'production', multiple lines and stack traces 
    are encapsulated into a single JSON object per log entry.
    
    In 'development', it falls back to a more readable format, 
    but still supports JSON if needed.
    """
    logger = logging.getLogger()
    
    # Determine the log level from settings (default to INFO)
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(log_level)

    handler = logging.StreamHandler(sys.stdout)
    
    # Define fields to include in the JSON log
    # asctime: Timestamp
    # levelname: INFO, ERROR, etc.
    # name: Logger name (e.g. backend.main)
    # message: The actual log message
    format_str = '%(asctime)s %(levelname)s %(name)s %(message)s'
    
    # Configure the JSON formatter
    # rename_fields allows mapping standard logging fields to Google Cloud Logging expected fields
    # e.g. levelname -> severity
    formatter = jsonlogger.JsonFormatter(
        format_str,
        rename_fields={"levelname": "severity", "asctime": "timestamp"},
        datefmt="%Y-%m-%dT%H:%M:%S%z"
    )
    
    handler.setFormatter(formatter)
    
    # Avoid duplicate handlers if setup_logging is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()
        
    logger.addHandler(handler)
    
    return logger

# Create a module-level logger instance
logger = logging.getLogger("health_ai")
