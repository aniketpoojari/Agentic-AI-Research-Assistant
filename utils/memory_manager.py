"""Memory management utility for the Dynamic Research Assistant."""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages conversation memory and research context."""
    
    def __init__(self, memory_limit=1000):
        try:
            self.memory_limit = memory_limit
            self.conversations = defaultdict(list)
            self.research_context = defaultdict(dict)
            self.session_data = defaultdict(dict)
        except Exception as e:
            error_msg = f"Error in MemoryManager.__init__: {str(e)}"
            logger.error(error_msg)
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
            error_msg = f"Error in store_conversation: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    

    def get_conversation_history(self, session_id, limit=None):
        """Get conversation history for a session."""
        try:
            messages = self.conversations.get(session_id, [])
            
            if limit:
                return messages[-limit:]
            
            return messages
            
        except Exception as e:
            error_msg = f"Error in get_conversation_history: {str(e)}"
            logger.error(error_msg)
            return []