"""Fixed-window rate limiter: Redis when configured (shared across API replicas), in-process
memory otherwise (single-instance development)."""

from __future__ import annotations

import threading
import time
from functools import lru_cache

from app.config import get_settings
from app.errors import ApiError


class _Memory:
    def __init__(self):
        self._lock = threading.Lock()
        self._counts: dict[str, tuple[int, int]] = {}

    def hit(self, key: str, window: int) -> int:
        now_window = int(time.time()) // window
        with self._lock:
            w, c = self._counts.get(key, (now_window, 0))
            if w != now_window:
                w, c = now_window, 0
            c += 1
            self._counts[key] = (w, c)
            if len(self._counts) > 50_000:
                self._counts = {k: v for k, v in self._counts.items() if v[0] == now_window}
            return c

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


class _Redis:
    def __init__(self, url: str):
        import redis

        self.r = redis.Redis.from_url(url)

    def hit(self, key: str, window: int) -> int:
        k = f"rl:{key}:{int(time.time()) // window}"
        pipe = self.r.pipeline()
        pipe.incr(k)
        pipe.expire(k, window + 1)
        return int(pipe.execute()[0])

    def reset(self) -> None:  # pragma: no cover
        pass


@lru_cache
def _backend():
    url = get_settings().redis_url
    if url:
        try:
            b = _Redis(url)
            b.r.ping()
            return b
        except Exception:
            pass
    return _Memory()


def check_rate(key: str, limit: int, window_s: int = 60) -> None:
    if limit <= 0:
        return
    if _backend().hit(key, window_s) > limit:
        raise ApiError(429, "rate_limited", "Too many requests. Please retry later.", {"retry_after_s": window_s})


def reset_rate_limits() -> None:
    _backend().reset()
