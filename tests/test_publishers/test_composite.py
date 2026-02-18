"""Tests for CompositePublisher."""

from __future__ import annotations

from unittest.mock import MagicMock

from scientist.observation import observe
from scientist.publishers.composite import CompositePublisher
from scientist.result import Result


def _make_result() -> Result[int]:
    control = observe("control", lambda: 42)
    candidate = observe("candidate", lambda: 42)
    return Result(
        experiment_name="test",
        control=control,
        candidate=candidate,
        matched=True,
        ignored=False,
    )


class TestCompositePublisher:
    def test_publishes_to_all(self):
        p1 = MagicMock()
        p2 = MagicMock()
        p3 = MagicMock()

        composite = CompositePublisher(p1, p2, p3)
        result = _make_result()
        composite.publish(result)

        p1.publish.assert_called_once_with(result)
        p2.publish.assert_called_once_with(result)
        p3.publish.assert_called_once_with(result)

    def test_one_error_doesnt_stop_others(self):
        p1 = MagicMock()
        p2 = MagicMock()
        p2.publish.side_effect = RuntimeError("broken")
        p3 = MagicMock()

        composite = CompositePublisher(p1, p2, p3)
        composite.publish(_make_result())

        p1.publish.assert_called_once()
        p2.publish.assert_called_once()
        p3.publish.assert_called_once()
