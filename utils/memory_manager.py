"""Memory management utility for the Dynamic Research Assistant."""

from datetime import datetime
from collections import defaultdict
from logger.logging import get_logger

logger = get_logger(__name__)

class MemoryManager:
    """Manages conversation memory and research context."""

    def __init__(self, memory_limit=50):
        try:
            self.conversations = defaultdict(list)
            self.memory_limit = memory_limit  # Max messages per session
            logger.info("MemoryManager Utility Class Initialized")

        except Exception as e:
            error_msg = f"Error in MemoryManager Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)
    
    
    def store_conversation(self, session_id, message):
        """Store a conversation message."""
        
        try:
            message["timestamp"] = datetime.now().isoformat()
            self.conversations[session_id].append(message)
            
            # Limit memory size
            if len(self.conversations[session_id]) > self.memory_limit:
                self.conversations[session_id] = self.conversations[session_id][-self.memory_limit:]
                
        except Exception as e:
            error_msg = f"Error in store_conversation utility function -> {str(e)}"
            raise Exception(error_msg)
    

    def get_conversation_history(self, session_id, limit=None):
        """Get conversation history for a session."""
        
        try:
            messages = self.conversations.get(session_id, [])
            
            if limit:
                return messages[-limit:]
            
            return messages
            
        except Exception as e:
            error_msg = f"Error in get_conversation_history utility function -> {str(e)}"
            raise Exception(error_msg)