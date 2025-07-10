"""Conversation memory tool for the Dynamic Research Assistant."""

from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
from utils.memory_manager import MemoryManager

class ConversationMemoryTool:
    def __init__(self):
        load_dotenv()
        self.memory_manager = MemoryManager()
        self.conversation_memory_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
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
                return {
                    "success": False,
                    "error": "Message storage failed: " + str(e)
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
                return {
                    "success": False,
                    "error": "Failed to get conversation history: " + str(e)
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
                return {
                    "success": False,
                    "error": "Failed to get memory stats: " + str(e)
                }

                
        return [store_conversation, get_conversation_history, get_memory_stats]
