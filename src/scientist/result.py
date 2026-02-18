"""Result of an experiment comparing control and candidate observations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .observation import Observation

T = TypeVar("T")


@dataclass(frozen=True)
class Result(Generic[T]):
    """Aggregates control and candidate observations.

    Attributes:
        experiment_name: Name of the experiment
        control: Observation from the control behavior
        candidate: Observation from the candidate behavior
        matched: Whether control and candidate values matched
        ignored: Whether a mismatch was ignored by a filter
    """

    experiment_name: str
    control: Observation[T]
    candidate: Observation[T]
    matched: bool
    ignored: bool

    @property
    def mismatched(self) -> bool:
        return not self.matched

    @property
    def ignored_mismatch(self) -> bool:
        return self.mismatched and self.ignored

    @property
    def unexpected_mismatch(self) -> bool:
        return self.mismatched and not self.ignored
