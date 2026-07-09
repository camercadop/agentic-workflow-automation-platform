"""Unit tests for src/agents/llm/client.py (utility functions and config)."""

import pytest

from src.agents.llm.client import LLMConfigError, LLMError, parse_json_response


class TestParseJsonResponse:
    def test_parse_fenced_json(self) -> None:
        response = '```json\n{"key": "value"}\n```'
        assert parse_json_response(response) == {"key": "value"}

    def test_parse_raw_json(self) -> None:
        assert parse_json_response('{"a": 1}') == {"a": 1}

    def test_parse_fenced_no_lang(self) -> None:
        response = '```\n{"x": true}\n```'
        assert parse_json_response(response) == {"x": True}

    def test_parse_invalid_raises(self) -> None:
        with pytest.raises(ValueError, match="Could not extract"):
            parse_json_response("not json at all")

    def test_parse_with_surrounding_text(self) -> None:
        response = 'Here is the result:\n```json\n{"status": "ok"}\n```\nDone.'
        assert parse_json_response(response) == {"status": "ok"}


class TestLLMClientInit:
    def test_missing_api_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        with pytest.raises(LLMConfigError, match="No API key"):
            from src.agents.llm.client import LLMClient

            LLMClient(api_key="")


class TestExceptions:
    def test_llm_error_is_exception(self) -> None:
        err = LLMError("test")
        assert str(err) == "test"
        assert isinstance(err, Exception)

    def test_llm_config_error_is_exception(self) -> None:
        err = LLMConfigError("bad config")
        assert str(err) == "bad config"
        assert isinstance(err, Exception)
