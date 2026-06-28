"""Workflow Executor (ADR-006, ADR-007).

Executes a workflow DAG by topologically ordering nodes, provisioning
per-node execution contexts, and running plugin instances in isolation.
Applies per-node execution policies (retry, timeout, error handling).
"""

from __future__ import annotations

from typing import Any

from src.core.context import ContextManager
from src.core.contracts import (
    ActionPlugin,
    ConditionPlugin,
    PluginBase,
    TransformerPlugin,
    TriggerPlugin,
)
from src.core.policies import (
    ErrorStrategy,
    ExecutionPolicy,
    NodeExecutionError,
    NodeExecutionResult,
    PolicyExecutor,
    RetryPolicy,
    TimeoutPolicy,
)
from src.core.registry import LifecycleState, PluginRegistry
from src.core.workflow import WorkflowDefinition


class WorkflowExecutionError(Exception):
    """Raised when workflow execution fails."""


class WorkflowExecutor:
    """Executes a workflow DAG respecting isolation and dependencies.

    Implements the Routing Engine + Node Executor responsibilities:
        - Determines execution order via topological sort
        - Provisions isolated execution contexts per node
        - Materializes plugin instances and executes them
        - Applies execution policies (retry, timeout, error strategy)
    """

    def __init__(
        self,
        registry: PluginRegistry,
        context_manager: ContextManager,
    ) -> None:
        """Initialize executor with registry and context manager."""
        self._registry = registry
        self._context_manager = context_manager

    def execute(
        self,
        workflow: WorkflowDefinition,
        initial_data: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Execute a workflow and return results keyed by node ID.

        Args:
            workflow: The workflow definition to execute.
            initial_data: Optional seed data for root nodes.

        Returns:
            A dict mapping node IDs to their execution output dicts.

        Raises:
            WorkflowExecutionError: On plugin lookup or execution failure
                (when error strategy is FAIL_FAST).
        """
        order = self._topological_order(workflow)
        results: dict[str, dict[str, Any]] = {}
        pruned: set[str] = set()
        node_inputs = self._build_node_inputs(workflow, results, initial_data or {})

        for node_id in order:
            if node_id in pruned:
                continue

            node = next(n for n in workflow.nodes if n.node_id == node_id)
            plugin_entry = self._resolve_plugin(node.plugin_name)
            plugin = plugin_entry.plugin
            data = node_inputs.get(node_id, initial_data or {})
            policy = self._build_policy(node.config)

            # Provision isolated execution context (ADR-006)
            ctx = self._context_manager.provision(plugin.manifest)
            try:
                node_result = PolicyExecutor.run(
                    fn=lambda p=plugin, d=data: self._execute_plugin(p, d),
                    policy=policy,
                    node_id=node_id,
                )
                self._handle_result(node_result, policy)
                if node_result.success:
                    results[node_id] = node_result.data

                # Branch pruning for condition nodes
                if node_result.success and isinstance(plugin, ConditionPlugin):
                    pruned.update(
                        self._prune_branches(workflow, node_id, node_result.data)
                    )

                # Refresh inputs for downstream nodes
                node_inputs = self._build_node_inputs(
                    workflow, results, initial_data or {}
                )
            finally:
                self._context_manager.destroy(ctx.context_id)

        return results

    def _prune_branches(
        self,
        workflow: WorkflowDefinition,
        condition_node_id: str,
        result_data: dict[str, Any],
    ) -> set[str]:
        """Determine which downstream nodes to prune based on condition result.

        Only prunes when outgoing edges have condition labels. Nodes reachable
        through non-pruned paths are preserved.

        Args:
            workflow: The workflow definition.
            condition_node_id: The condition node that was just evaluated.
            result_data: The condition node's output (expects 'result' key).

        Returns:
            Set of node IDs to skip.
        """
        condition_result = result_data.get("result", True)
        outcome = "true" if condition_result else "false"

        outgoing = [e for e in workflow.edges if e.source_node == condition_node_id]
        # Only apply pruning if edges have condition labels
        labeled = [e for e in outgoing if e.condition is not None]
        if not labeled:
            return set()

        # Find nodes on the pruned branch
        pruned_targets = {e.target_node for e in labeled if e.condition != outcome}
        # Find nodes on the active branch
        active_targets = {e.target_node for e in labeled if e.condition == outcome}
        # Also include unlabeled edges as always-active
        active_targets.update(e.target_node for e in outgoing if e.condition is None)

        # Expand pruned set: collect all nodes reachable exclusively from pruned targets
        all_node_ids = {n.node_id for n in workflow.nodes}
        adjacency: dict[str, set[str]] = {nid: set() for nid in all_node_ids}
        incoming: dict[str, set[str]] = {nid: set() for nid in all_node_ids}
        for edge in workflow.edges:
            adjacency[edge.source_node].add(edge.target_node)
            incoming[edge.target_node].add(edge.source_node)

        pruned: set[str] = set()
        queue = list(pruned_targets - active_targets)
        while queue:
            nid = queue.pop()
            # A node is pruned only if ALL its incoming sources are pruned or
            # the condition node itself (for direct targets)
            sources = incoming[nid]
            all_sources_pruned = all(
                s in pruned or s == condition_node_id for s in sources
            )
            if not all_sources_pruned:
                continue
            pruned.add(nid)
            for child in adjacency[nid]:
                if child not in pruned:
                    queue.append(child)

        return pruned

    def _build_policy(self, config: dict[str, Any]) -> ExecutionPolicy:
        """Extract execution policy from node config, falling back to defaults.

        Args:
            config: Node configuration dict, may contain a "policy" key.

        Returns:
            The resolved ExecutionPolicy.
        """
        policy_cfg = config.get("policy", {})
        if not policy_cfg:
            return ExecutionPolicy()

        retry_cfg = policy_cfg.get("retry", {})
        timeout_cfg = policy_cfg.get("timeout", {})
        error_strategy = policy_cfg.get("error_strategy", ErrorStrategy.FAIL_FAST)

        return ExecutionPolicy(
            retry=RetryPolicy(
                max_attempts=retry_cfg.get("max_attempts", 1),
                delay_seconds=retry_cfg.get("delay_seconds", 0.0),
                backoff_factor=retry_cfg.get("backoff_factor", 2.0),
            ),
            timeout=TimeoutPolicy(
                timeout_seconds=timeout_cfg.get("timeout_seconds", 30.0),
            ),
            error_strategy=ErrorStrategy(error_strategy),
        )

    def _handle_result(
        self, result: NodeExecutionResult, policy: ExecutionPolicy
    ) -> None:
        """Apply the error strategy to a failed node result.

        Args:
            result: The execution result for a node.
            policy: The execution policy governing error handling.

        Raises:
            NodeExecutionError: When strategy is FAIL_FAST and the node failed.
        """
        if result.success:
            return

        if policy.error_strategy == ErrorStrategy.FAIL_FAST:
            raise NodeExecutionError(result.node_id, result.error or "Unknown")
        # SKIP_NODE and CONTINUE both allow the workflow to proceed
        result.skipped = policy.error_strategy == ErrorStrategy.SKIP_NODE

    def _resolve_plugin(self, plugin_name: str) -> Any:
        """Resolve a plugin from the registry; must be Active.

        Args:
            plugin_name: The registered name of the plugin.

        Returns:
            The registry entry for the plugin.

        Raises:
            WorkflowExecutionError: If the plugin is not in ACTIVE state.
        """
        entry = self._registry.get(plugin_name)
        if entry.state != LifecycleState.ACTIVE:
            raise WorkflowExecutionError(
                f"Plugin '{plugin_name}' is not active (state: {entry.state})."
            )
        return entry

    def _execute_plugin(
        self,
        plugin: PluginBase,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a plugin based on its contract type.

        Args:
            plugin: The plugin instance to execute.
            data: Input data for the plugin.

        Returns:
            The plugin's output as a dict.

        Raises:
            WorkflowExecutionError: If the plugin type is unknown.
        """
        if isinstance(plugin, TriggerPlugin):
            return plugin.check()
        if isinstance(plugin, ConditionPlugin):
            return {"result": plugin.evaluate(data)}
        if isinstance(plugin, TransformerPlugin):
            return plugin.transform(data)
        if isinstance(plugin, ActionPlugin):
            return plugin.execute(data)

        raise WorkflowExecutionError(f"Unknown plugin type: {type(plugin).__name__}")

    def _topological_order(self, workflow: WorkflowDefinition) -> list[str]:
        """Sort nodes so each one runs after all its dependencies (Kahn's algorithm).

        Starts with nodes that have no incoming edges, then repeatedly
        removes them from the graph and adds newly-unblocked nodes
        until all nodes are ordered.

        Args:
            workflow: The workflow definition containing nodes and edges.

        Returns:
            Node IDs in topological execution order.
        """
        node_ids = [n.node_id for n in workflow.nodes]
        in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
        adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}

        for edge in workflow.edges:
            adjacency[edge.source_node].append(edge.target_node)
            in_degree[edge.target_node] += 1

        queue = [nid for nid in node_ids if in_degree[nid] == 0]
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def _build_node_inputs(
        self,
        workflow: WorkflowDefinition,
        results: dict[str, dict[str, Any]],
        initial_data: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        """Map upstream outputs to downstream inputs via edges.

        Args:
            workflow: The workflow definition.
            results: Already-computed node results.
            initial_data: Seed data for root nodes.

        Returns:
            A dict mapping node IDs to their resolved input dicts.
        """
        inputs: dict[str, dict[str, Any]] = {}
        for edge in workflow.edges:
            source_result = results.get(edge.source_node)
            if source_result is None:
                continue
            target_data = inputs.setdefault(edge.target_node, {})
            value = source_result.get(edge.source_port, source_result)
            target_data[edge.target_port] = value

        # Nodes with no incoming edges get initial_data
        nodes_with_input = {e.target_node for e in workflow.edges}
        for node in workflow.nodes:
            if node.node_id not in nodes_with_input:
                inputs.setdefault(node.node_id, initial_data)

        return inputs
