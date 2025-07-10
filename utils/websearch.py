"""Web search utility for the Dynamic Research Assistant."""

import logging
import requests
import asyncio
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

from utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class WebSearch:
    """Handles web search operations using multiple search providers."""
    
    def __init__(self):
        try:
            self.config = ConfigLoader()
            self.timeout = self.config.get("search.timeout", 30)
            self.max_results = self.config.get("search.max_results", 10)
            self.user_agent = self.config.get("search.user_agent", "Research Assistant Bot 1.0")
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.user_agent})
            logger.info("WebSearch initialized successfully")
        except Exception as e:
            error_msg = f"Error in WebSearch.__init__: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
        
    def search(self, query, num_results=None):
        """Search the web for the given query."""
        try:
            if not query or not query.strip():
                return []
            
            num_results = num_results or self.max_results
            logger.info(f"Starting web search for query: {query[:100]}...")
            
            # Try Tavily first if API key is available
            tavily_key = self.config.get_env("TAVILY_API_KEY")
            if tavily_key:
                try:
                    results = self._search_tavily(query, num_results)
                    if results:
                        logger.info(f"Tavily search returned {len(results)} results")
                        return results
                except Exception as e:
                    logger.warning(f"Tavily search failed: {e}")
            
            # Try DuckDuckGo as fallback
            try:
                results = self._search_duckduckgo(query, num_results)
                if results:
                    logger.info(f"DuckDuckGo search returned {len(results)} results")
                    return results
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed: {e}")
            
            # If all searches fail, return empty list
            logger.warning("All search providers failed")
            return []
            
        except Exception as e:
            error_msg = f"Error in search: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def _search_tavily(self, query, num_results):
        """Search using Tavily API."""
        try:
            api_key = self.config.get_api_key("tavily")
            if not api_key:
                return []
            
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
            
            response = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for result in data.get("results", []):
                try:
                    search_result = {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "snippet": result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", ""),
                        "source": "tavily",
                        "score": result.get("score", 0.0)
                    }
                    results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing Tavily result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            error_msg = f"Error in _search_tavily: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def _search_duckduckgo(self, query, num_results):
        """Search using DuckDuckGo (basic implementation)."""
        try:
            # This is a simplified implementation
            # In production, you might want to use a proper DuckDuckGo API or library
            search_url = f"https://duckduckgo.com/html/?q={query}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Parse DuckDuckGo results (this is a basic implementation)
            result_elements = soup.find_all('div', class_='result')[:num_results]
            
            for element in result_elements:
                try:
                    title_elem = element.find('a', class_='result__a')
                    snippet_elem = element.find('a', class_='result__snippet')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                        url = title_elem.get('href', '')
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                        
                        search_result = {
                            "title": title,
                            "url": url,
                            "content": snippet,
                            "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                            "source": "duckduckgo",
                            "score": 0.5
                        }
                        results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing DuckDuckGo result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            error_msg = f"Error in _search_duckduckgo: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    async def async_search(self, query, num_results=None):
        """Asynchronous web search."""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.search, query, num_results)
        except Exception as e:
            error_msg = f"Error in async_search: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def get_page_content(self, url):
        """Extract text content from a web page."""
        try:
            if not url or not url.strip():
                return ""
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return ""
            
            headers = {"User-Agent": self.user_agent}
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            logger.info(f"Extracted {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            error_msg = f"Error in get_page_content for {url}: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def search_and_extract(self, query, num_results=None, extract_content=True):
        """Search and optionally extract full content from results."""
        try:
            results = self.search(query, num_results)
            
            if not extract_content:
                return results
            
            # Extract full content for each result
            enhanced_results = []
            for result in results:
                try:
                    if result.get("url"):
                        full_content = self.get_page_content(result["url"])
                        result["full_content"] = full_content
                    enhanced_results.append(result)
                except Exception as e:
                    logger.warning(f"Failed to extract content from {result.get('url', 'unknown')}: {e}")
                    enhanced_results.append(result)
            
            return enhanced_results
            
        except Exception as e:
            error_msg = f"Error in search_and_extract: {str(e)}"
            logger.error(error_msg)
            print(error_msg)
            raise Exception(error_msg)
    
    def validate_url(self, url):
        """Validate if a URL is accessible."""
        try:
            if not url or not url.strip():
                return False
            
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
            
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {e}")
            return False
    
    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            if hasattr(self, 'session'):
                self.session.close()
        except Exception:
            pass
