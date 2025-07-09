"""Memory management utility for the Dynamic Research Assistant."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages conversation memory and research context."""
    
    def __init__(self, memory_limit: int = 1000):
        self.memory_limit = memory_limit
        self.conversations = defaultdict(list)
        self.research_context = defaultdict(dict)
        self.session_data = defaultdict(dict)
    
    def store_conversation(self, session_id: str, message: Dict[str, Any]) -> None:
        """Store a conversation message."""
        try:
            message["timestamp"] = datetime.now().isoformat()
            self.conversations[session_id].append(message)
            
            # Limit memory size
            if len(self.conversations[session_id]) > self.memory_limit:
                self.conversations[session_id] = self.conversations[session_id][-self.memory_limit:]
                
        except Exception as e:
            logger.error(f"Failed to store conversation: {e}")
    
    def get_conversation_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            messages = self.conversations.get(session_id, [])
            
            if limit:
                return messages[-limit:]
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []

    def clear_session(self, session_id: str) -> None:
        """Clear all data for a session."""
        try:
            if session_id in self.conversations:
                del self.conversations[session_id]
            
            if session_id in self.research_context:
                del self.research_context[session_id]
            
            if session_id in self.session_data:
                del self.session_data[session_id]
                
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")

    def get_memory_stats(self) -> Dict[str, Any]:
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
            logger.error(f"Failed to get memory stats: {e}")
            return {}
    



    
    def store_session_data(self, session_id: str, key: str, value: Any) -> None:
        """Store session-specific data."""
        try:
            if session_id not in self.session_data:
                self.session_data[session_id] = {}
            
            self.session_data[session_id][key] = {
                "value": value,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to store session data: {e}")
    
    def get_session_data(self, session_id: str, key: str) -> Any:
        """Get session-specific data."""
        try:
            session = self.session_data.get(session_id, {})
            data = session.get(key, {})
            return data.get("value")
            
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> None:
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
            logger.error(f"Failed to cleanup old sessions: {e}")
    