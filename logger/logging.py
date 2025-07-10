"""Simple logging setup for the Dynamic Research Assistant."""

import logging
import os
from pathlib import Path

def setup_logging(log_level="INFO", log_file=None):
    """Simple logging setup."""
    try:
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
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic logging
        logging.basicConfig(level=logging.INFO)

def get_logger(name):
    """Get a logger."""
    try:
        return logging.getLogger(name)
    except Exception as e:
        print(f"Error getting logger {name}: {e}")
        return logging.getLogger()

# Initialize with environment variables
try:
    setup_logging(
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE", "logs/app.log")
    )
except Exception as e:
    print(f"Error initializing logging: {e}")
