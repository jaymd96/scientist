"""Tests for Experiment."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scientist.context import set_default_enabled, set_default_publisher
from scientist.errors import ExperimentMismatchError
from scientist.experiment import Experiment
from scientist.publishers import NoopPublisher


class TestExperimentBasics:
    def test_returns_control_value(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        assert exp.run() == 42

    def test_returns_control_on_mismatch(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 99)
        assert exp.run() == 42

    def test_candidate_exception_doesnt_affect_control(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert exp.run() == 42

    def test_control_exception_is_reraised(self):
        exp = Experiment[int]("test")
        exp.use(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
        exp.try_(lambda: 42)
        with pytest.raises(RuntimeError, match="fail"):
            exp.run()

    def test_missing_control_raises(self):
        exp = Experiment[int]("test")
        exp.try_(lambda: 42)
        with pytest.raises(ValueError, match="Control"):
            exp.run()

    def test_missing_candidate_raises(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        with pytest.raises(ValueError, match="Candidate"):
            exp.run()


class TestGates:
    def test_run_if_false_skips_candidate(self):
        candidate_called = False

        def candidate():
            nonlocal candidate_called
            candidate_called = True
            return 99

        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(candidate)
        exp.run_if(lambda: False)
        result = exp.run()
        assert result == 42
        assert not candidate_called

    def test_run_if_true_runs_candidate(self):
        candidate_called = False

        def candidate():
            nonlocal candidate_called
            candidate_called = True
            return 42

        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(candidate)
        exp.run_if(lambda: True)
        exp.run()
        assert candidate_called

    def test_disabled_skips_candidate(self):
        candidate_called = False

        def candidate():
            nonlocal candidate_called
            candidate_called = True
            return 99

        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(candidate)
        exp.enabled(False)
        result = exp.run()
        assert result == 42
        assert not candidate_called

    def test_default_enabled_false(self):
        candidate_called = False

        def candidate():
            nonlocal candidate_called
            candidate_called = True
            return 99

        set_default_enabled(False)
        try:
            exp = Experiment[int]("test")
            exp.use(lambda: 42)
            exp.try_(candidate)
            exp.run()
            assert not candidate_called
        finally:
            set_default_enabled(True)


class TestIgnoreFilters:
    def test_ignore_filter_marks_ignored(self):
        publisher = MagicMock()
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 99)
        exp.ignore(lambda r: True)
        exp.publish(publisher)
        exp.run()

        published_result = publisher.publish.call_args[0][0]
        assert published_result.ignored
        assert published_result.mismatched

    def test_no_ignore_filter_leaves_unignored(self):
        publisher = MagicMock()
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 99)
        exp.publish(publisher)
        exp.run()

        published_result = publisher.publish.call_args[0][0]
        assert not published_result.ignored
        assert published_result.mismatched


class TestRaiseOnMismatches:
    def test_raises_on_mismatch(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 99)
        exp.raise_on_mismatches()
        with pytest.raises(ExperimentMismatchError):
            exp.run()

    def test_no_raise_on_match(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        exp.raise_on_mismatches()
        assert exp.run() == 42

    def test_no_raise_on_ignored_mismatch(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 99)
        exp.raise_on_mismatches()
        exp.ignore(lambda r: True)
        assert exp.run() == 42


class TestHooksAndCleanup:
    def test_before_run_hooks(self):
        calls = []
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        exp.before_run(lambda: calls.append("hook1"))
        exp.before_run(lambda: calls.append("hook2"))
        exp.run()
        assert calls == ["hook1", "hook2"]

    def test_cleanup_runs_on_success(self):
        cleaned = []
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        exp.clean(lambda: cleaned.append(True))
        exp.run()
        assert cleaned == [True]

    def test_cleanup_runs_on_error(self):
        cleaned = []
        exp = Experiment[int]("test")
        exp.use(lambda: (_ for _ in ()).throw(RuntimeError()))
        exp.try_(lambda: 42)
        exp.clean(lambda: cleaned.append(True))
        with pytest.raises(RuntimeError):
            exp.run()
        assert cleaned == [True]


class TestPublishing:
    def test_publishes_result(self):
        publisher = MagicMock()
        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        exp.publish(publisher)
        exp.run()
        publisher.publish.assert_called_once()

    def test_default_publisher(self):
        publisher = MagicMock()
        set_default_publisher(publisher)
        try:
            exp = Experiment[int]("test")
            exp.use(lambda: 42)
            exp.try_(lambda: 42)
            exp.run()
            publisher.publish.assert_called_once()
        finally:
            set_default_publisher(None)

    def test_publisher_error_doesnt_propagate(self):
        def bad_publisher_fn(result):
            raise RuntimeError("publish failed")

        publisher = MagicMock()
        publisher.publish.side_effect = RuntimeError("publish failed")

        exp = Experiment[int]("test")
        exp.use(lambda: 42)
        exp.try_(lambda: 42)
        exp.publish(publisher)
        assert exp.run() == 42  # Should not raise


class TestRandomOrder:
    @patch("scientist.experiment.random")
    def test_control_first(self, mock_random):
        mock_random.random.return_value = 0.1
        order = []

        def control():
            order.append("control")
            return 42

        def candidate():
            order.append("candidate")
            return 42

        exp = Experiment[int]("test")
        exp.use(control)
        exp.try_(candidate)
        exp.run()
        assert order == ["control", "candidate"]

    @patch("scientist.experiment.random")
    def test_candidate_first(self, mock_random):
        mock_random.random.return_value = 0.9
        order = []

        def control():
            order.append("control")
            return 42

        def candidate():
            order.append("candidate")
            return 42

        exp = Experiment[int]("test")
        exp.use(control)
        exp.try_(candidate)
        exp.run()
        assert order == ["candidate", "control"]


class TestAsyncRun:
    @pytest.mark.asyncio
    async def test_async_returns_control(self):
        exp = Experiment[int]("test")
        exp.use(lambda: 42)  # type: ignore
        exp.try_(lambda: 42)  # type: ignore

        # For async_run, behaviors should be async
        async def control():
            return 42

        async def candidate():
            return 42

        exp2 = Experiment[int]("test")
        exp2.use(control)  # type: ignore
        exp2.try_(candidate)  # type: ignore
        result = await exp2.async_run()
        assert result == 42

    @pytest.mark.asyncio
    async def test_async_mismatch(self):
        async def control():
            return 42

        async def candidate():
            return 99

        publisher = MagicMock()
        exp = Experiment[int]("test")
        exp.use(control)  # type: ignore
        exp.try_(candidate)  # type: ignore
        exp.publish(publisher)
        result = await exp.async_run()
        assert result == 42

        published_result = publisher.publish.call_args[0][0]
        assert published_result.mismatched

    @pytest.mark.asyncio
    async def test_async_disabled_skips(self):
        called = False

        async def candidate():
            nonlocal called
            called = True
            return 99

        async def control():
            return 42

        exp = Experiment[int]("test")
        exp.use(control)  # type: ignore
        exp.try_(candidate)  # type: ignore
        exp.enabled(False)
        result = await exp.async_run()
        assert result == 42
        assert not called
