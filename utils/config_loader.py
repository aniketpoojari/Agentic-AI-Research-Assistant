"""Configuration loader for the Dynamic Research Assistant."""

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from dotenv import dotenv_values

class ConfigLoader:
    """Loads configuration from YAML files and environment variables."""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        try:
            # Load .env file directly into a dictionary
            self.env_vars = dotenv_values(".env")
            
            self.config_file = config_file
            self.config_data = {}
            self.load_config()
            
        except Exception as e:
            error_msg = f"Error in ConfigLoader.__init__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)
    
    def load_config(self):
        """Load configuration from YAML file."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r') as file:
                    self.config_data = yaml.safe_load(file) or {}
            else:
                print(f"Warning: Config file {self.config_file} not found. Using defaults.")
                self.config_data = {}
                
        except Exception as e:
            error_msg = f"Error loading config: {str(e)}"
            print(error_msg)
            self.config_data = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        try:
            keys = key.split('.')
            value = self.config_data
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception as e:
            print(f"Error getting config key {key}: {e}")
            return default
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable from .env file directly."""
        try:
            # First check .env file, then fall back to system env
            return self.env_vars.get(key, os.getenv(key, default))
        except Exception as e:
            print(f"Error getting environment variable {key}: {e}")
            return default
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        try:
            key_mapping = {
                "groq": "GROQ_API_KEY",
                "openai": "OPENAI_API_KEY", 
                "anthropic": "ANTHROPIC_API_KEY"
            }
            
            env_key = key_mapping.get(provider.lower())
            if env_key:
                return self.get_env(env_key)
            else:
                print(f"Unknown provider: {provider}")
                return None
                
        except Exception as e:
            print(f"Error getting API key for {provider}: {e}")
            return None
    
    def reload(self):
        """Reload configuration and .env file."""
        try:
            # Reload .env file
            self.env_vars = dotenv_values(".env")
            # Reload config file
            self.load_config()
        except Exception as e:
            print(f"Error reloading config: {e}")
