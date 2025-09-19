"""
Timeout utilities for preventing hanging operations
"""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Union
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TimeoutError(Exception):
    """Custom timeout exception"""
    pass


def with_timeout(timeout_seconds: float, fallback_value: Any = None,
                 raise_on_timeout: bool = True):
    """
    Decorator to add timeout to async functions

    Args:
        timeout_seconds: Maximum time to wait
        fallback_value: Value to return if timeout occurs (only if raise_on_timeout=False)
        raise_on_timeout: Whether to raise exception or return fallback on timeout
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                func_name = getattr(func, '__name__', 'unknown')
                logger.warning(f"Function {func_name} timed out after {timeout_seconds}s")

                if raise_on_timeout:
                    raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
                else:
                    logger.info(f"Returning fallback value for {func_name}")
                    return fallback_value
        return wrapper
    return decorator


async def run_with_timeout(
    coro,
    timeout_seconds: float,
    fallback_value: Any = None,
    raise_on_timeout: bool = True
) -> Any:
    """
    Run coroutine with timeout

    Args:
        coro: Coroutine to run
        timeout_seconds: Maximum time to wait
        fallback_value: Value to return if timeout occurs
        raise_on_timeout: Whether to raise exception or return fallback on timeout

    Returns:
        Result of coroutine or fallback value
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Coroutine timed out after {timeout_seconds}s")

        if raise_on_timeout:
            raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        else:
            return fallback_value


@asynccontextmanager
async def timeout_context(timeout_seconds: float, operation_name: str = "operation"):
    """
    Context manager for timeout operations

    Args:
        timeout_seconds: Maximum time to wait
        operation_name: Name for logging purposes
    """
    start_time = asyncio.get_event_loop().time()

    try:
        logger.debug(f"Starting {operation_name} with {timeout_seconds}s timeout")

        async with asyncio.timeout(timeout_seconds):
            yield

        elapsed = asyncio.get_event_loop().time() - start_time
        logger.debug(f"{operation_name} completed in {elapsed:.2f}s")

    except asyncio.TimeoutError:
        elapsed = asyncio.get_event_loop().time() - start_time
        logger.warning(f"{operation_name} timed out after {elapsed:.2f}s")
        raise TimeoutError(f"{operation_name} timed out after {timeout_seconds} seconds")


class CircuitBreaker:
    """
    Simple circuit breaker implementation for fault tolerance
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def is_circuit_open(self) -> bool:
        """Check if circuit is open (failing)"""
        if self.state == "OPEN":
            # Check if we should try again
            if (asyncio.get_event_loop().time() - self.last_failure_time) > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker moving to HALF_OPEN state")
                return False
            return True
        return False

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED state")

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()

        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")


def with_circuit_breaker(circuit_breaker: CircuitBreaker, fallback_value: Any = None):
    """
    Decorator to add circuit breaker protection to async functions
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if circuit_breaker.is_circuit_open():
                func_name = getattr(func, '__name__', 'unknown')
                logger.warning(f"Circuit breaker is OPEN for {func_name}, returning fallback")
                return fallback_value

            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise e

        return wrapper
    return decorator


# Global circuit breakers for different services
rag_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
llm_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
chromadb_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=45.0)