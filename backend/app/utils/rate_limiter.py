import asyncio
import time


class AsyncRateLimiter:
    """Simple async rate limiter that enforces a minimum interval between calls.

    Usage:
        limiter = AsyncRateLimiter(calls_per_second=2.0)

        async def fetch_data():
            async with limiter:
                # this block will wait if called too quickly
                response = await some_api_call()
    """

    def __init__(self, calls_per_second: float = 1.0) -> None:
        if calls_per_second <= 0:
            raise ValueError("calls_per_second must be positive")
        self._min_interval: float = 1.0 / calls_per_second
        self._last_call: float = 0.0
        self._lock: asyncio.Lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until enough time has passed since the last call."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                await asyncio.sleep(wait_time)
            self._last_call = time.monotonic()

    async def __aenter__(self) -> "AsyncRateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        pass
