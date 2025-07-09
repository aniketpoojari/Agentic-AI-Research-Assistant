"""Exception handling for the Dynamic Research Assistant."""

import logging
from typing import Any, Dict, Optional
from functools import wraps
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class ResearchAssistantException(Exception):
    """Base exception for all research assistant errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }

class APIException(ResearchAssistantException):
    """Exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.status_code = status_code

class ToolException(ResearchAssistantException):
    """Exception for tool-related errors."""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.tool_name = tool_name

def handle_exceptions(func):
    """Decorator to handle exceptions in API endpoints."""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIException as e:
            # Re-raise API exceptions with proper HTTP status
            raise HTTPException(
                status_code=e.status_code,
                detail={
                    "message": e.message,
                    "details": e.details
                }
            )
        except ToolException as e:
            logger.error(f"Tool error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Tool error: {e.message}",
                    "tool": e.tool_name,
                    "details": e.details
                }
            )
        except ResearchAssistantException as e:
            logger.error(f"Research Assistant error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "message": f"Internal error: {e.message}",
                    "details": e.details
                }
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail={
                    "message": "An unexpected error occurred",
                    "details": {"original_error": str(e)}
                }
            )
    
    return wrapper

def handle_tool_exceptions(func):
    """Decorator specifically for tool functions."""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ToolException:
            raise  # Re-raise tool exceptions
        except Exception as e:
            logger.error(f"Tool execution failed in {func.__name__}: {e}")
            raise ToolException(
                message=f"Tool execution failed: {str(e)}",
                tool_name=func.__name__,
                details={"original_error": str(e)}
            )
    
    return wrapper