"""Tests for NoopPublisher."""

from scientist.observation import observe
from scientist.publishers.noop import NoopPublisher
from scientist.result import Result


def test_noop_does_nothing():
    """Smoke test — noop publisher should not raise."""
    publisher = NoopPublisher()
    control = observe("control", lambda: 42)
    candidate = observe("candidate", lambda: 42)
    result = Result(
        experiment_name="test",
        control=control,
        candidate=candidate,
        matched=True,
        ignored=False,
    )
    publisher.publish(result)  # Should not raise
