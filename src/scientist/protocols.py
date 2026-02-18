"""Core protocols for the Scientist library.

Defines the fundamental abstractions:
- Comparator[T]: Protocol for comparing observation values
- Publisher: Protocol for publishing experiment results
"""

from __future__ import annotations

from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Comparator(Protocol[T]):  # type: ignore[misc]
    """Protocol for comparing two observation values."""

    def compare(self, control: T, candidate: T) -> bool:
        """Compare control and candidate values.

        Returns True if values are equivalent.
        """
        ...


@runtime_checkable
class Publisher(Protocol):
    """Protocol for publishing experiment results."""

    def publish(self, result: object) -> None:
        """Publish an experiment result."""
        ...
