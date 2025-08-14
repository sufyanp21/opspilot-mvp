from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import Request, Response


class TokenBucketLimiter:
    def __init__(self, capacity_per_minute: int) -> None:
        self.capacity = capacity_per_minute
        self.window_seconds = 60
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self.requests[key]
        # Evict old timestamps
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) < self.capacity:
            bucket.append(now)
            return True
        return False


def rate_limit_middleware_factory(capacity_per_minute: int, header_prefix: str = "X-RateLimit"):
    limiter = TokenBucketLimiter(capacity_per_minute)

    async def middleware(request: Request, call_next):
        client_ip = request.headers.get("x-forwarded-for") or request.client.host  # type: ignore[union-attr]
        key = f"{client_ip}:{request.url.path}"
        allowed = limiter.allow(key)
        if not allowed:
            return Response(status_code=429, content="Too Many Requests")
        response = await call_next(request)
        return response

    return middleware

def path_scoped_rate_limit(paths: set[str], capacity_per_minute: int):
    limiter = TokenBucketLimiter(capacity_per_minute)

    async def middleware(request: Request, call_next):
        path = request.url.path
        if any(path.startswith(p) for p in paths):
            client_ip = request.headers.get("x-forwarded-for") or request.client.host  # type: ignore[union-attr]
            key = f"{client_ip}:{path}"
            if not limiter.allow(key):
                return Response(status_code=429, content="Too Many Requests")
        return await call_next(request)

    return middleware

