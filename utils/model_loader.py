"""Model loader for different LLM providers."""

from typing import Any, Dict
from langchain_groq import ChatGroq

from utils.config_loader import ConfigLoader
from logger.logging import get_logger

logger = get_logger(__name__)

class ModelLoader:
    """Loads and configures language models from different providers."""
    
    def __init__(self, model_provider: str = "groq"):
        try:
            self.config = ConfigLoader()
            self.model_provider = model_provider.lower()
            self.llm = None
            logger.info(f"ModelLoader Utility Class Initialized")
        
        except Exception as e:
            error_msg = f"Error in ModelLoader Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)
        
    def load_llm(self) -> Any:
        """Load the specified language model."""
        try:
            if self.llm is not None:
                logger.info(f"Returning cached {self.model_provider} model")
                return self.llm
                
            if self.model_provider == "groq":
                self.llm = self._load_groq_model()
            # elif self.model_provider == "openai":
                # self.llm = self._load_openai_model()
            # elif self.model_provider == "anthropic":
                # self.llm = self._load_anthropic_model()
            else:
                error_msg = f"Unsupported model provider: {self.model_provider}"
                raise Exception(error_msg)
            
            # Skip validation to avoid extra LangSmith traces
            # self.validate_model()

            logger.info(f"Successfully loaded {self.model_provider} model")
            return self.llm
            
        except Exception as e:
            error_msg = f"Error in load_llm utility function -> {str(e)}"
            raise Exception(error_msg)
    
    def _load_groq_model(self) -> ChatGroq:
        """Load Groq model."""
        
        try:
            api_key = self.config.get_api_key("groq")
            if not api_key:
                error_msg = "Groq API key not found. Please set GROQ_API_KEY environment variable"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            model_name = self.config.get_env("MODEL_NAME", "llama-3.1-8b-instant")
            temperature = self.config.get_env("MODEL_TEMPERATURE", 0.1)
            max_tokens = self.config.get("MODEL_MAX_TOKENS", 4096)
            
            logger.info(f"Loading Groq model: {model_name}")
            
            return ChatGroq(
                groq_api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        except Exception as e:
            error_msg = f"Error in _load_groq_model utility function -> {str(e)}"
            raise Exception(error_msg)
    
    '''def _load_openai_model(self) -> ChatOpenAI:
        """Load OpenAI model."""
        try:
            api_key = self.config.get_api_key("openai")
            if not api_key:
                error_msg = "OpenAI API key not found. Please set OPENAI_API_KEY environment variable"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            model_name = self.config.get("models.openai.model_name", "gpt-4-turbo-preview")
            temperature = self.config.get("models.openai.temperature", 0.1)
            max_tokens = self.config.get("models.openai.max_tokens", 4096)
            
            logger.info(f"Loading OpenAI model: {model_name}")
            
            return ChatOpenAI(
                openai_api_key=api_key,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        except Exception as e:
            error_msg = f"Error in _load_openai_model: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def _load_anthropic_model(self) -> ChatAnthropic:
        """Load Anthropic model."""
        try:
            api_key = self.config.get_api_key("anthropic")
            if not api_key:
                error_msg = "Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable"
                logger.error(error_msg)
                raise Exception(error_msg)
                
            model_name = self.config.get("models.anthropic.model_name", "claude-3-sonnet-20240229")
            temperature = self.config.get("models.anthropic.temperature", 0.1)
            max_tokens = self.config.get("models.anthropic.max_tokens", 4096)
            
            logger.info(f"Loading Anthropic model: {model_name}")
            
            return ChatAnthropic(
                anthropic_api_key=api_key,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
        except Exception as e:
            error_msg = f"Error in _load_anthropic_model: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)'''
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        try:
            if self.llm is None:
                return {
                    "provider": self.model_provider,
                    "loaded": False,
                    "error": "Model not loaded"
                }
            
            base_info = {
                "provider": self.model_provider,
                "loaded": True,
                "model_name": getattr(self.llm, 'model_name', getattr(self.llm, 'model', 'unknown')),
                "temperature": getattr(self.llm, 'temperature', 'unknown'),
                "max_tokens": getattr(self.llm, 'max_tokens', 'unknown')
            }
            
            # Add provider-specific information
            if self.model_provider == "groq":
                base_info.update({
                    "api_base": getattr(self.llm, 'groq_api_base', 'default'),
                    "streaming": getattr(self.llm, 'streaming', False)
                })
            elif self.model_provider == "openai":
                base_info.update({
                    "organization": getattr(self.llm, 'openai_organization', None),
                    "api_version": getattr(self.llm, 'openai_api_version', None)
                })
            elif self.model_provider == "anthropic":
                base_info.update({
                    "api_version": getattr(self.llm, 'anthropic_api_version', None)
                })
            
            return base_info
            
        except Exception as e:
            error_msg = f"Error in get_model_info: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return {
                "provider": self.model_provider,
                "loaded": False,
                "error": error_msg
            }
    
    def validate_model(self) -> bool:
        """Validate that the model is working correctly."""
        try:
            if self.llm is None:
                error_msg = "Model not loaded, cannot validate"
                raise Exception(error_msg)
            
            # Simple test prompt
            test_prompt = "Hello, please respond with 'OK' if you can understand this message."
            response = self.llm.invoke(test_prompt)
            
            if hasattr(response, 'content') and response.content:
                logger.info("Model validation successful")
                return True
            else:
                error_msg = "Model validation failed - no response content"
                raise Exception(error_msg)
                
                
        except Exception as e:
            error_msg = f"Error in validate_model utility function -> {str(e)}"
            raise Exception(error_msg)
    

    def reload_model(self) -> Any:
        """Reload the model (useful for configuration changes)."""
        try:
            logger.info(f"Reloading {self.model_provider} model")
            self.llm = None
            self.config.reload()
            return self.load_llm()
            
        except Exception as e:
            error_msg = f"Error in reload_model: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def switch_provider(self, new_provider: str) -> Any:
        """Switch to a different model provider."""
        try:
            logger.info(f"Switching from {self.model_provider} to {new_provider}")
            self.model_provider = new_provider.lower()
            self.llm = None
            return self.load_llm()
            
        except Exception as e:
            error_msg = f"Error in switch_provider: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def get_available_providers(self) -> list:
        """Get list of available model providers."""
        try:
            providers = []
            
            # Check Groq
            if self.config.get_env("GROQ_API_KEY"):
                providers.append("groq")
            
            # Check OpenAI
            if self.config.get_env("OPENAI_API_KEY"):
                providers.append("openai")
            
            # Check Anthropic
            if self.config.get_env("ANTHROPIC_API_KEY"):
                providers.append("anthropic")
            
            return providers
            
        except Exception as e:
            error_msg = f"Error in get_available_providers: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            return []
    
    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            if hasattr(self, 'llm') and self.llm is not None:
                logger.info(f"Cleaning up {self.model_provider} model")
        except Exception as e:
            # Don't raise exceptions in destructor
            pass
