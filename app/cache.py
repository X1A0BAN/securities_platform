from __future__ import annotations

import time
from dataclasses import dataclass
from functools import lru_cache
from threading import RLock
from typing import Any

from app.config import get_settings


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int = 300, maxsize: int = 512, enabled: bool = True) -> None:
        self._ttl_seconds = ttl_seconds
        self._maxsize = maxsize
        self._enabled = enabled
        self._store: dict[str, CacheEntry] = {}
        self._lock = RLock()

    def get(self, key: str) -> Any | None:
        if not self._enabled:
            return None

        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            if entry.expires_at <= time.time():
                self._store.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: Any) -> Any:
        if not self._enabled:
            return value

        with self._lock:
            self._prune_expired_locked()
            if len(self._store) >= self._maxsize:
                oldest_key = next(iter(self._store))
                self._store.pop(oldest_key, None)
            self._store[key] = CacheEntry(
                value=value,
                expires_at=time.time() + self._ttl_seconds,
            )
        return value

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _prune_expired_locked(self) -> None:
        now = time.time()
        expired_keys = [key for key, entry in self._store.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._store.pop(key, None)


@lru_cache(maxsize=1)
def get_query_cache() -> TTLCache:
    settings = get_settings()
    return TTLCache(
        ttl_seconds=settings.query_cache_ttl_seconds,
        maxsize=settings.query_cache_maxsize,
        enabled=settings.query_cache_enabled,
    )
