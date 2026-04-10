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
    # Rationale: In development, we want more visibility into DB and Server cycles.
    is_dev = os.getenv("ENVIRONMENT", "development").lower() == "development"
    third_party_level = logging.WARNING if not is_dev else logging.INFO
    db_level = logging.WARNING if not is_dev else logging.INFO

    for logger_name in [
        "sqlalchemy.engine", 
        "sqlalchemy.dialects",
        "sqlalchemy.orm",
        "httpx", 
        "httpcore", 
        "uvicorn"
    ]:
        logging.getLogger(logger_name).setLevel(third_party_level)
        logging.getLogger(logger_name).propagate = False

    # DB Pool Logging is critical for hang detection
    logging.getLogger("sqlalchemy.pool").setLevel(db_level)
    logging.getLogger("uvicorn.access").setLevel(third_party_level)
    logging.getLogger("uvicorn.error").setLevel(third_party_level)
    
    # FastEmbed/Model logging can be chatty
    logging.getLogger("fastembed").setLevel(logging.INFO)
    
    mode_emoji = "🔥" if is_dev else "🛡️"
    logger.info(f"{mode_emoji} [System] Elite Logging System Initialized (Mode: {os.getenv('ENVIRONMENT', 'unknown')}).")

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
