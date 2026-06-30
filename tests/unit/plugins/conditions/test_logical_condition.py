"""Tests for logical condition plugins."""

from src.plugins.conditions.logical_condition import (
    AndCondition,
    OrCondition,
    NotCondition,
)
from src.plugins.conditions.true_condition import TrueCondition
from src.core.contracts import ConditionPlugin


class FalseCondition(ConditionPlugin):
    """Simple condition that always returns False."""

    def evaluate(self, data: dict[str, any]) -> bool:  # type: ignore[override]
        return False

    @property
    def manifest(self):
        # Minimal manifest for testing; not used in logic
        from src.core.manifest import PluginManifest, PluginType

        return PluginManifest(
            name="false-condition", version="1.0.0", plugin_type=PluginType.CONDITION
        )


def test_and_condition_all_true() -> None:
    cond = AndCondition([TrueCondition(), TrueCondition()])
    assert cond.evaluate({}) is True


def test_and_condition_one_false() -> None:
    cond = AndCondition([TrueCondition(), FalseCondition()])
    assert cond.evaluate({}) is False


def test_and_condition_empty() -> None:
    cond = AndCondition()
    assert cond.evaluate({}) is True


def test_or_condition_any_true() -> None:
    cond = OrCondition([FalseCondition(), TrueCondition()])
    assert cond.evaluate({}) is True


def test_or_condition_all_false() -> None:
    cond = OrCondition([FalseCondition(), FalseCondition()])
    assert cond.evaluate({}) is False


def test_or_condition_empty() -> None:
    cond = OrCondition()
    assert cond.evaluate({}) is False


def test_not_condition_true() -> None:
    cond = NotCondition(TrueCondition())
    assert cond.evaluate({}) is False


def test_not_condition_false() -> None:
    cond = NotCondition(FalseCondition())
    assert cond.evaluate({}) is True


def test_not_condition_none() -> None:
    cond = NotCondition()
    assert cond.evaluate({}) is True
