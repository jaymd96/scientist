"""Observation of a behavior's execution.

Captures the result of running a behavior including its value,
exceptions, and execution timing (wall-clock and CPU).
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Observation(Generic[T]):
    """Captures the execution result of a behavior.

    Attributes:
        name: Identifier (e.g., "control", "candidate")
        value: Returned value, or None if exception raised
        exception: Exception raised, or None if succeeded
        duration_seconds: Wall-clock execution time
        cpu_time_seconds: CPU execution time
    """

    name: str
    value: T | None
    exception: BaseException | None
    duration_seconds: float
    cpu_time_seconds: float

    @property
    def raised(self) -> bool:
        """Whether the behavior raised an exception."""
        return self.exception is not None

    @property
    def value_or_raise(self) -> T:
        """Get the value, or re-raise the exception."""
        if self.exception is not None:
            raise self.exception
        return self.value  # type: ignore

    def equivalent_to(self, other: Observation[T]) -> bool:
        """Check if this observation is equivalent to another.

        Equivalent if both succeeded with equal values, or both raised
        the same exception type.
        """
        if self.raised and other.raised:
            return type(self.exception) == type(other.exception)
        if not self.raised and not other.raised:
            return self.value == other.value
        return False


def observe(name: str, behavior: Callable[[], T]) -> Observation[T]:
    """Execute a behavior and capture its observation.

    Measures both wall-clock time and CPU time.
    """
    start_time = time.perf_counter()
    start_cpu = time.process_time()

    try:
        value = behavior()
        return Observation(
            name=name,
            value=value,
            exception=None,
            duration_seconds=time.perf_counter() - start_time,
            cpu_time_seconds=time.process_time() - start_cpu,
        )
    except BaseException as e:
        return Observation(
            name=name,
            value=None,
            exception=e,
            duration_seconds=time.perf_counter() - start_time,
            cpu_time_seconds=time.process_time() - start_cpu,
        )


async def async_observe(
    name: str, behavior: Callable[[], Awaitable[T]]
) -> Observation[T]:
    """Async variant of observe() for async code paths."""
    start_time = time.perf_counter()
    start_cpu = time.process_time()

    try:
        value = await behavior()
        return Observation(
            name=name,
            value=value,
            exception=None,
            duration_seconds=time.perf_counter() - start_time,
            cpu_time_seconds=time.process_time() - start_cpu,
        )
    except BaseException as e:
        return Observation(
            name=name,
            value=None,
            exception=e,
            duration_seconds=time.perf_counter() - start_time,
            cpu_time_seconds=time.process_time() - start_cpu,
        )
