"""Tests for comparators."""

from __future__ import annotations

from scientist.comparators import (
    CallableComparator,
    DefaultComparator,
    comparator_from_func,
    percent_difference_comparator,
    set_comparator,
)


class TestDefaultComparator:
    def test_equal(self):
        assert DefaultComparator().compare(42, 42)

    def test_not_equal(self):
        assert not DefaultComparator().compare(42, 99)

    def test_strings(self):
        assert DefaultComparator().compare("abc", "abc")
        assert not DefaultComparator().compare("abc", "xyz")


class TestCallableComparator:
    def test_custom_comparison(self):
        cmp = CallableComparator(lambda a, b: abs(a - b) < 5)
        assert cmp.compare(10, 12)
        assert not cmp.compare(10, 20)


class TestComparatorFromFunc:
    def test_wraps_function(self):
        cmp = comparator_from_func(lambda a, b: a == b)
        assert cmp.compare(1, 1)
        assert not cmp.compare(1, 2)


class TestPercentDifferenceComparator:
    def test_within_threshold(self):
        cmp = percent_difference_comparator(0.1)
        assert cmp.compare(100.0, 105.0)

    def test_outside_threshold(self):
        cmp = percent_difference_comparator(0.1)
        assert not cmp.compare(100.0, 120.0)

    def test_both_zero(self):
        cmp = percent_difference_comparator(0.1)
        assert cmp.compare(0.0, 0.0)

    def test_one_zero(self):
        cmp = percent_difference_comparator(0.1)
        assert not cmp.compare(0.0, 5.0)
        assert not cmp.compare(5.0, 0.0)

    def test_exact_threshold(self):
        cmp = percent_difference_comparator(0.1)
        assert cmp.compare(100.0, 110.0)


class TestSetComparator:
    def test_equal_sets(self):
        cmp = set_comparator()
        assert cmp.compare({1, 2, 3}, {3, 2, 1})

    def test_different_sets(self):
        cmp = set_comparator()
        assert not cmp.compare({1, 2}, {2, 3})
