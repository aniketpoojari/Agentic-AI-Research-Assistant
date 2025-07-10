"""Conversation memory tool for the Dynamic Research Assistant."""

from langchain.tools import tool
from dotenv import load_dotenv
from utils.memory_manager import MemoryManager

class ConversationMemoryTool:
    def __init__(self):
        try:
            load_dotenv()
            self.memory_manager = MemoryManager()
            self.conversation_memory_tool_list = self._setup_tools()
        except Exception as e:
            error_msg = f"Error in ConversationMemoryTool.__init__: {str(e)}"
            print(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for conversation memory"""
        
        @tool
        def store_conversation(session_id: str, message: str, role: str = "user"):
            """Store a conversation message"""
            try:
                message_data = {
                    "role": role,
                    "content": message
                }
                self.memory_manager.store_conversation(session_id, message_data)
                return {
                    "success": True,
                    "session_id": session_id,
                    "message_stored": True
                }
            except Exception as e:
                error_msg = f"Error in store_conversation: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def get_conversation_history(session_id: str, limit: int = 10):
            """Get conversation history for a session"""
            try:
                history = self.memory_manager.get_conversation_history(session_id, limit)
                return {
                    "success": True,
                    "session_id": session_id,
                    "history": history,
                    "message_count": len(history)
                }
            except Exception as e:
                error_msg = f"Error in get_conversation_history: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def get_memory_stats():
            """Get memory usage statistics"""
            try:
                stats = self.memory_manager.get_memory_stats()
                return {
                    "success": True,
                    "stats": stats
                }
            except Exception as e:
                error_msg = f"Error in get_memory_stats: {str(e)}"
                print(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }

        return [store_conversation, get_conversation_history, get_memory_stats]
