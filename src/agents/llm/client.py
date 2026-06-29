"""Provider-agnostic LLM client using the OpenAI-compatible API format.

Works with OpenRouter, local LLM servers (Ollama, vLLM), OpenAI, or
any endpoint that implements the chat completions interface.

Configuration via environment variables:
    LLM_API_KEY:       API key for the provider (required)
    LLM_BASE_URL:      Base URL of the API (default: https://openrouter.ai/api/v1)
    LLM_MODEL:         Model identifier (default: anthropic/claude-sonnet-4-20250514)
    LLM_MAX_TOKENS:    Max response tokens (default: 4096)
    LLM_TEMPERATURE:   Sampling temperature (default: 0.3)
"""

import json
import os
import re
from pathlib import Path
from typing import Any

from openai import OpenAI, OpenAIError

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "anthropic/claude-sonnet-4-20250514"


class LLMClient:
    """Thin wrapper around any OpenAI-compatible chat completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize the LLM client.

        Args:
            api_key: API key. Falls back to LLM_API_KEY env var.
            base_url: API base URL. Falls back to LLM_BASE_URL env var.
            model: Model identifier. Falls back to LLM_MODEL env var.

        Raises:
            LLMConfigError: If no API key is configured.
        """
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL", _DEFAULT_BASE_URL)
        self.model = model or os.environ.get("LLM_MODEL", _DEFAULT_MODEL)
        self.max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
        self.temperature = float(os.environ.get("LLM_TEMPERATURE", "0.3"))

        if not self.api_key:
            raise LLMConfigError(
                "No API key configured. Set LLM_API_KEY environment variable."
            )

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def invoke(self, system_prompt: str, user_message: str) -> str:
        """Send a message to the LLM and return the response text.

        Args:
            system_prompt: The system-level instructions for the model.
            user_message: The user-level message/context for the model.

        Returns:
            The model's text response.

        Raises:
            LLMError: If the API call fails.
        """
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )
            content = response.choices[0].message.content
            return content or ""
        except OpenAIError as e:
            raise LLMError(f"LLM invocation failed: {e}") from e


class LLMError(Exception):
    """Raised when an LLM invocation fails."""


class LLMConfigError(Exception):
    """Raised when LLM configuration is missing or invalid."""


def load_system_prompt(agent_name: str) -> str:
    """Load a system prompt from the prompts directory.

    Args:
        agent_name: Agent role name (e.g., "planner", "developer").

    Returns:
        The system prompt text.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
    """
    prompt_file = _PROMPTS_DIR / f"{agent_name}_system_prompt.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"System prompt not found: {prompt_file}")
    return prompt_file.read_text()


def parse_json_response(response: str) -> dict[str, Any]:
    """Extract a JSON block from an LLM response.

    The LLM may wrap JSON in markdown fences. This function extracts and parses it.

    Args:
        response: Raw LLM response text.

    Returns:
        Parsed dictionary from the JSON content.

    Raises:
        ValueError: If no valid JSON can be extracted.
    """
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", response, re.DOTALL)
    if match:
        result: dict[str, Any] = json.loads(match.group(1))
        return result

    try:
        result = json.loads(response)
        return result
    except json.JSONDecodeError:
        pass

    raise ValueError("Could not extract valid JSON from LLM response")
