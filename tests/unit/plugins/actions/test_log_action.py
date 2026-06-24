"""Unit tests for LogAction plugin."""

import logging
from typing import Any

from src.core.manifest import PluginType
from src.plugins.actions.log_action import LogAction


class TestLogAction:
    """Tests for LogAction plugin behavior."""

    def test_execute_returns_data_unchanged(self) -> None:
        action = LogAction()
        data: dict[str, Any] = {"key": "value", "count": 42}
        result = action.execute(data)
        assert result == data

    def test_execute_logs_data(self, caplog: logging.LogCaptureFixture) -> None:
        action = LogAction()
        data: dict[str, Any] = {"msg": "hello"}
        with caplog.at_level(logging.INFO):
            action.execute(data)
        assert "LogAction received" in caplog.text
        assert "hello" in caplog.text

    def test_manifest_metadata(self) -> None:
        action = LogAction()
        manifest = action.manifest
        assert manifest.name == "log-action"
        assert manifest.version == "1.0.0"
        assert manifest.plugin_type == PluginType.ACTION
