"""Web search utility for the Dynamic Research Assistant."""

import logging
import requests
import asyncio
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

from utils.config_loader import ConfigLoader
from exception.exception_handling import ToolException

logger = logging.getLogger(__name__)

class WebSearch:
    """Handles web search operations using multiple search providers."""
    
    def __init__(self):
        self.config = ConfigLoader()
        self.timeout = self.config.get("search.timeout", 30)
        self.max_results = self.config.get("search.max_results", 10)
        self.user_agent = self.config.get("search.user_agent", "Research Assistant Bot 1.0")
        
    def search(self, query: str, num_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search the web for the given query."""
        try:
            num_results = num_results or self.max_results
            
            # Try different search providers
            results = []
            
            # Try Tavily first if API key is available
            try:
                tavily_key = self.config.get_env("TAVILY_API_KEY")
                if tavily_key:
                    results = self._search_tavily(query, num_results)
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"Tavily search failed: {e}")
            
            # Try SERP API if available
            try:
                serp_key = self.config.get_env("SERP_API_KEY")
                if serp_key:
                    results = self._search_serp(query, num_results)
                    if results:
                        return results
            except Exception as e:
                logger.warning(f"SERP API search failed: {e}")
            
            # Fallback to DuckDuckGo
            results = self._search_duckduckgo(query, num_results)
            return results
            
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            raise ToolException(f"Web search failed: {e}")
    
    def _search_tavily(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API."""
        api_key = self.config.get_api_key("tavily")
        
        url = "https://api.tavily.com/search"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "include_raw_content": True,
            "max_results": num_results
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for result in data.get("results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "content": result.get("content", ""),
                "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                "source": "tavily"
            })
        
        return results
    
    def _search_serp(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using SERP API."""
        api_key = self.config.get_api_key("serp")
        
        url = "https://serpapi.com/search"
        params = {
            "q": query,
            "api_key": api_key,
            "engine": "google",
            "num": num_results
        }
        
        response = requests.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        
        data = response.json()
        results = []
        
        for result in data.get("organic_results", []):
            results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", ""),
                "content": result.get("snippet", ""),
                "source": "serp"
            })
        
        return results
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (as fallback)."""
        # This is a simplified implementation
        # In production, you might want to use a proper DuckDuckGo API wrapper
        
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}
        headers = {"User-Agent": self.user_agent}
        
        response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        results = []
        
        # Parse DuckDuckGo results
        for result in soup.find_all('div', class_='result')[:num_results]:
            title_elem = result.find('a', class_='result__a')
            snippet_elem = result.find('div', class_='result__snippet')
            
            if title_elem and snippet_elem:
                results.append({
                    "title": title_elem.get_text(strip=True),
                    "url": title_elem.get('href', ''),
                    "snippet": snippet_elem.get_text(strip=True),
                    "content": snippet_elem.get_text(strip=True),
                    "source": "duckduckgo"
                })
        
        return results
    
    async def async_search(self, query: str, num_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Asynchronous web search."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, query, num_results)
    
    def get_page_content(self, url: str) -> str:
        """Extract text content from a web page."""
        try:
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            raise ToolException(f"Failed to extract content: {e}")