"""Summarization tool for the Dynamic Research Assistant."""

from langchain_core.tools import tool
from utils.summarizer import Summarizer
from logger.logging import get_logger
import json

logger = get_logger(__name__)

class SummarizationTool:
    def __init__(self, model_provider="groq"):
        try:
            self.summarizer = Summarizer(model_provider)
            self.summarization_tool_list = self._setup_tools()
            logger.info("SummarizationTool Class Initialized")
        
        except Exception as e:
            error_msg = f"Error in SummarizationTool Class Initialization -> {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for summarization"""
        
        @tool
        def summarize_text(text: str, max_length: int = 500):
            """Summarize a given text to specified length"""
            
            try:
                summary = self.summarizer.summarize_text(text, max_length)
                return {
                    "success": True,
                    "summary": summary,
                    "original_length": len(text),
                    "summary_length": len(summary)
                }
            
            except Exception as e:
                error_msg = f"Error in summarize_text tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def create_executive_summary(documents: str, topic: str):
            """Create executive summary from multiple documents about a topic"""
            
            try:
                # Parse documents string as JSON if needed
                try:
                    docs = json.loads(documents)
                except:
                    docs = [{"content": documents, "title": "Document"}]
                
                summary = self.summarizer.create_executive_summary(docs, topic)
                return {
                    "success": True,
                    "executive_summary": summary,
                    "topic": topic,
                    "documents_processed": len(docs)
                }
            
            except Exception as e:
                error_msg = f"Error in create_executive_summary tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        @tool
        def extract_key_points(text: str, num_points: int = 5):
            """Extract key points from text"""
            
            try:
                key_points = self.summarizer.extract_key_points(text, num_points)
                return {
                    "success": True,
                    "key_points": key_points,
                    "num_points": len(key_points)
                }
            
            except Exception as e:
                error_msg = f"Error in extract_key_points tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        return [summarize_text, create_executive_summary, extract_key_points]
