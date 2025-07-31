#!/usr/bin/env python3
from typing import Any, Optional
from collections import OrderedDict

class LRUCache:
    """
    A simple Least Recently Used cache with a fixed item limit.
    Methods:
      - has(key): return True if key in cache (and mark it as used)
      - get(key): return value if found (mark as used), otherwise return None
      - set(key, value): insert/update; evict least-recently-used if at capacity
    """

    def __init__(self, item_limit: int):
        if item_limit <= 0:
            raise ValueError("item_limit must be positive")
        self.item_limit = item_limit
        self._cache: OrderedDict[str, Any] = OrderedDict()

    def has(self, key: str) -> bool:
        if key in self._cache:
            self._cache.move_to_end(key)
            return True
        return False

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def set(self, key: str, value: Any):
        if key in self._cache:
            self._cache.move_to_end(key)
            self._cache[key] = value
        else:
            if len(self._cache) >= self.item_limit:
                self._cache.popitem(last=False)
            self._cache[key] = value
