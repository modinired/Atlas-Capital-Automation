"""
In‑memory rate limiting middleware for the Terry Delmonaco Presents: AI service.

This module implements a simple sliding‑window rate limiter.  When the
`RATE_LIMIT_PER_MIN` environment variable is set to a positive integer, each
incoming request is counted against a per‑identifier window lasting one
minute.  The identifier is derived from the API key if present or the client
IP address.  If the number of requests exceeds the configured limit within the
window, the request is rejected with a 429 (Too Many Requests) error.

Note: This implementation stores counters in process memory and does not
persist across process restarts or share state between workers.  For
distributed rate limiting, use a shared store like Redis.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

# Parse the rate limit from the environment.  A value of 0 disables rate limiting.
try:
    _rate_limit = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))
except ValueError:
    _rate_limit = 0


class _SlidingWindowRateLimiter:
    """Internal helper implementing a sliding window rate limiter."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        # Maps an identifier (API key or IP) to a list of request timestamps
        self._requests: Dict[str, List[datetime]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """Return True if the request should be allowed for this identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=1)
        timestamps = self._requests.get(identifier, [])
        # Remove timestamps outside the window
        timestamps = [ts for ts in timestamps if ts > window_start]
        if len(timestamps) >= self.limit:
            # Store the pruned list before returning
            self._requests[identifier] = timestamps
            return False
        timestamps.append(now)
        self._requests[identifier] = timestamps
        return True


_limiter = _SlidingWindowRateLimiter(_rate_limit) if _rate_limit > 0 else None


async def enforce_rate_limit(request: Request) -> None:
    """Check the rate limit for the given request and raise HTTPException if exceeded."""
    if _limiter is None:
        return
    # Use API key if provided, otherwise use client IP
    api_key = request.headers.get("X-API-Key")
    identifier = api_key if api_key else (request.client.host if request.client else "anonymous")
    if not _limiter.is_allowed(identifier):
        raise HTTPException(status_code=HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")