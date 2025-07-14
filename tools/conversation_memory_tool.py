"""Conversation memory tool for the Dynamic Research Assistant."""

from langchain.tools import tool
from utils.memory_manager import MemoryManager
from logger.logging import get_logger

logger = get_logger(__name__)

class ConversationMemoryTool:
    def __init__(self):
        try:
            self.memory_manager = MemoryManager()
            self.conversation_memory_tool_list = self._setup_tools()
            logger.info("ConversationMemoryTool Class Initialized")

        except Exception as e:
            error_msg = f"Error in ConversationMemoryTool Class Initialization -> {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for conversation memory"""
        
        @tool
        def store_conversation(conversation_id: str, message: str, role: str = "user"):
            """Store a conversation message"""
            try:
                message_data = {
                    "role": role,
                    "content": message
                }
                self.memory_manager.store_conversation(conversation_id, message_data)
                return {
                    "success": True,
                    "conversation_id": conversation_id,
                    "message_stored": True
                }
            
            except Exception as e:
                error_msg = f"Error in store_conversation tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def get_conversation_history(conversation_id: str, limit: int = 10):
            """Get conversation history for a session"""
            try:
                history = self.memory_manager.get_conversation_history(conversation_id, limit)
                return {
                    "success": True,
                    "session_id": conversation_id,
                    "history": history,
                    "message_count": len(history)
                }
            
            except Exception as e:
                error_msg = f"Error in get_conversation_history tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        

        return [store_conversation, get_conversation_history]
