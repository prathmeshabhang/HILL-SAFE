"""
api_key_manager.py — Multi-API Key Management, Pool Rotation & Cooldown Handler
==============================================================================
Provides high-availability API key pooling for FLOODY SHIELD:
  1. Multi-Key Pooling: Load multiple comma-separated keys or numbered keys (KEY_1, KEY_2).
  2. Round-Robin Load Balancing: Distributes requests evenly across available credentials.
  3. Automatic 429 Rate-Limit Fallback: When a provider triggers HTTP 429, marks that key
     in a cooldown state (e.g., 60s) and automatically rolls over to the next healthy key.
  4. Redaction & Zero-Leak Safety: All logging masks credentials (e.g., sk-***4f2a).
  5. Graceful Local Degradation: If all keys are exhausted or missing, flags fallback mode.
"""

from __future__ import annotations

import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def mask_key(key: str) -> str:
    """Masks an API key for safe logging (e.g., 'ab***1234')."""
    if not key or len(key) < 6:
        return "***"
    return f"{key[:3]}***{key[-4:]}"


@dataclass
class KeyRecord:
    key_value: str
    failure_count: int = 0
    cooldown_until: float = 0.0
    total_calls: int = 0

    @property
    def is_available(self) -> bool:
        return time.time() >= self.cooldown_until


class MultiAPIKeyPool:
    """Manages an individual service's pool of API keys (e.g., 'copernicus', 'nasa_earthdata')."""

    def __init__(self, service_name: str, keys: Optional[List[str]] = None, cooldown_seconds: float = 60.0):
        self.service_name = service_name
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._records: List[KeyRecord] = []
        self._index: int = 0

        if keys:
            for k in keys:
                self.add_key(k)

    def add_key(self, key: str) -> None:
        key_clean = key.strip()
        if key_clean and not any(r.key_value == key_clean for r in self._records):
            self._records.append(KeyRecord(key_value=key_clean))

    @property
    def total_keys(self) -> int:
        return len(self._records)

    @property
    def available_keys_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._records if r.is_available)

    def get_key(self) -> Optional[str]:
        """
        Returns the next available API key using round-robin rotation.
        Skips keys currently in rate-limit cooldown.
        """
        with self._lock:
            if not self._records:
                return None

            n = len(self._records)
            for _ in range(n):
                idx = self._index % n
                self._index += 1
                record = self._records[idx]
                if record.is_available:
                    record.total_calls += 1
                    return record.key_value

            # If all are in cooldown, pick the one with earliest cooldown expiry
            soonest = min(self._records, key=lambda r: r.cooldown_until)
            soonest.total_calls += 1
            return soonest.key_value

    def report_rate_limit(self, key: str) -> None:
        """
        Reports that a key hit HTTP 429 / rate limit.
        Puts it into cooldown so subsequent requests switch to other keys.
        """
        with self._lock:
            for record in self._records:
                if record.key_value == key:
                    record.failure_count += 1
                    record.cooldown_until = time.time() + self.cooldown_seconds
                    break

    def get_status_summary(self) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            return {
                "service": self.service_name,
                "total_keys": len(self._records),
                "active_healthy_keys": sum(1 for r in self._records if r.cooldown_until <= now),
                "keys_in_cooldown": sum(1 for r in self._records if r.cooldown_until > now),
                "records": [
                    {
                        "key_masked": mask_key(r.key_value),
                        "total_calls": r.total_calls,
                        "failure_count": r.failure_count,
                        "is_cooldown": r.cooldown_until > now,
                        "cooldown_remaining_sec": max(0, int(r.cooldown_until - now)),
                    }
                    for r in self._records
                ],
            }


class APIKeyManager:
    """
    Central API Key Manager for FLOODY SHIELD.
    Loads environment variables from .env and system env, building pools for:
      - COPERNICUS_API_KEYS (Sentinel-1 / Sentinel-2)
      - EARTHDATA_TOKENS (NASA GPM, SMAP, DEM)
      - GEMINI_API_KEYS (AI Logic & Early Warning Reasoning)
      - OPENWEATHER_API_KEYS
    """

    _instance: Optional[APIKeyManager] = None
    _singleton_lock = threading.Lock()

    def __init__(self, env_path: Optional[Path] = None):
        self.pools: Dict[str, MultiAPIKeyPool] = {}
        self._load_from_env(env_path)

    @classmethod
    def get_instance(cls) -> APIKeyManager:
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _load_from_env(self, env_path: Optional[Path] = None) -> None:
        target_path = env_path or (Path.cwd() / ".env")
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())

        # Register standard pools
        self._register_pool_from_env("copernicus", ["COPERNICUS_API_KEYS", "COPERNICUS_API_KEY", "CDSE_API_KEY"])
        self._register_pool_from_env("earthdata", ["EARTHDATA_TOKENS", "EARTHDATA_TOKEN", "NASA_EARTHDATA_KEY"])
        self._register_pool_from_env("gemini", ["GEMINI_API_KEYS", "GEMINI_API_KEY", "GOOGLE_API_KEY"])
        self._register_pool_from_env("openweather", ["OPENWEATHER_API_KEYS", "OPENWEATHER_API_KEY"])

    def _register_pool_from_env(self, pool_name: str, var_names: List[str]) -> None:
        pool = MultiAPIKeyPool(service_name=pool_name)

        for var in var_names:
            val = os.environ.get(var, "").strip()
            if val:
                # Support comma-separated or semicolon-separated keys
                parts = [p.strip() for p in re.split(r"[,;]", val) if p.strip()]
                for p in parts:
                    pool.add_key(p)

        # Also support numbered env vars: e.g. GEMINI_API_KEY_1, GEMINI_API_KEY_2
        prefix = var_names[0].rstrip("S") + "_"
        for k, v in os.environ.items():
            if k.startswith(prefix) and v.strip():
                pool.add_key(v.strip())

        self.pools[pool_name] = pool

    def get_key(self, service: str) -> Optional[str]:
        pool = self.pools.get(service)
        if pool:
            return pool.get_key()
        return None

    def report_rate_limit(self, service: str, key: str) -> None:
        pool = self.pools.get(service)
        if pool:
            pool.report_rate_limit(key)

    def get_pool_status(self) -> Dict[str, Any]:
        return {name: pool.get_status_summary() for name, pool in self.pools.items()}

    def get_status_summary(self) -> Dict[str, Any]:
        return self.get_pool_status()


def get_global_key_pool_manager() -> APIKeyManager:
    return APIKeyManager.get_instance()
