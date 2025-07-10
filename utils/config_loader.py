"""Configuration loader for the Dynamic Research Assistant."""

import os
import yaml
from typing import Any
from pathlib import Path
from dotenv import load_dotenv

# from exception.exception_handling import ConfigurationException

class ConfigLoader:
    """Loads and manages configuration from YAML files and environment variables."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file and environment variables."""
        # Load environment variables
        load_dotenv()
        
        # Load YAML configuration
        # try:
        if self.config_path.exists():
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file) or {}
            # else:
                # raise ConfigurationException(f"Config file not found: {self.config_path}")
        # except yaml.YAMLError as e:
        #     raise ConfigurationException(f"Error parsing YAML config: {e}")
        # except Exception as e:
        #     raise ConfigurationException(f"Error loading config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'models.groq.model_name')."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_env(self, key: str, default: Any = None) -> Any:
        """Get environment variable."""
        return os.getenv(key, default)
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a specific service."""
        key = f"{service.upper()}_API_KEY"
        api_key = self.get_env(key)
        
        # if not api_key:
            # raise ConfigurationException(f"API key not found for {service}. Please set {key}")
        
        return api_key
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()