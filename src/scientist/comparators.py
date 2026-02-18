"""Built-in comparators for experiment value comparison."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from .protocols import Comparator

T = TypeVar("T")


class DefaultComparator(Generic[T]):
    """Compares using the == operator."""

    def compare(self, control: T, candidate: T) -> bool:
        return control == candidate


class CallableComparator(Generic[T]):
    """Wraps a comparison function as a Comparator."""

    def __init__(self, fn: Callable[[T, T], bool]) -> None:
        self.fn = fn

    def compare(self, control: T, candidate: T) -> bool:
        return self.fn(control, candidate)


def comparator_from_func(fn: Callable[[T, T], bool]) -> Comparator[T]:
    """Create a Comparator from a comparison function."""
    return CallableComparator(fn)


def percent_difference_comparator(threshold: float) -> Comparator[float]:
    """Comparator for numeric values within a percentage threshold.

    Args:
        threshold: Maximum acceptable percentage difference (0.0-1.0)
    """

    def compare(control: float, candidate: float) -> bool:
        if control == 0 and candidate == 0:
            return True
        if control == 0 or candidate == 0:
            return False
        return abs(control - candidate) / abs(control) <= threshold

    return CallableComparator(compare)


def set_comparator() -> Comparator[set[object]]:
    """Comparator for set equality."""

    def compare(control: set[object], candidate: set[object]) -> bool:
        return control == candidate

    return CallableComparator(compare)
