"""Tests for Experiment syntactic sugar: run_if_entity, run_if_group, run_if_percent."""

from __future__ import annotations

from scientist import Experiment


class TestRunIfEntity:
    def test_deterministic_gating(self):
        """Same entity always gets same result for same experiment."""
        results = []
        for _ in range(10):
            exp = Experiment[int]("pricing-v2")
            exp.use(lambda: 42)
            exp.try_(lambda: 99)
            exp.run_if_entity("customer-abc", percent=50)

            publisher_results = []

            class Capture:
                def publish(self, result):
                    publisher_results.append(result)

            exp.publish(Capture())
            exp.run()
            results.append(len(publisher_results) > 0)

        # All runs should have the same gating decision
        assert len(set(results)) == 1

    def test_uses_experiment_name_as_salt(self):
        """Different experiment names can bucket the same entity differently."""
        decisions = {}
        for name in [f"exp-{i}" for i in range(50)]:
            ran_candidate = False

            class Tracker:
                def publish(self, result):
                    nonlocal ran_candidate
                    ran_candidate = True

            exp = Experiment[int](name)
            exp.use(lambda: 42)
            exp.try_(lambda: 99)
            exp.run_if_entity("user-123", percent=50)
            exp.publish(Tracker())
            exp.run()
            decisions[name] = ran_candidate

        # At 50%, not all experiments should gate the same way
        values = list(decisions.values())
        assert True in values and False in values

    def test_returns_self_for_chaining(self):
        exp = Experiment[int]("test")
        result = exp.run_if_entity("user-1", percent=50)
        assert result is exp


class TestRunIfGroup:
    def test_enabled_when_in_group(self):
        ran_candidate = False

        class Tracker:
            def publish(self, result):
                nonlocal ran_candidate
                ran_candidate = True

        exp = Experiment[int]("dashboard-v2")
        exp.use(lambda: 1)
        exp.try_(lambda: 2)
        exp.run_if_group(allowed={"beta"}, actual={"beta", "premium"})
        exp.publish(Tracker())
        exp.run()

        assert ran_candidate

    def test_disabled_when_not_in_group(self):
        ran_candidate = False

        class Tracker:
            def publish(self, result):
                nonlocal ran_candidate
                ran_candidate = True

        exp = Experiment[int]("dashboard-v2")
        exp.use(lambda: 1)
        exp.try_(lambda: 2)
        exp.run_if_group(allowed={"internal"}, actual={"premium"})
        exp.publish(Tracker())
        exp.run()

        assert not ran_candidate

    def test_returns_self_for_chaining(self):
        exp = Experiment[int]("test")
        result = exp.run_if_group(allowed={"a"}, actual={"b"})
        assert result is exp


class TestRunIfPercent:
    def test_zero_never_runs(self):
        ran_count = 0

        class Counter:
            def publish(self, result):
                nonlocal ran_count
                ran_count += 1

        for _ in range(50):
            exp = Experiment[int]("test")
            exp.use(lambda: 1)
            exp.try_(lambda: 2)
            exp.run_if_percent(0)
            exp.publish(Counter())
            exp.run()

        assert ran_count == 0

    def test_hundred_always_runs(self):
        ran_count = 0

        class Counter:
            def publish(self, result):
                nonlocal ran_count
                ran_count += 1

        for _ in range(50):
            exp = Experiment[int]("test")
            exp.use(lambda: 1)
            exp.try_(lambda: 2)
            exp.run_if_percent(100)
            exp.publish(Counter())
            exp.run()

        assert ran_count == 50

    def test_returns_self_for_chaining(self):
        exp = Experiment[int]("test")
        result = exp.run_if_percent(50)
        assert result is exp
