"""Simple logging setup for the Dynamic Research Assistant."""

import logging
import os
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Simple logging setup."""
    # Create logs directory if needed
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Basic configuration
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

def get_logger(name: str):
    """Get a logger."""
    return logging.getLogger(name)

# Initialize with environment variables
setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "logs/app.log")
)
