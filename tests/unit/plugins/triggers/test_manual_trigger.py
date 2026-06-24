"""Unit tests for ManualTrigger plugin."""

from src.plugins.triggers.manual_trigger import ManualTrigger


def test_manual_trigger_with_config() -> None:
    config = {"data": {"key": "value", "status": "ok"}}
    trigger = ManualTrigger(config=config)
    result = trigger.check()
    assert result == {"event": "manual", "payload": {"key": "value", "status": "ok"}}


def test_manual_trigger_without_config() -> None:
    trigger = ManualTrigger()
    result = trigger.check()
    assert result == {"event": "manual", "payload": {}}
