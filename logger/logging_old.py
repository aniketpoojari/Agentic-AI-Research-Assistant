"""Logging configuration for the Dynamic Research Assistant."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from utils.config_loader import ConfigLoader

def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: int = 10485760,  # 10MB
    backup_count: int = 5
) -> None:
    """Setup logging configuration."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name."""
    return logging.getLogger(name)

# Initialize logging on module import
try:
    config = ConfigLoader()
    setup_logging(
        log_level=config.get("logging.level", "INFO"),
        log_file=config.get("logging.file"),
        max_file_size=config.get("logging.max_file_size", 10485760),
        backup_count=config.get("logging.backup_count", 5)
    )
except Exception as e:
    # Fallback to basic logging if config fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logging.getLogger(__name__).warning(f"Failed to load logging config: {e}")