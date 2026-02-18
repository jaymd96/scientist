"""Structlog-based publisher for experiment results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocols import Publisher

if TYPE_CHECKING:
    from ..result import Result


class LogPublisher:
    """Publisher that logs results via structlog.

    Gracefully degrades to no-op if structlog is not installed.
    """

    def publish(self, result: Result[object]) -> None:
        try:
            import structlog
        except ImportError:
            return

        logger = structlog.get_logger("scientist")

        if result.matched:
            logger.info(
                "experiment matched",
                experiment=result.experiment_name,
                control_duration=result.control.duration_seconds,
                candidate_duration=result.candidate.duration_seconds,
            )
        elif result.ignored_mismatch:
            logger.info(
                "experiment mismatched (ignored)",
                experiment=result.experiment_name,
                control_value=repr(result.control.value),
                candidate_value=repr(result.candidate.value),
            )
        else:
            logger.warning(
                "experiment mismatched",
                experiment=result.experiment_name,
                control_value=repr(result.control.value),
                candidate_value=repr(result.candidate.value),
                control_duration=result.control.duration_seconds,
                candidate_duration=result.candidate.duration_seconds,
                control_raised=result.control.raised,
                candidate_raised=result.candidate.raised,
            )


def new_log_publisher() -> Publisher:
    return LogPublisher()  # type: ignore
