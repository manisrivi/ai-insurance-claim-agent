# rate_limit.py: a small in-memory rate limiter (no extra package)
# Each "bucket" allows N requests per IP in a time window. Too many -> 429.
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self.hits: dict[str, deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            # forget hits older than the window
            while q and now - q[0] > self.window:
                q.popleft()
            if len(q) >= self.max_requests:
                return False
            q.append(now)
            # housekeeping: drop IPs with no recent hits (keeps memory small)
            if len(self.hits) > 10_000:
                for ip in [k for k, v in self.hits.items() if not v or now - v[-1] > self.window]:
                    del self.hits[ip]
            return True

    def reset(self) -> None:
        with self.lock:
            self.hits.clear()


def client_ip(request: Request) -> str:
    # Behind a proxy, run uvicorn with --proxy-headers so this is the real user IP
    return request.client.host if request.client else "unknown"


def limit(limiter: RateLimiter):
    # FastAPI dependency: use as dependencies=[Depends(limit(submit_limiter))]
    def check(request: Request) -> None:
        if not limiter.allow(client_ip(request)):
            raise HTTPException(status_code=429, detail="Too many requests. Wait a minute and try again.")
    return check
