"""Tests for collection condition plugins."""

from src.plugins.conditions.collection_condition import (
    ContainsInCollection,
    LengthEquals,
    IsEmpty,
)


def test_contains_in_collection_pass() -> None:
    plugin = ContainsInCollection(key="items", expected=2)
    assert plugin.evaluate({"items": [1, 2, 3]})


def test_contains_in_collection_fail() -> None:
    plugin = ContainsInCollection(key="items", expected=4)
    assert not plugin.evaluate({"items": [1, 2, 3]})


def test_length_equals_pass() -> None:
    plugin = LengthEquals(key="items", expected=3)
    assert plugin.evaluate({"items": [1, 2, 3]})


def test_length_equals_fail() -> None:
    plugin = LengthEquals(key="items", expected=2)
    assert not plugin.evaluate({"items": [1, 2, 3]})


def test_is_empty_pass() -> None:
    plugin = IsEmpty(key="items")
    assert plugin.evaluate({"items": []})


def test_is_empty_fail() -> None:
    plugin = IsEmpty(key="items")
    assert not plugin.evaluate({"items": [1]})
