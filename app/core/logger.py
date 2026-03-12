import logging
import sys

def setup_logger(name: str = "rdd_backend"):
    logger = logging.getLogger(name)
    
    # Prevent duplicate logs if initialized multiple times
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Output to console
        handler = logging.StreamHandler(sys.stdout)
        
        # The format: [Timestamp] - [Level] - [Message]
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

# Export the initialized logger
logger = setup_logger()