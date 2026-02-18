"""Tests for Result."""

from __future__ import annotations

from scientist.observation import observe
from scientist.result import Result


def _make_result(
    *, matched: bool = True, ignored: bool = False
) -> Result[int]:
    control = observe("control", lambda: 1)
    candidate = observe("candidate", lambda: 1 if matched else 2)
    return Result(
        experiment_name="test",
        control=control,
        candidate=candidate,
        matched=matched,
        ignored=ignored,
    )


class TestResult:
    def test_matched(self):
        r = _make_result(matched=True)
        assert r.matched
        assert not r.mismatched
        assert not r.unexpected_mismatch
        assert not r.ignored_mismatch

    def test_mismatched(self):
        r = _make_result(matched=False)
        assert r.mismatched
        assert r.unexpected_mismatch
        assert not r.ignored_mismatch

    def test_ignored_mismatch(self):
        r = _make_result(matched=False, ignored=True)
        assert r.mismatched
        assert r.ignored_mismatch
        assert not r.unexpected_mismatch

    def test_matched_ignored_is_not_mismatch(self):
        r = _make_result(matched=True, ignored=True)
        assert not r.mismatched
        assert not r.unexpected_mismatch
        assert not r.ignored_mismatch
