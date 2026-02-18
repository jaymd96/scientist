"""Tests for LogPublisher."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import structlog

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
    def test_logs_matched(self):
        mock_logger = MagicMock()
        with patch.object(structlog, "get_logger", return_value=mock_logger):
            publisher = LogPublisher()
            publisher.publish(_make_result(matched=True))
            mock_logger.info.assert_called_once()
            assert "matched" in mock_logger.info.call_args[0][0]

    def test_logs_mismatch_warning(self):
        mock_logger = MagicMock()
        with patch.object(structlog, "get_logger", return_value=mock_logger):
            publisher = LogPublisher()
            publisher.publish(_make_result(matched=False))
            mock_logger.warning.assert_called_once()

    def test_logs_ignored_mismatch_info(self):
        mock_logger = MagicMock()
        with patch.object(structlog, "get_logger", return_value=mock_logger):
            publisher = LogPublisher()
            publisher.publish(_make_result(matched=False, ignored=True))
            mock_logger.info.assert_called_once()
            assert "ignored" in mock_logger.info.call_args[0][0]

    def test_graceful_without_structlog(self):
        """Should not raise if structlog import fails."""
        publisher = LogPublisher()
        with patch.dict("sys.modules", {"structlog": None}):
            publisher.publish(_make_result())  # Should not raise
