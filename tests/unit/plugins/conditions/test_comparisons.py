"""Unit tests for comparison condition plugins."""

from typing import Any

from src.core.manifest import PluginType
from src.plugins.conditions.comparisons import (
    Equal,
    GreaterOrEqualThan,
    GreaterThan,
    LessOrEqualThan,
    LessThan,
    NotEqual,
)


class TestGreaterThan:
    """Tests for GreaterThan condition."""

    def test_evaluate_true(self) -> None:
        condition = GreaterThan(key="score", value=5)
        assert condition.evaluate({"score": 10}) is True

    def test_evaluate_false(self) -> None:
        condition = GreaterThan(key="score", value=5)
        assert condition.evaluate({"score": 3}) is False

    def test_evaluate_equal_returns_false(self) -> None:
        condition = GreaterThan(key="score", value=5)
        assert condition.evaluate({"score": 5}) is False

    def test_manifest_metadata(self) -> None:
        condition = GreaterThan(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "greater-than-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION


class TestLessThan:
    """Tests for LessThan condition."""

    def test_evaluate_true(self) -> None:
        condition = LessThan(key="score", value=5)
        assert condition.evaluate({"score": 3}) is True

    def test_evaluate_false(self) -> None:
        condition = LessThan(key="score", value=5)
        assert condition.evaluate({"score": 10}) is False

    def test_evaluate_equal_returns_false(self) -> None:
        condition = LessThan(key="score", value=5)
        assert condition.evaluate({"score": 5}) is False

    def test_manifest_metadata(self) -> None:
        condition = LessThan(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "less-than-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION


class TestEqual:
    """Tests for Equal condition."""

    def test_evaluate_true(self) -> None:
        condition = Equal(key="status", value="active")
        assert condition.evaluate({"status": "active"}) is True

    def test_evaluate_false(self) -> None:
        condition = Equal(key="status", value="active")
        assert condition.evaluate({"status": "inactive"}) is False

    def test_evaluate_missing_key(self) -> None:
        condition = Equal(key="status", value="active")
        assert condition.evaluate({}) is False

    def test_manifest_metadata(self) -> None:
        condition = Equal(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "equal-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION


class TestNotEqual:
    """Tests for NotEqual condition."""

    def test_evaluate_true(self) -> None:
        condition = NotEqual(key="status", value="active")
        assert condition.evaluate({"status": "inactive"}) is True

    def test_evaluate_false(self) -> None:
        condition = NotEqual(key="status", value="active")
        assert condition.evaluate({"status": "active"}) is False

    def test_manifest_metadata(self) -> None:
        condition = NotEqual(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "not-equal-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION


class TestGreaterOrEqualThan:
    """Tests for GreaterOrEqualThan condition."""

    def test_evaluate_greater_true(self) -> None:
        condition = GreaterOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 10}) is True

    def test_evaluate_equal_true(self) -> None:
        condition = GreaterOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 5}) is True

    def test_evaluate_less_false(self) -> None:
        condition = GreaterOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 3}) is False

    def test_manifest_metadata(self) -> None:
        condition = GreaterOrEqualThan(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "greater-or-equal-than-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION


class TestLessOrEqualThan:
    """Tests for LessOrEqualThan condition."""

    def test_evaluate_less_true(self) -> None:
        condition = LessOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 3}) is True

    def test_evaluate_equal_true(self) -> None:
        condition = LessOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 5}) is True

    def test_evaluate_greater_false(self) -> None:
        condition = LessOrEqualThan(key="score", value=5)
        assert condition.evaluate({"score": 10}) is False

    def test_manifest_metadata(self) -> None:
        condition = LessOrEqualThan(key="x", value=0)
        manifest = condition.manifest
        assert manifest.name == "less-or-equal-than-condition"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.CONDITION
