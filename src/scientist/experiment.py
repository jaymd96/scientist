"""Experiment: the core Scientist abstraction.

Runs old (control) and new (candidate) code in parallel, compares
results, publishes findings. Always returns the control's result.
"""

from __future__ import annotations

import random
from collections.abc import Awaitable, Callable, Collection
from typing import Generic, TypeVar

from .comparators import DefaultComparator
from .context import get_default_enabled, get_default_publisher
from .errors import ExperimentMismatchError
from .observation import Observation, async_observe, observe
from .protocols import Comparator, Publisher
from .publishers import NoopPublisher
from .result import Result

T = TypeVar("T")


class Experiment(Generic[T]):
    """Experiment for safe refactoring through controlled experiments.

    Flow:
    1. Check if enabled
    2. Check run_if gate
    3. Run before_run hooks
    4. Execute control and candidate in random order
    5. Compare observations
    6. Apply ignore filters
    7. Publish result
    8. Return control value
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._control: Callable[[], T] | None = None
        self._candidate: Callable[[], T] | None = None
        self._comparator: Comparator[T] = DefaultComparator()
        self._publisher: Publisher | None = None
        self._run_if_fn: Callable[[], bool] | None = None
        self._enabled: bool | None = None
        self._ignore_filters: list[Callable[[Result[T]], bool]] = []
        self._before_run_hooks: list[Callable[[], None]] = []
        self._clean_fn: Callable[[], None] | None = None
        self._raise_on_mismatches = False

    def use(self, control: Callable[[], T]) -> Experiment[T]:
        """Set the control (old) behavior."""
        self._control = control
        return self

    def try_(self, candidate: Callable[[], T]) -> Experiment[T]:
        """Set the candidate (new) behavior."""
        self._candidate = candidate
        return self

    def compare(self, comparator: Comparator[T]) -> Experiment[T]:
        """Set a custom comparator."""
        self._comparator = comparator
        return self

    def publish(self, publisher: Publisher) -> Experiment[T]:
        """Set the publisher for results."""
        self._publisher = publisher
        return self

    def run_if(self, fn: Callable[[], bool]) -> Experiment[T]:
        """Set a gate function. Candidate only runs if this returns True."""
        self._run_if_fn = fn
        return self

    def run_if_entity(
        self, entity_id: str, *, percent: float
    ) -> Experiment[T]:
        """Deterministic per-entity gate using the experiment name as salt.

        Same entity always gets the same True/False for this experiment.
        Different experiments bucket independently.
        """
        from .gates import entity_gate

        self._run_if_fn = entity_gate(entity_id, percent=percent, salt=self.name)
        return self

    def run_if_group(
        self, *, allowed: Collection[str], actual: Collection[str]
    ) -> Experiment[T]:
        """Group membership gate. Runs candidate if entity is in any allowed group."""
        from .gates import group_gate

        self._run_if_fn = group_gate(allowed=allowed, actual=actual)
        return self

    def run_if_percent(self, percent: float) -> Experiment[T]:
        """Random per-request gate. Each call has percent% chance of running."""
        from .gates import request_gate

        self._run_if_fn = request_gate(percent=percent)
        return self

    def enabled(self, value: bool) -> Experiment[T]:
        """Explicitly enable or disable the experiment."""
        self._enabled = value
        return self

    def ignore(self, fn: Callable[[Result[T]], bool]) -> Experiment[T]:
        """Add an ignore filter. If any returns True, mismatch is ignored."""
        self._ignore_filters.append(fn)
        return self

    def before_run(self, fn: Callable[[], None]) -> Experiment[T]:
        """Add a before_run hook."""
        self._before_run_hooks.append(fn)
        return self

    def clean(self, fn: Callable[[], None]) -> Experiment[T]:
        """Set cleanup function, called after experiment completes."""
        self._clean_fn = fn
        return self

    def raise_on_mismatches(self) -> Experiment[T]:
        """Enable raising ExperimentMismatchError on unexpected mismatches."""
        self._raise_on_mismatches = True
        return self

    def _is_enabled(self) -> bool:
        if self._enabled is not None:
            return self._enabled
        return get_default_enabled()

    def _get_publisher(self) -> Publisher:
        return self._publisher or get_default_publisher() or NoopPublisher()

    def _run_control_only(self) -> T:
        if self._control is None:
            raise ValueError("Control behavior not set")
        return self._control()

    def _build_result(
        self, control_obs: Observation[T], candidate_obs: Observation[T]
    ) -> Result[T]:
        matched = self._compare_observations(control_obs, candidate_obs)

        result = Result(
            experiment_name=self.name,
            control=control_obs,
            candidate=candidate_obs,
            matched=matched,
            ignored=False,
        )

        ignored = False
        for ignore_filter in self._ignore_filters:
            if ignore_filter(result):
                ignored = True
                break

        if ignored:
            result = Result(
                experiment_name=self.name,
                control=control_obs,
                candidate=candidate_obs,
                matched=matched,
                ignored=True,
            )

        return result

    def _finish(self, result: Result[T], control_obs: Observation[T]) -> T:
        publisher = self._get_publisher()
        try:
            publisher.publish(result)
        except Exception:
            pass

        if self._raise_on_mismatches and result.unexpected_mismatch:
            raise ExperimentMismatchError(result)

        if control_obs.raised:
            raise control_obs.exception  # type: ignore

        return control_obs.value  # type: ignore

    def run(self) -> T:
        """Run the experiment. Returns control value."""
        if not self._is_enabled():
            return self._run_control_only()

        if self._run_if_fn and not self._run_if_fn():
            return self._run_control_only()

        for hook in self._before_run_hooks:
            hook()

        if self._control is None:
            raise ValueError("Control behavior not set")
        if self._candidate is None:
            raise ValueError("Candidate behavior not set")

        try:
            if random.random() < 0.5:
                control_obs = observe("control", self._control)
                candidate_obs = observe("candidate", self._candidate)
            else:
                candidate_obs = observe("candidate", self._candidate)
                control_obs = observe("control", self._control)

            result = self._build_result(control_obs, candidate_obs)
            return self._finish(result, control_obs)

        finally:
            if self._clean_fn:
                try:
                    self._clean_fn()
                except Exception:
                    pass

    async def async_run(self) -> T:
        """Async variant of run() for async control/candidate behaviors."""
        if not self._is_enabled():
            if self._control is None:
                raise ValueError("Control behavior not set")
            return await self._control()  # type: ignore

        if self._run_if_fn and not self._run_if_fn():
            if self._control is None:
                raise ValueError("Control behavior not set")
            return await self._control()  # type: ignore

        for hook in self._before_run_hooks:
            hook()

        if self._control is None:
            raise ValueError("Control behavior not set")
        if self._candidate is None:
            raise ValueError("Candidate behavior not set")

        try:
            if random.random() < 0.5:
                control_obs = await async_observe("control", self._control)  # type: ignore
                candidate_obs = await async_observe("candidate", self._candidate)  # type: ignore
            else:
                candidate_obs = await async_observe("candidate", self._candidate)  # type: ignore
                control_obs = await async_observe("control", self._control)  # type: ignore

            result = self._build_result(control_obs, candidate_obs)
            return self._finish(result, control_obs)

        finally:
            if self._clean_fn:
                try:
                    self._clean_fn()
                except Exception:
                    pass

    def _compare_observations(
        self, control: Observation[T], candidate: Observation[T]
    ) -> bool:
        if control.raised and candidate.raised:
            return type(control.exception) == type(candidate.exception)
        if not control.raised and not candidate.raised:
            return self._comparator.compare(control.value, candidate.value)  # type: ignore
        return False
