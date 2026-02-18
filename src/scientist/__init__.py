"""Scientist: Safe refactoring through controlled experiments.

Run old (control) and new (candidate) code paths simultaneously,
compare results, and publish findings. The control's result is
always returned to the caller.

    from scientist import Experiment

    exp = Experiment[int]("my-experiment")
    exp.use(lambda: old_algorithm())
    exp.try_(lambda: new_algorithm())
    result = exp.run()  # Returns old_algorithm() result
"""

from __future__ import annotations

from .comparators import (
    CallableComparator,
    DefaultComparator,
    comparator_from_func,
    percent_difference_comparator,
    set_comparator,
)
from .context import (
    get_default_enabled,
    get_default_publisher,
    set_default_enabled,
    set_default_publisher,
)
from .errors import ExperimentMismatchError
from .experiment import Experiment
from .observation import Observation, async_observe, observe
from .protocols import Comparator, Publisher
from .publishers import (
    CompositePublisher,
    LogPublisher,
    NoopPublisher,
    OTelPublisher,
    new_composite_publisher,
    new_log_publisher,
    new_noop_publisher,
    new_otel_publisher,
)
from .result import Result

__all__ = [
    "Experiment",
    "Observation",
    "Result",
    "Comparator",
    "Publisher",
    "DefaultComparator",
    "CallableComparator",
    "comparator_from_func",
    "percent_difference_comparator",
    "set_comparator",
    "NoopPublisher",
    "LogPublisher",
    "CompositePublisher",
    "OTelPublisher",
    "new_noop_publisher",
    "new_log_publisher",
    "new_composite_publisher",
    "new_otel_publisher",
    "ExperimentMismatchError",
    "observe",
    "async_observe",
    "set_default_publisher",
    "get_default_publisher",
    "set_default_enabled",
    "get_default_enabled",
]
