"""Workflow Executor (ADR-006, ADR-007).

Executes a workflow DAG by topologically ordering nodes, provisioning
per-node execution contexts, and running plugin instances in isolation.
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
    """

    def __init__(
        self,
        registry: PluginRegistry,
        context_manager: ContextManager,
    ) -> None:
        self._registry = registry
        self._context_manager = context_manager

    def execute(
        self,
        workflow: WorkflowDefinition,
        initial_data: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Execute a workflow and return results keyed by node ID.

        Raises WorkflowExecutionError on plugin lookup or execution failure.
        """
        order = self._topological_order(workflow)
        results: dict[str, dict[str, Any]] = {}
        node_inputs = self._build_node_inputs(
            workflow, results, initial_data or {}
        )

        for node_id in order:
            node = next(n for n in workflow.nodes if n.node_id == node_id)
            plugin_entry = self._resolve_plugin(node.plugin_name)
            plugin = plugin_entry.plugin
            data = node_inputs.get(node_id, initial_data or {})

            # Provision isolated execution context (ADR-006)
            ctx = self._context_manager.provision(plugin.manifest)
            try:
                result = self._execute_plugin(plugin, data)
                results[node_id] = result
                # Refresh inputs for downstream nodes
                node_inputs = self._build_node_inputs(
                    workflow, results, initial_data or {}
                )
            finally:
                self._context_manager.destroy(ctx.context_id)

        return results

    def _resolve_plugin(self, plugin_name: str) -> Any:
        """Resolve a plugin from the registry; must be Active."""
        entry = self._registry.get(plugin_name)
        if entry.state != LifecycleState.ACTIVE:
            raise WorkflowExecutionError(
                f"Plugin '{plugin_name}' is not active "
                f"(state: {entry.state})."
            )
        return entry

    def _execute_plugin(
        self,
        plugin: PluginBase,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a plugin based on its contract type."""
        if isinstance(plugin, TriggerPlugin):
            return plugin.check()
        if isinstance(plugin, ConditionPlugin):
            return {"result": plugin.evaluate(data)}
        if isinstance(plugin, TransformerPlugin):
            return plugin.transform(data)
        if isinstance(plugin, ActionPlugin):
            return plugin.execute(data)
        raise WorkflowExecutionError(
            f"Unknown plugin type: {type(plugin).__name__}"
        )

    def _topological_order(
        self, workflow: WorkflowDefinition
    ) -> list[str]:
        """Compute topological execution order from the DAG."""
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
        """Map upstream outputs to downstream inputs via edges."""
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
