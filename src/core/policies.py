"""Execution policies for workflow node resilience.

Provides configurable retry, timeout, and error handling strategies
that the WorkflowExecutor applies per-node during DAG execution.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ErrorStrategy(StrEnum):
    """Determines workflow behavior when a node execution fails."""

    FAIL_FAST = "fail_fast"
    SKIP_NODE = "skip_node"
    CONTINUE = "continue"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Per-node retry configuration."""

    max_attempts: int = 1
    delay_seconds: float = 0.0
    backoff_factor: float = 2.0


@dataclass(frozen=True, slots=True)
class TimeoutPolicy:
    """Per-node timeout configuration."""

    timeout_seconds: float = 30.0


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Combined execution policy for a workflow node."""

    retry: RetryPolicy = field(default_factory=RetryPolicy)
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    error_strategy: ErrorStrategy = ErrorStrategy.FAIL_FAST


@dataclass(slots=True)
class NodeExecutionResult:
    """Result of a single node execution including policy outcomes."""

    node_id: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempts: int = 1
    skipped: bool = False


class NodeExecutionError(Exception):
    """Raised when a node fails and error strategy is FAIL_FAST."""

    def __init__(self, node_id: str, message: str) -> None:
        """Initialize with node ID and error message.

        Args:
            node_id: The ID of the failed node.
            message: Description of the failure.
        """
        self.node_id = node_id
        super().__init__(f"Node '{node_id}' failed: {message}")


class PolicyExecutor:
    """Applies execution policies (retry, timeout) to a callable.

    Used by the WorkflowExecutor to wrap individual plugin calls.
    """

    _pool = ThreadPoolExecutor(max_workers=4)

    @classmethod
    def run(
        cls,
        fn: Any,
        policy: ExecutionPolicy,
        node_id: str,
    ) -> NodeExecutionResult:
        """Execute fn with retry and timeout policies applied.

        Args:
            fn: The callable to execute.
            policy: The execution policy to apply.
            node_id: The node ID for result tracking.

        Returns:
            The execution result with success/failure and attempt count.
        """
        last_error: str = ""

        for attempt in range(1, policy.retry.max_attempts + 1):
            try:
                future = cls._pool.submit(fn)
                result = future.result(timeout=policy.timeout.timeout_seconds)

                return NodeExecutionResult(
                    node_id=node_id,
                    success=True,
                    data=result,
                    attempts=attempt,
                )
            except FuturesTimeout:
                last_error = f"Timed out after {policy.timeout.timeout_seconds}s"
                future.cancel()
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)

            # Wait before retry (skip delay on last attempt)
            if attempt < policy.retry.max_attempts:
                delay = policy.retry.delay_seconds * (
                    policy.retry.backoff_factor ** (attempt - 1)
                )
                if delay > 0:
                    time.sleep(delay)

        return NodeExecutionResult(
            node_id=node_id,
            success=False,
            error=last_error,
            attempts=policy.retry.max_attempts,
        )
