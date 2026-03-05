"""
In-memory TTL cache for compute_all results.
─────────────────────────────────────────────
Keeps slider interactions snappy by avoiding redundant pipeline runs.
Thread-safe enough for a single-process uvicorn (fine for hackathon).
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, Optional


class TTLCache:
    """Simple dict-based cache with per-entry TTL."""

    def __init__(self, default_ttl: float = 2.0):
        self._store: Dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def make_key(region_id: str, overrides: Optional[Dict[str, float]] = None) -> str:
        """Produce a stable cache key from region + overrides."""
        if not overrides:
            return region_id
        # Sort keys for stability, round values to avoid float jitter
        parts = sorted(
            f"{k}={round(v, 2)}" for k, v in overrides.items()
        )
        suffix = hashlib.md5("|".join(parts).encode()).hexdigest()[:10]
        return f"{region_id}:{suffix}"

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if (time.time() - ts) > self._default_ttl:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        self._store[key] = (time.time(), value)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)


# Singleton instances
compute_cache = TTLCache(default_ttl=2.0)    # /simulate results
narrative_cache = TTLCache(default_ttl=30.0)  # narrative text (Bedrock calls are expensive)
