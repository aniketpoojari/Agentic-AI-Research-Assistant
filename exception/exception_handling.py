"""Exception handling for the Dynamic Research Assistant."""

import logging
import traceback

logger = logging.getLogger(__name__)

class ResearchAssistantException(Exception):
    """Base exception for all research assistant errors."""
    
    def __init__(self, message, details=None, source_function=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.source_function = source_function
        self.traceback = traceback.format_exc()
        
    def to_dict(self):
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "source_function": self.source_function,
            "traceback": self.traceback
        }

class APIException(ResearchAssistantException):
    """Exception for API-related errors."""
    
    def __init__(self, message, status_code=500, details=None, source_function=None):
        super().__init__(message, details, source_function)
        self.status_code = status_code

class ToolException(ResearchAssistantException):
    """Exception for tool-related errors."""
    
    def __init__(self, message, tool_name=None, details=None, source_function=None):
        super().__init__(message, details, source_function)
        self.tool_name = tool_name

def log_error(error, function_name):
    """Log error with function name and traceback."""
    logger.error(f"Error in {function_name}: {str(error)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
