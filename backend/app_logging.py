import logging
import sys
import os

# Elite V2.2: Unified Logging System
# Emojis for professional terminal aesthetics

LOG_FORMAT = "%(levelname)s - %(asctime)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging():
    """
    [CTO ELITE] Centralized logger setup.
    Silences noisy libraries and unifies the boot sequence format.
    """
    # Root logger configuration
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout
    )

    # Main Gateway Logger
    logger = logging.getLogger("api-gateway")
    logger.setLevel(logging.INFO)

    # Silence Noisy Third-Party Libraries (Aggressive V2.2)
    for logger_name in [
        "sqlalchemy", 
        "sqlalchemy.engine", 
        "sqlalchemy.pool", 
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
        "httpx", 
        "httpcore", 
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error"
    ]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
        logging.getLogger(logger_name).propagate = False # Prevent propagation to root
    
    # FastEmbed/Model logging can be chatty
    logging.getLogger("fastembed").setLevel(logging.INFO)
    
    logger.info("🎨 [System] Elite Logging System Initialized.")

def get_logger(name: str):
    return logging.getLogger(name)
