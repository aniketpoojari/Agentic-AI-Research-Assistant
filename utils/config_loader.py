"""Configuration loader for the Dynamic Research Assistant."""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

class ConfigLoader:
    """Loads and manages configuration from YAML files and environment variables."""
    
    def __init__(self, config_path="config/config.yaml"):
        try:
            self.config_path = Path(config_path)
            self.config = {}
            self._load_config()
        except Exception as e:
            error_msg = f"Error in ConfigLoader.__init__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def _load_config(self):
        """Load configuration from YAML file and environment variables."""
        try:
            # Load environment variables
            load_dotenv()
            
            # Load YAML configuration
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
            else:
                print(f"Config file not found: {self.config_path}")
                self.config = {}
                
        except yaml.YAMLError as e:
            error_msg = f"Error parsing YAML config in _load_config: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error loading config in _load_config: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def get(self, key, default=None):
        """Get configuration value using dot notation (e.g., 'models.groq.model_name')."""
        try:
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            error_msg = f"Error in get for key {key}: {str(e)}"
            print(error_msg)
            return default
    
    def get_env(self, key, default=None):
        """Get environment variable."""
        try:
            return os.getenv(key, default)
        except Exception as e:
            error_msg = f"Error in get_env for key {key}: {str(e)}"
            print(error_msg)
            return default
    
    def get_api_key(self, service):
        """Get API key for a specific service."""
        try:
            key = f"{service.upper()}_API_KEY"
            api_key = self.get_env(key)
            
            if not api_key:
                error_msg = f"API key not found for {service}. Please set {key}"
                print(error_msg)
                raise Exception(error_msg)
            
            return api_key
            
        except Exception as e:
            error_msg = f"Error in get_api_key for service {service}: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def reload(self):
        """Reload configuration from file."""
        try:
            self._load_config()
        except Exception as e:
            error_msg = f"Error in reload: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
