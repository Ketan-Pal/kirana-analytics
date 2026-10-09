import logging
import sys
from config import settings

def setup_logging():
    """Configures structured application logging."""
    level = getattr(logging, settings.log_level, logging.INFO)
    log_format = "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_logger(name: str) -> logging.Logger:
    """Returns a named logger instance."""
    return logging.getLogger(name)

# Initialize on import
setup_logging()
