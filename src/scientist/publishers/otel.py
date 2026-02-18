"""OpenTelemetry publisher for experiment results.

Records experiment metrics via OpenTelemetry meters:
- scientist.experiment.total: Counter of experiments run
- scientist.experiment.duration: Histogram of execution duration
- scientist.experiment.mismatches: Counter of unexpected mismatches

Gracefully degrades to no-op if opentelemetry-api is not installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..protocols import Publisher

if TYPE_CHECKING:
    from ..result import Result


class OTelPublisher:
    """Publisher that records experiment results as OpenTelemetry metrics.

    Uses opentelemetry-api only (not SDK), so the user configures their
    own exporter (OTLP to SigNoz, Prometheus, etc.).

    Args:
        meter_name: Name for the OTel meter (default: "scientist")
    """

    def __init__(self, meter_name: str = "scientist") -> None:
        self._meter_name = meter_name
        self._meter = None
        self._total_counter = None
        self._mismatch_counter = None
        self._duration_histogram = None
        self._initialized = False

    def _ensure_initialized(self) -> bool:
        """Lazy-init OTel instruments. Returns False if OTel unavailable."""
        if self._initialized:
            return self._meter is not None

        self._initialized = True

        try:
            from opentelemetry import metrics
        except ImportError:
            return False

        self._meter = metrics.get_meter(self._meter_name)

        self._total_counter = self._meter.create_counter(
            "scientist.experiment.total",
            description="Total experiment runs",
            unit="1",
        )

        self._mismatch_counter = self._meter.create_counter(
            "scientist.experiment.mismatches",
            description="Unexpected experiment mismatches",
            unit="1",
        )

        self._duration_histogram = self._meter.create_histogram(
            "scientist.experiment.duration",
            description="Experiment behavior execution duration",
            unit="s",
        )

        return True

    def publish(self, result: Result[object]) -> None:
        if not self._ensure_initialized():
            return

        attributes = {
            "experiment": result.experiment_name,
            "matched": str(result.matched).lower(),
            "ignored": str(result.ignored).lower(),
        }

        self._total_counter.add(1, attributes)  # type: ignore

        if result.unexpected_mismatch:
            self._mismatch_counter.add(  # type: ignore
                1, {"experiment": result.experiment_name}
            )

        self._duration_histogram.record(  # type: ignore
            result.control.duration_seconds,
            {
                "experiment": result.experiment_name,
                "behavior": "control",
            },
        )

        self._duration_histogram.record(  # type: ignore
            result.candidate.duration_seconds,
            {
                "experiment": result.experiment_name,
                "behavior": "candidate",
            },
        )

        # Record span event on mismatch if there's an active span
        if result.unexpected_mismatch:
            try:
                from opentelemetry import trace

                span = trace.get_current_span()
                if span.is_recording():
                    span.add_event(
                        "scientist.mismatch",
                        attributes={
                            "experiment": result.experiment_name,
                            "control.value": repr(result.control.value),
                            "candidate.value": repr(result.candidate.value),
                            "control.raised": result.control.raised,
                            "candidate.raised": result.candidate.raised,
                        },
                    )
            except Exception:
                pass


def new_otel_publisher(meter_name: str = "scientist") -> Publisher:
    return OTelPublisher(meter_name)  # type: ignore
