"""
Simple time-based cache for external API calls.
"""
import time
from typing import Any, Callable, Optional

_cache = {}

def cached_call(
    key: str,
    func: Callable,
    ttl_seconds: int = 60,
    *args,
    **kwargs
) -> Any:
    """
    Call func(*args, **kwargs) and cache the result for ttl_seconds.
    If called again within ttl_seconds, return cached result.
    
    Args:
        key: Unique cache key
        func: Function to call
        ttl_seconds: Time to live in seconds
        *args, **kwargs: Arguments to pass to func
    
    Returns:
        Result from func (cached or fresh)
    """
    now = time.time()
    
    if key in _cache:
        timestamp, value = _cache[key]
        if now - timestamp < ttl_seconds:
            # Cache hit
            return value
    
    # Cache miss or expired - call function
    result = func(*args, **kwargs)
    _cache[key] = (now, result)
    return result


def cache_get(key: str) -> Any:
    """
    Get value from cache without expiry check.
    Used by background cache system.
    
    Args:
        key: Cache key to retrieve
    
    Returns:
        Cached value or None if not found
    """
    if key in _cache:
        _, value = _cache[key]
        return value
    return None


def cache_set(key: str, value: Any, ttl: int = None):
    """
    Set value in cache with current timestamp.
    Used by background cache system.
    
    Args:
        key: Cache key
        value: Value to cache
        ttl: Time to live (optional, for compatibility)
    """
    now = time.time()
    _cache[key] = (now, value)


def clear_cache(key: Optional[str] = None):
    """
    Clear cache for specific key or all keys.
    """
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()
