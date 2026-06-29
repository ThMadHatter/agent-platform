import asyncio
import logging
import random
from typing import Any, Callable, TypeVar, Optional

T = TypeVar("T")
logger = logging.getLogger(__name__)

class RetryEngine:
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def execute_with_retry(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        retries = 0
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Max retries ({self.max_retries}) reached for {func.__name__}. Error: {e}")
                    raise

                delay = min(self.max_delay, self.base_delay * (2 ** (retries - 1)) + random.uniform(0, 0.1))
                logger.warning(f"Retry {retries}/{self.max_retries} for {func.__name__} after {delay:.2f}s. Error: {e}")
                await asyncio.sleep(delay)
