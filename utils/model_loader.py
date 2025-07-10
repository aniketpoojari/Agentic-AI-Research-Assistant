"""Model loader for different LLM providers."""

import logging
from typing import Any, Dict
from langchain_groq import ChatGroq
# from langchain_openai import ChatOpenAI

from utils.config_loader import ConfigLoader
# from exception.exception_handling import ConfigurationException

logger = logging.getLogger(__name__)

class ModelLoader:
    """Loads and configures language models from different providers."""
    
    def __init__(self, model_provider: str = "groq"):
        self.config = ConfigLoader()
        self.model_provider = model_provider.lower()
        self.llm = None
        
    def load_llm(self) -> Any:
        """Load the specified language model."""
        if self.llm is not None:
            return self.llm
            
        try:
            if self.model_provider == "groq":
                self.llm = self._load_groq_model()
        except Exception as e:
            logger.error(f"Failed to load {self.model_provider} model: {e}")
        # elif self.model_provider == "openai":
            # self.llm = self._load_openai_model()
        # else:
            # raise ConfigurationException(f"Unsupported model provider: {self.model_provider}")
        
        logger.info(f"Successfully loaded {self.model_provider} model")
        return self.llm
            
        # except Exception as e:
        #     logger.error(f"Failed to load {self.model_provider} model: {e}")
        #     raise ConfigurationException(f"Failed to load model: {e}")
    
    def _load_groq_model(self) -> ChatGroq:
        """Load Groq model."""
        api_key = self.config.get_api_key("groq")
        # print(api_key)
        model_name = self.config.get("models.groq.model_name", "llama3-8b-8192")
        temperature = self.config.get("models.groq.temperature", 0.1)
        max_tokens = self.config.get("models.groq.max_tokens", 4096)
        
        return ChatGroq(
            groq_api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    '''def _load_openai_model(self) -> ChatOpenAI:
        """Load OpenAI model."""
        api_key = self.config.get_api_key("openai")
        model_name = self.config.get("models.openai.model_name", "gpt-4-turbo-preview")
        temperature = self.config.get("models.openai.temperature", 0.1)
        max_tokens = self.config.get("models.openai.max_tokens", 4096)
        
        return ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )'''
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if self.llm is None:
            return {"provider": self.model_provider, "loaded": False}
        
        return {
            "provider": self.model_provider,
            "loaded": True,
            "model_name": getattr(self.llm, 'model_name', 'unknown'),
            "temperature": getattr(self.llm, 'temperature', 'unknown'),
            "max_tokens": getattr(self.llm, 'max_tokens', 'unknown')
        }