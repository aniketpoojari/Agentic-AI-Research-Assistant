"""Web search tool for the Dynamic Research Assistant."""

from langchain_core.tools import tool
from utils.websearch import WebSearch
from logger.logging import get_logger

logger = get_logger(__name__)

class WebSearchTool:
    def __init__(self):
        try:
            self.web_search = WebSearch()
            self.web_search_tool_list = self._setup_tools()
            logger.info("WebSearchTool Class Initialized")
        
        except Exception as e:
            error_msg = f"Error in WebSearchTool Class Initialization -> {str(e)}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def _setup_tools(self):
        """Setup all tools for web search"""
        
        @tool
        def search_web(query: str, max_results: int = 10):
            """Search the web for information on a given query"""
            
            try:
                results = self.web_search.search(query, max_results)
                return {
                    "success": True,
                    "results": results,
                    "query": query,
                    "total_results": len(results)
                }
            
            except Exception as e:
                error_msg = f"Error in search_web tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "query": query
                }
        
        @tool
        def get_page_content(url: str):
            """Extract full content from a specific web page"""
            
            try:
                content = self.web_search.get_page_content(url)
                return {
                    "success": True,
                    "content": content,
                    "url": url
                }
            
            except Exception as e:
                error_msg = f"Error in get_page_content tool -> {str(e)}"
                logger.error(error_msg)
                return {
                    "success": False,
                    "error": error_msg,
                    "url": url
                }
        
        return [search_web, get_page_content]
