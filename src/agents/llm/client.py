"""Provider-agnostic LLM client using the OpenAI-compatible API format.

Works with OpenRouter, local LLM servers (Ollama, vLLM), OpenAI, or
any endpoint that implements the chat completions interface.

Supports tool-calling: agents can invoke tools (file_ops, run_command)
iteratively until they produce a final text response.

Configuration via environment variables:
    LLM_API_KEY:       API key for the provider (required)
    LLM_BASE_URL:      Base URL of the API (default: https://openrouter.ai/api/v1)
    LLM_MODEL:         Model identifier (default: openrouter/free)
    LLM_MAX_TOKENS:    Max response tokens (default: 4096)
    LLM_TEMPERATURE:   Sampling temperature (default: 0.3)
    LLM_MAX_RETRIES:   Max retries for empty/failed responses (default: 3)
    LLM_RETRY_DELAY:   Initial retry delay in seconds (default: 2.0)
    LLM_RETRY_BACKOFF: Backoff multiplier per retry (default: 2.0)
"""

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from openai import OpenAI, OpenAIError
from openai.types.chat import ChatCompletionMessageToolCall

from src.agents.llm.tools import (
    MAX_TOOL_ITERATIONS,
    TOOL_SCHEMAS,
    execute_tool_call,
    set_workspace,
)

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
_DEFAULT_MODEL = "openrouter/free"


class LLMClient:
    """Thin wrapper around any OpenAI-compatible chat completions API.

    Supports single-shot invocations (invoke) and agentic tool-calling
    loops (invoke_with_tools). Includes retry logic with exponential
    backoff for transient failures and empty responses.
    """

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
        self.max_retries = int(os.environ.get("LLM_MAX_RETRIES", "3"))
        self.retry_delay = float(os.environ.get("LLM_RETRY_DELAY", "2.0"))
        self.retry_backoff = float(os.environ.get("LLM_RETRY_BACKOFF", "2.0"))

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

        This is a simple single-shot call with no tool support.
        Retries on empty responses or transient API errors.

        Args:
            system_prompt: The system-level instructions for the model.
            user_message: The user-level message/context for the model.

        Returns:
            The model's text response.

        Raises:
            LLMError: If the API call fails after all retries.
        """
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore[arg-type]
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
                choice = response.choices[0]
                finish_reason = choice.finish_reason
                content = choice.message.content or ""

                logger.debug(
                    "invoke: attempt=%d, finish_reason=%s, content_len=%d",
                    attempt + 1,
                    finish_reason,
                    len(content),
                )

                if content:
                    return content

                # Empty content — retry if attempts remain
                if finish_reason == "length":
                    logger.warning(
                        "Response truncated (max_tokens=%d). "
                        "Consider increasing LLM_MAX_TOKENS.",
                        self.max_tokens,
                    )

                logger.warning(
                    "Empty response from LLM (finish_reason=%s, attempt %d/%d)",
                    finish_reason,
                    attempt + 1,
                    self.max_retries + 1,
                )

            except OpenAIError as e:
                last_error = e
                logger.warning(
                    "LLM API error on attempt %d/%d: %s",
                    attempt + 1,
                    self.max_retries + 1,
                    e,
                )

            # Wait before retrying (skip delay on last attempt)
            if attempt < self.max_retries:
                delay = self.retry_delay * (self.retry_backoff**attempt)
                logger.info("Retrying in %.1fs...", delay)
                time.sleep(delay)

        if last_error:
            raise LLMError(
                f"LLM invocation failed after {self.max_retries + 1} attempts: "
                f"{last_error}"
            ) from last_error
        raise LLMError(
            f"LLM returned empty response after {self.max_retries + 1} attempts. "
            "Check model configuration and LLM_MAX_TOKENS."
        )

    def invoke_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        workspace: Path | None = None,
    ) -> str:
        """Send a message and execute tools until the LLM produces a final response.

        Implements an agentic loop:
        1. Send system + user message with tool definitions
        2. If LLM returns tool calls -> execute them -> feed results back
        3. Repeat until LLM returns a text response (no tool calls)

        Includes retry logic for empty responses and transient API errors.

        Args:
            system_prompt: The system-level instructions for the model.
            user_message: The user-level message/context for the model.
            workspace: Optional workspace root for tool execution.

        Returns:
            The model's final text response after all tool calls are resolved.

        Raises:
            LLMError: If the API call fails or max iterations exceeded.
        """
        if workspace:
            set_workspace(workspace)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        empty_response_retries = 0

        for iteration in range(MAX_TOOL_ITERATIONS):
            logger.debug(
                "Tool loop iteration %d/%d", iteration + 1, MAX_TOOL_ITERATIONS
            )

            response = self._api_call_with_retry(messages, use_tools=True)
            if not response or not response.choices:
                logger.warning(
                    "API returned empty response/choices at iteration %d. Retrying.",
                    iteration + 1,
                )
                empty_response_retries += 1
                if empty_response_retries > self.max_retries:
                    raise LLMError(
                        "LLM returned empty response/choices after "
                        f"{empty_response_retries} retries."
                    )
                delay = self.retry_delay * (self.retry_backoff**empty_response_retries)
                time.sleep(delay)
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You returned an empty response. "
                            "Please provide your complete answer or "
                            "continue using tools if needed."
                        ),
                    }
                )
                continue
            choice = response.choices[0]
            message = choice.message
            finish_reason = choice.finish_reason

            logger.debug(
                "Tool loop: iteration=%d, finish_reason=%s, "
                "content_len=%d, tool_calls=%s",
                iteration + 1,
                finish_reason,
                len(message.content or ""),
                bool(message.tool_calls),
            )

            # Handle truncated response (hit max_tokens)
            if finish_reason == "length" and not message.tool_calls:
                logger.warning(
                    "Response truncated at iteration %d (max_tokens=%d). "
                    "Asking model to continue.",
                    iteration + 1,
                    self.max_tokens,
                )
                # Append what we got and ask to continue
                if message.content:
                    messages.append({"role": "assistant", "content": message.content})
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Your response was truncated. "
                                "Please continue from where you left off."
                            ),
                        }
                    )
                    continue

            # If the model produced a final text response (no tool calls)
            if not message.tool_calls:
                content = message.content or ""

                # Handle empty response with retry
                if not content:
                    empty_response_retries += 1
                    if empty_response_retries <= self.max_retries:
                        delay = self.retry_delay * (
                            self.retry_backoff ** (empty_response_retries - 1)
                        )
                        logger.warning(
                            "Empty response (finish_reason=%s). "
                            "Retry %d/%d after %.1fs.",
                            finish_reason,
                            empty_response_retries,
                            self.max_retries,
                            delay,
                        )
                        time.sleep(delay)
                        # Nudge the model to produce output
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "You returned an empty response. "
                                    "Please provide your complete answer or "
                                    "continue using tools if needed."
                                ),
                            }
                        )
                        continue

                    raise LLMError(
                        f"LLM returned empty response after "
                        f"{empty_response_retries} retries "
                        f"(finish_reason={finish_reason}). "
                        f"Check model configuration and LLM_MAX_TOKENS."
                    )

                logger.info(
                    "Tool loop completed after %d iteration(s) "
                    "(response length: %d chars)",
                    iteration + 1,
                    len(content),
                )
                return content

            # Reset empty-response counter on successful tool-call iteration
            empty_response_retries = 0

            # Process tool calls
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            # Execute each tool call and append results
            for tool_call in message.tool_calls:
                tool_result = self._execute_single_tool(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

        raise LLMError(
            f"Tool loop exceeded maximum iterations ({MAX_TOOL_ITERATIONS}). "
            "The agent may be stuck in a loop."
        )

    def _api_call_with_retry(
        self,
        messages: list[dict[str, Any]],
        *,
        use_tools: bool = False,
    ) -> Any:
        """Make an API call with exponential backoff retry on transient errors.

        Args:
            messages: Conversation messages to send.
            use_tools: Whether to include tool schemas.

        Returns:
            The API response object.

        Raises:
            LLMError: If all retry attempts fail.
        """
        last_error: OpenAIError | None = None
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
        if use_tools:
            kwargs["tools"] = TOOL_SCHEMAS

        for attempt in range(self.max_retries + 1):
            try:
                return self._client.chat.completions.create(**kwargs)
            except OpenAIError as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = self.retry_delay * (self.retry_backoff**attempt)
                    logger.warning(
                        "API error (attempt %d/%d): %s. Retrying in %.1fs...",
                        attempt + 1,
                        self.max_retries + 1,
                        e,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "API error (attempt %d/%d): %s. No retries left.",
                        attempt + 1,
                        self.max_retries + 1,
                        e,
                    )

        raise LLMError(
            f"LLM API call failed after {self.max_retries + 1} attempts: {last_error}"
        ) from last_error

    def _execute_single_tool(self, tool_call: ChatCompletionMessageToolCall) -> str:
        """Execute a single tool call and return the result.

        Args:
            tool_call: The tool call from the LLM response.

        Returns:
            String result from tool execution.
        """
        name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError as e:
            # Attempt to repair truncated JSON (common with large write_file content)
            repaired = self._try_repair_tool_json(name, tool_call.function.arguments)
            if repaired is not None:
                arguments = repaired
                logger.warning("Repaired truncated JSON for tool '%s'", name)
            else:
                logger.error("Failed to parse tool arguments for '%s': %s", name, e)
                return (
                    f"Error: Invalid JSON in tool arguments: {e}. "
                    f"Your response was likely truncated. "
                    f"Please retry the write_file call with the complete content."
                )

        logger.info("Executing tool: %s(%s)", name, arguments)
        result = execute_tool_call(name, arguments)
        logger.debug("Tool '%s' result: %s", name, result[:200])
        return result

    @staticmethod
    def _try_repair_tool_json(tool_name: str, raw_args: str) -> dict[str, Any] | None:
        """Attempt to repair truncated JSON from tool call arguments.

        Handles the common case where write_file content is cut off mid-string
        due to token limits, resulting in an unterminated string.

        Args:
            tool_name: Name of the tool (only write_file is repaired).
            raw_args: The raw JSON string that failed to parse.

        Returns:
            Parsed arguments dict if repair succeeded, None otherwise.
        """
        if tool_name != "write_file":
            return None

        # Try closing the unterminated string and object
        # Common truncation: {"path": "...", "content": "some code...
        for suffix in ['"}', '\n"}', '"\n}']:
            try:
                repaired: dict[str, Any] = json.loads(raw_args + suffix)
                if "path" in repaired and "content" in repaired:
                    logger.info(
                        "JSON repair succeeded for write_file (appended %r)",
                        suffix,
                    )
                    return repaired
            except json.JSONDecodeError:
                continue

        return None


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
