"""Web search tool for the Dynamic Research Assistant."""

from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
from utils.websearch import WebSearch

class WebSearchTool:
    def __init__(self):
        load_dotenv()
        self.web_search = WebSearch()
        self.web_search_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for web search"""
        
        @tool
        def search_web(query: str, num_results: int = 10):
            """Search the web for information on a given query"""
            try:
                results = self.web_search.search(query, num_results)
                return {
                    "success": True,
                    "results": results,
                    "query": query,
                    "total_results": len(results)
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
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
                return {
                    "success": False,
                    "error": str(e),
                    "url": url
                }
        
        return [search_web, get_page_content]
