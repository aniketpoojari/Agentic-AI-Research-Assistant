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

    def clear_session(self, session_id):
        """Clear all data for a session."""
        try:
            if session_id in self.conversations:
                del self.conversations[session_id]
            
            if session_id in self.research_context:
                del self.research_context[session_id]
            
            if session_id in self.session_data:
                del self.session_data[session_id]
                
        except Exception as e:
            error_msg = f"Error in clear_session: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def get_memory_stats(self):
        """Get memory usage statistics."""
        try:
            total_conversations = sum(len(messages) for messages in self.conversations.values())
            total_sessions = len(self.conversations)
            
            return {
                "total_sessions": total_sessions,
                "total_conversations": total_conversations,
                "memory_limit": self.memory_limit,
                "research_contexts": len(self.research_context),
                "session_data_entries": len(self.session_data)
            }
            
        except Exception as e:
            error_msg = f"Error in get_memory_stats: {str(e)}"
            logger.error(error_msg)
            return {}

    def store_session_data(self, session_id, key, value):
        """Store session-specific data."""
        try:
            if session_id not in self.session_data:
                self.session_data[session_id] = {}
            
            self.session_data[session_id][key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error in store_session_data: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    def get_session_data(self, session_id, key):
        """Get session-specific data."""
        try:
            session = self.session_data.get(session_id, {})
            data = session.get(key, {})
            return data.get("value")
            
        except Exception as e:
            error_msg = f"Error in get_session_data: {str(e)}"
            logger.error(error_msg)
            return None
    
    def cleanup_old_sessions(self, max_age_hours=24):
        """Remove old session data."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            sessions_to_remove = []
            
            for session_id, messages in self.conversations.items():
                if messages:
                    last_message_time = datetime.fromisoformat(messages[-1]["timestamp"])
                    if last_message_time < cutoff_time:
                        sessions_to_remove.append(session_id)
            
            for session_id in sessions_to_remove:
                self.clear_session(session_id)
                
        except Exception as e:
            error_msg = f"Error in cleanup_old_sessions: {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)
