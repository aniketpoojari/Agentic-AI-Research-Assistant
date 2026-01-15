"""
Caching utilities for the Research Assistant.

Provides in-memory caching with TTL for:
- LLM responses
- Web search results
- Page content extraction

Reduces API costs and improves response times for repeated queries.
"""

import hashlib
import time
from typing import Any, Optional, Dict
from functools import wraps
from threading import Lock
from dataclasses import dataclass
from logger.logging import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item with expiration."""
    value: Any
    created_at: float
    ttl: int  # Time to live in seconds
    hits: int = 0

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl


class ResponseCache:
    """
    Thread-safe in-memory cache with TTL support.

    Features:
    - Configurable TTL per entry
    - LRU-style eviction when max size reached
    - Thread-safe operations
    - Hit/miss statistics
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache.

        Args:
            max_size: Maximum number of entries (default 1000)
            default_ttl: Default time-to-live in seconds (default 1 hour)
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0}

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_str = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired:
                    entry.hits += 1
                    self._stats["hits"] += 1
                    logger.debug(f"Cache hit for key: {key[:16]}...")
                    return entry.value
                else:
                    # Remove expired entry
                    del self._cache[key]

            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional custom TTL."""
        with self._lock:
            # Evict oldest entries if at max size
            if len(self._cache) >= self._max_size:
                self._evict_oldest()

            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl or self._default_ttl
            )
            logger.debug(f"Cached value for key: {key[:16]}...")

    def _evict_oldest(self) -> None:
        """Remove oldest entries (LRU-style)."""
        if not self._cache:
            return

        # Sort by created_at and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k].created_at
        )

        num_to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:num_to_remove]:
            del self._cache[key]

        logger.debug(f"Evicted {num_to_remove} cache entries")

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total if total > 0 else 0

            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": f"{hit_rate:.2%}",
                "default_ttl": self._default_ttl
            }


# Global cache instances
llm_cache = ResponseCache(max_size=500, default_ttl=1800)  # 30 min for LLM
search_cache = ResponseCache(max_size=200, default_ttl=3600)  # 1 hour for search
content_cache = ResponseCache(max_size=100, default_ttl=7200)  # 2 hours for content


def cached_llm_call(ttl: Optional[int] = None):
    """
    Decorator for caching LLM responses.

    Usage:
        @cached_llm_call(ttl=1800)
        def generate_summary(text: str) -> str:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"llm:{func.__name__}:{llm_cache._generate_key(*args, **kwargs)}"

            # Check cache
            cached_result = llm_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"LLM cache hit for {func.__name__}")
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            llm_cache.set(cache_key, result, ttl)
            logger.info(f"LLM result cached for {func.__name__}")

            return result
        return wrapper
    return decorator


def cached_search(ttl: Optional[int] = None):
    """
    Decorator for caching web search results.

    Usage:
        @cached_search(ttl=3600)
        def search_web(query: str, max_results: int) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"search:{func.__name__}:{search_cache._generate_key(*args, **kwargs)}"

            cached_result = search_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Search cache hit for query")
                return cached_result

            result = func(*args, **kwargs)
            search_cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def cached_content(ttl: Optional[int] = None):
    """
    Decorator for caching page content extraction.

    Usage:
        @cached_content(ttl=7200)
        def get_page_content(url: str) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"content:{func.__name__}:{content_cache._generate_key(*args, **kwargs)}"

            cached_result = content_cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Content cache hit for URL")
                return cached_result

            result = func(*args, **kwargs)
            content_cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


def get_all_cache_stats() -> Dict[str, Any]:
    """Get statistics for all cache instances."""
    return {
        "llm_cache": llm_cache.get_stats(),
        "search_cache": search_cache.get_stats(),
        "content_cache": content_cache.get_stats()
    }


def clear_all_caches() -> None:
    """Clear all cache instances."""
    llm_cache.clear()
    search_cache.clear()
    content_cache.clear()
    logger.info("All caches cleared")
