"""Simple conversation memory tool for the Dynamic Research Assistant."""

from langchain.tools import tool
from logger.logging import get_logger

logger = get_logger(__name__)


class ConversationMemoryTool:
    def __init__(self, memory_limit: int = 20):
        """Initialize with a memory limit (max messages to store per session)."""
        self.memory_limit = memory_limit
        self.conversations = {}  # {session_id: [messages]}
        self.current_session_id = None
        self.conversation_memory_tool_list = self._setup_tools()
        logger.info(f"ConversationMemoryTool initialized with limit={memory_limit}")

    def set_session_id(self, session_id: str):
        """Set current session ID."""
        self.current_session_id = session_id

    def add_message(self, role: str, content: str):
        """Add a message to current session's memory."""
        if not self.current_session_id:
            return

        if self.current_session_id not in self.conversations:
            self.conversations[self.current_session_id] = []

        self.conversations[self.current_session_id].append({
            "role": role,
            "content": content
        })

        # Keep only last N messages
        if len(self.conversations[self.current_session_id]) > self.memory_limit:
            self.conversations[self.current_session_id] = \
                self.conversations[self.current_session_id][-self.memory_limit:]

        logger.info(f"Added {role} message to session {self.current_session_id[:8]}...")

    def _setup_tools(self):
        """Setup the memory tools."""

        @tool
        def get_conversation_history(limit: int = 10):
            """Get previous conversation history. Use this when user asks about previous questions or past conversation."""
            try:
                session_id = self.current_session_id
                if not session_id or session_id not in self.conversations:
                    return {
                        "success": True,
                        "history": [],
                        "message_count": 0,
                        "note": "No conversation history found"
                    }

                history = self.conversations[session_id][-limit:]
                logger.info(f"Retrieved {len(history)} messages for session {session_id[:8]}...")

                return {
                    "success": True,
                    "history": history,
                    "message_count": len(history)
                }

            except Exception as e:
                error_msg = f"Error in get_conversation_history -> {str(e)}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

        return [get_conversation_history]
