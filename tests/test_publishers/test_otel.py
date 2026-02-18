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


class TestOTelPublisher:
    def test_records_total_counter_on_match(self):
        mock_meter = MagicMock()
        mock_counter = MagicMock()
        mock_mismatch_counter = MagicMock()
        mock_histogram = MagicMock()

        mock_meter.create_counter.side_effect = [mock_counter, mock_mismatch_counter]
        mock_meter.create_histogram.return_value = mock_histogram

        with patch("scientist.publishers.otel.metrics") as mock_metrics:
            mock_metrics.get_meter.return_value = mock_meter

            publisher = OTelPublisher()
            publisher.publish(_make_result(matched=True))

            mock_counter.add.assert_called_once()
            args = mock_counter.add.call_args
            assert args[0][0] == 1
            assert args[0][1]["matched"] == "true"

            mock_mismatch_counter.add.assert_not_called()

    def test_records_mismatch_counter(self):
        mock_meter = MagicMock()
        mock_counter = MagicMock()
        mock_mismatch_counter = MagicMock()
        mock_histogram = MagicMock()

        mock_meter.create_counter.side_effect = [mock_counter, mock_mismatch_counter]
        mock_meter.create_histogram.return_value = mock_histogram

        with patch("scientist.publishers.otel.metrics") as mock_metrics:
            mock_metrics.get_meter.return_value = mock_meter

            publisher = OTelPublisher()
            publisher.publish(_make_result(matched=False))

            mock_mismatch_counter.add.assert_called_once()

    def test_records_duration_histogram(self):
        mock_meter = MagicMock()
        mock_counter = MagicMock()
        mock_mismatch_counter = MagicMock()
        mock_histogram = MagicMock()

        mock_meter.create_counter.side_effect = [mock_counter, mock_mismatch_counter]
        mock_meter.create_histogram.return_value = mock_histogram

        with patch("scientist.publishers.otel.metrics") as mock_metrics:
            mock_metrics.get_meter.return_value = mock_meter

            publisher = OTelPublisher()
            publisher.publish(_make_result())

            assert mock_histogram.record.call_count == 2
            calls = mock_histogram.record.call_args_list
            assert calls[0][0][1]["behavior"] == "control"
            assert calls[1][0][1]["behavior"] == "candidate"

    def test_graceful_without_otel(self):
        """Should not raise if opentelemetry not installed."""
        publisher = OTelPublisher()
        # Force re-init
        publisher._initialized = False
        publisher._meter = None

        with patch.dict("sys.modules", {"opentelemetry": None, "opentelemetry.metrics": None}):
            publisher._initialized = False
            # Should not raise
            publisher.publish(_make_result())

    def test_custom_meter_name(self):
        mock_meter = MagicMock()
        mock_meter.create_counter.return_value = MagicMock()
        mock_meter.create_histogram.return_value = MagicMock()

        with patch("scientist.publishers.otel.metrics") as mock_metrics:
            mock_metrics.get_meter.return_value = mock_meter

            publisher = OTelPublisher(meter_name="my-experiments")
            publisher.publish(_make_result())

            mock_metrics.get_meter.assert_called_once_with("my-experiments")
