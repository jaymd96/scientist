"""Tests for OTelPublisher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scientist.observation import observe
from scientist.publishers.otel import OTelPublisher
from scientist.result import Result


def _make_result(*, matched: bool = True, ignored: bool = False) -> Result[int]:
    control = observe("control", lambda: 42)
    candidate = observe("candidate", lambda: 42 if matched else 99)
    return Result(
        experiment_name="test",
        control=control,
        candidate=candidate,
        matched=matched,
        ignored=ignored,
    )


def _make_publisher_with_mocks():
    """Create an OTelPublisher with pre-injected mock instruments."""
    publisher = OTelPublisher()

    mock_counter = MagicMock()
    mock_mismatch_counter = MagicMock()
    mock_histogram = MagicMock()

    publisher._initialized = True
    publisher._meter = MagicMock()
    publisher._total_counter = mock_counter
    publisher._mismatch_counter = mock_mismatch_counter
    publisher._duration_histogram = mock_histogram

    return publisher, mock_counter, mock_mismatch_counter, mock_histogram


class TestOTelPublisher:
    def test_records_total_counter_on_match(self):
        publisher, counter, mismatch, histogram = _make_publisher_with_mocks()
        publisher.publish(_make_result(matched=True))

        counter.add.assert_called_once()
        args = counter.add.call_args
        assert args[0][0] == 1
        assert args[0][1]["matched"] == "true"
        mismatch.add.assert_not_called()

    def test_records_mismatch_counter(self):
        publisher, counter, mismatch, histogram = _make_publisher_with_mocks()
        publisher.publish(_make_result(matched=False))

        mismatch.add.assert_called_once()
        assert mismatch.add.call_args[0][1]["experiment"] == "test"

    def test_records_duration_histogram(self):
        publisher, counter, mismatch, histogram = _make_publisher_with_mocks()
        publisher.publish(_make_result())

        assert histogram.record.call_count == 2
        calls = histogram.record.call_args_list
        assert calls[0][0][1]["behavior"] == "control"
        assert calls[1][0][1]["behavior"] == "candidate"

    def test_ignored_mismatch_not_counted_as_unexpected(self):
        publisher, counter, mismatch, histogram = _make_publisher_with_mocks()
        publisher.publish(_make_result(matched=False, ignored=True))

        counter.add.assert_called_once()
        mismatch.add.assert_not_called()

    def test_lazy_initialization(self):
        """Instruments are created on first publish, not __init__."""
        publisher = OTelPublisher()
        assert not publisher._initialized
        assert publisher._meter is None

    def test_graceful_without_otel(self):
        """Should not raise if opentelemetry not installed."""
        publisher = OTelPublisher()
        publisher._initialized = False

        with patch.dict("sys.modules", {"opentelemetry": None, "opentelemetry.metrics": None}):
            publisher._initialized = False
            publisher.publish(_make_result())  # Should not raise

    def test_custom_meter_name(self):
        """Verifies meter_name is stored correctly."""
        publisher = OTelPublisher(meter_name="my-experiments")
        assert publisher._meter_name == "my-experiments"
