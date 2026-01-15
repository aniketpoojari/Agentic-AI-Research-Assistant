"""Web search utility for the Dynamic Research Assistant."""

import requests
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from utils.config_loader import ConfigLoader
from utils.cache import search_cache, content_cache
from logger.logging import get_logger

logger = get_logger(__name__)


class WebSearch:
    """Handles web search operations using multiple search providers."""

    def __init__(self):
        try:
            self.config = ConfigLoader()
            self.timeout = self.config.get("search.timeout", 30)
            self.user_agent = self.config.get("search.user_agent", "Research Assistant Bot 1.0")
            self.max_results = int(self.config.get_env("SEARCH_MAX_RESULTS", 5))
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.user_agent})
            logger.info("WebSearch Utility Class Initialized")

        except Exception as e:
            error_msg = f"Error in WebSearch Utility Class Initialization -> {str(e)}"
            raise Exception(error_msg)
        
    def search(self, query, num_results=None):
        """Search the web for the given query."""

        try:
            if not query or not query.strip():
                return []

            num_results = num_results or self.max_results

            # Check cache first
            cache_key = f"search:{query}:{num_results}"
            cached_results = search_cache.get(cache_key)
            if cached_results is not None:
                logger.info(f"Returning cached search results for: {query[:50]}...")
                return cached_results

            logger.info(f"Starting web search for query: {query[:100]}...")
            
            # Try Tavily first if API key is available
            tavily_key = self.config.get_api_key("tavily")
            if tavily_key:
                try:
                    results = self._search_tavily(query, num_results)
                    if results:
                        logger.info(f"Tavily search returned {len(results)} results")
                        search_cache.set(cache_key, results, ttl=3600)  # Cache for 1 hour
                        return results
                except Exception as e:
                    logger.warning(f"Tavily search failed: {e}")

            # Try DuckDuckGo as fallback
            try:
                results = self._search_duckduckgo(query, num_results)
                if results:
                    logger.info(f"DuckDuckGo search returned {len(results)} results")
                    search_cache.set(cache_key, results, ttl=3600)  # Cache for 1 hour
                    return results
            except Exception as e:
                logger.warning(f"DuckDuckGo search failed: {e}")

            # If all searches fail, return empty list
            logger.warning("All search providers failed")
            return []
            
        except Exception as e:
            error_msg = f"Error in search utility function -> {str(e)}"
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
                    content = result.get("content", "")
                    search_result = {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": content,
                        "snippet": content[:200] + "..." if len(content) > 200 else content,
                        "source": "tavily",
                        "score": result.get("score", 0.0)
                    }
                    results.append(search_result)
                except Exception as e:
                    logger.warning(f"Error processing Tavily result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            error_msg = f"Error in _search_tavily utility function -> {str(e)}"
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
            error_msg = f"Error in _search_duckduckgo utility function -> {str(e)}"
            raise Exception(error_msg)
    
    async def async_search(self, query, num_results=None):
        """Asynchronous web search."""
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self.search, query, num_results)
        
        except Exception as e:
            error_msg = f"Error in async_search utility function -> {str(e)}"
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

            # Check cache first
            cache_key = f"content:{url}"
            cached_content = content_cache.get(cache_key)
            if cached_content is not None:
                logger.info(f"Returning cached content for: {url[:50]}...")
                return cached_content

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

            # Cache the content (2 hours TTL)
            content_cache.set(cache_key, text, ttl=7200)

            logger.info(f"Extracted {len(text)} characters from {url}")
            return text
            
        except Exception as e:
            error_msg = f"Error in get_page_content utility function for {url} -> {str(e)}"
            raise Exception(error_msg)
    
    
    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            if hasattr(self, 'session'):
                self.session.close()
        except Exception:
            pass
