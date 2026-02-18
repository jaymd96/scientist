"""Tests for Observation and observe()."""

from __future__ import annotations

import asyncio

import pytest

from scientist.observation import Observation, async_observe, observe


class TestObserve:
    def test_successful_observation(self):
        obs = observe("test", lambda: 42)
        assert obs.name == "test"
        assert obs.value == 42
        assert obs.exception is None
        assert not obs.raised
        assert obs.duration_seconds >= 0
        assert obs.cpu_time_seconds >= 0

    def test_exception_observation(self):
        obs = observe("test", lambda: (_ for _ in ()).throw(ValueError("boom")))
        assert obs.raised
        assert isinstance(obs.exception, ValueError)
        assert obs.value is None
        assert obs.duration_seconds >= 0

    def test_value_or_raise_success(self):
        obs = observe("test", lambda: 42)
        assert obs.value_or_raise == 42

    def test_value_or_raise_exception(self):
        def fail():
            raise RuntimeError("fail")

        obs = observe("test", fail)
        with pytest.raises(RuntimeError, match="fail"):
            obs.value_or_raise


class TestEquivalentTo:
    def test_same_values(self):
        a = observe("a", lambda: 42)
        b = observe("b", lambda: 42)
        assert a.equivalent_to(b)

    def test_different_values(self):
        a = observe("a", lambda: 42)
        b = observe("b", lambda: 99)
        assert not a.equivalent_to(b)

    def test_same_exception_type(self):
        def raise_value_error():
            raise ValueError("x")

        a = observe("a", raise_value_error)
        b = observe("b", raise_value_error)
        assert a.equivalent_to(b)

    def test_different_exception_types(self):
        a = observe("a", lambda: (_ for _ in ()).throw(ValueError()))
        b = observe("b", lambda: (_ for _ in ()).throw(TypeError()))
        assert not a.equivalent_to(b)

    def test_one_raised_one_didnt(self):
        a = observe("a", lambda: 42)

        def fail():
            raise ValueError()

        b = observe("b", fail)
        assert not a.equivalent_to(b)


class TestAsyncObserve:
    @pytest.mark.asyncio
    async def test_successful_async_observation(self):
        async def compute():
            return 42

        obs = await async_observe("test", compute)
        assert obs.value == 42
        assert not obs.raised

    @pytest.mark.asyncio
    async def test_exception_async_observation(self):
        async def fail():
            raise ValueError("async boom")

        obs = await async_observe("test", fail)
        assert obs.raised
        assert isinstance(obs.exception, ValueError)
