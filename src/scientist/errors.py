"""Exceptions raised by the Scientist library."""

from __future__ import annotations

from typing import Generic, TypeVar

from .result import Result

T = TypeVar("T")


class ExperimentMismatchError(Generic[T], Exception):
    """Raised when an experiment has an unexpected mismatch.

    Only raised when raise_on_mismatches is enabled.
    """

    def __init__(self, result: Result[T]) -> None:
        self.result = result
        super().__init__(
            f"Experiment '{result.experiment_name}' mismatched: "
            f"control={result.control.value}, "
            f"candidate={result.candidate.value}"
        )
