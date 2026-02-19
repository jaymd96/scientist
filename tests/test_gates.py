"""Tests for gate factory functions."""

from __future__ import annotations

from scientist.gates import entity_gate, group_gate, request_gate


class TestEntityGate:
    def test_deterministic_same_result(self):
        """Same entity_id + salt always produces the same result."""
        gate = entity_gate("customer-123", percent=50, salt="exp-a")
        results = [gate() for _ in range(100)]
        assert len(set(results)) == 1  # always the same

    def test_deterministic_across_instances(self):
        """Two gates with same params produce the same result."""
        a = entity_gate("customer-123", percent=50, salt="exp-a")
        b = entity_gate("customer-123", percent=50, salt="exp-a")
        assert a() == b()

    def test_different_salt_different_bucket(self):
        """Different salts can produce different results for same entity."""
        # With enough entities, different salts should bucket differently
        results_a = {
            eid: entity_gate(eid, percent=50, salt="exp-a")()
            for eid in [f"user-{i}" for i in range(200)]
        }
        results_b = {
            eid: entity_gate(eid, percent=50, salt="exp-b")()
            for eid in [f"user-{i}" for i in range(200)]
        }
        # Not all entities should be bucketed the same across experiments
        assert results_a != results_b

    def test_zero_percent_always_false(self):
        gate = entity_gate("anyone", percent=0, salt="test")
        assert gate() is False

    def test_hundred_percent_always_true(self):
        gate = entity_gate("anyone", percent=100, salt="test")
        assert gate() is True

    def test_distribution_roughly_correct(self):
        """With many entities at 30%, roughly 30% should be enabled."""
        enabled = sum(
            entity_gate(f"user-{i}", percent=30, salt="dist-test")()
            for i in range(1000)
        )
        # Allow ±5% tolerance
        assert 250 <= enabled <= 350

    def test_no_salt_still_deterministic(self):
        gate = entity_gate("customer-123", percent=50)
        results = [gate() for _ in range(50)]
        assert len(set(results)) == 1


class TestGroupGate:
    def test_match_single_group(self):
        gate = group_gate(allowed={"beta"}, actual={"beta", "premium"})
        assert gate() is True

    def test_no_match(self):
        gate = group_gate(allowed={"internal"}, actual={"beta", "premium"})
        assert gate() is False

    def test_empty_actual(self):
        gate = group_gate(allowed={"beta"}, actual=set())
        assert gate() is False

    def test_empty_allowed(self):
        gate = group_gate(allowed=set(), actual={"beta"})
        assert gate() is False

    def test_multiple_overlapping(self):
        gate = group_gate(
            allowed={"beta", "internal", "dogfood"},
            actual={"premium", "internal"},
        )
        assert gate() is True

    def test_works_with_lists(self):
        gate = group_gate(allowed=["beta", "internal"], actual=["internal"])
        assert gate() is True

    def test_deterministic(self):
        """Same inputs always produce same result."""
        gate = group_gate(allowed={"beta"}, actual={"beta"})
        results = [gate() for _ in range(50)]
        assert all(results)


class TestRequestGate:
    def test_zero_percent_always_false(self):
        gate = request_gate(percent=0)
        results = [gate() for _ in range(100)]
        assert not any(results)

    def test_hundred_percent_always_true(self):
        gate = request_gate(percent=100)
        results = [gate() for _ in range(100)]
        assert all(results)

    def test_distribution_roughly_correct(self):
        """With many calls at 30%, roughly 30% should return True."""
        gate = request_gate(percent=30)
        enabled = sum(gate() for _ in range(10000))
        assert 2500 <= enabled <= 3500

    def test_non_deterministic(self):
        """Different calls can produce different results."""
        gate = request_gate(percent=50)
        results = [gate() for _ in range(100)]
        # At 50%, extremely unlikely to be all True or all False
        assert 0 < sum(results) < 100
