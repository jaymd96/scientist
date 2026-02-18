"""Tests for LogPublisher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from scientist.observation import observe
from scientist.publishers.log import LogPublisher
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


class TestLogPublisher:
    @patch("scientist.publishers.log.structlog")
    def test_logs_matched(self, mock_structlog):
        mock_logger = MagicMock()
        mock_structlog.get_logger.return_value = mock_logger

        publisher = LogPublisher()
        publisher.publish(_make_result(matched=True))

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "matched" in call_args[0][0]

    @patch("scientist.publishers.log.structlog")
    def test_logs_mismatch_warning(self, mock_structlog):
        mock_logger = MagicMock()
        mock_structlog.get_logger.return_value = mock_logger

        publisher = LogPublisher()
        publisher.publish(_make_result(matched=False))

        mock_logger.warning.assert_called_once()

    @patch("scientist.publishers.log.structlog")
    def test_logs_ignored_mismatch_info(self, mock_structlog):
        mock_logger = MagicMock()
        mock_structlog.get_logger.return_value = mock_logger

        publisher = LogPublisher()
        publisher.publish(_make_result(matched=False, ignored=True))

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "ignored" in call_args[0][0]

    def test_graceful_without_structlog(self):
        """Should not raise if structlog not installed."""
        publisher = LogPublisher()
        with patch.dict("sys.modules", {"structlog": None}):
            # This simulates ImportError on import
            publisher.publish(_make_result())
