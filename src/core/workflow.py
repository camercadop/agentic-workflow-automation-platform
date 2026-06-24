"""Workflow Graph Definition (ADR-007).

Defines workflows as directed acyclic graphs (DAGs) of plugin node references
with typed edges representing data flow between ports.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


class WorkflowNode(BaseModel):
    """A node in the workflow DAG referencing a registered plugin type."""

    node_id: str = Field(
        min_length=1,
        description="Unique identifier for this node within the workflow.",
    )
    plugin_name: str = Field(
        min_length=1,
        description="Name of the registered plugin this node references.",
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin-specific configuration for this node.",
    )


class WorkflowEdge(BaseModel):
    """A typed directed edge connecting an output port to an input port."""

    source_node: str = Field(
        min_length=1,
        description="Node ID of the edge's origin.",
    )
    source_port: str = Field(
        min_length=1,
        description="Output port name on the source node.",
    )
    target_node: str = Field(
        min_length=1,
        description="Node ID of the edge's destination.",
    )
    target_port: str = Field(
        min_length=1,
        description="Input port name on the target node.",
    )
    data_type: str = Field(
        default="any",
        description="Expected data type flowing through this edge.",
    )


class WorkflowDefinition(BaseModel):
    """A workflow defined as a validated DAG (ADR-007).

    Validates acyclicity and edge referential integrity on construction.
    """

    name: str = Field(
        min_length=1,
        description="Unique workflow name.",
    )
    version: str = Field(
        default="1.0.0",
        min_length=1,
        description="Semantic version of this workflow definition.",
    )
    nodes: list[WorkflowNode] = Field(
        min_length=1,
        description="Ordered list of nodes in the workflow DAG.",
    )
    edges: list[WorkflowEdge] = Field(
        default_factory=list,
        description="Directed edges defining data flow between nodes.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional workflow-level metadata.",
    )

    @model_validator(mode="after")
    def _validate_graph(self) -> WorkflowDefinition:
        node_ids = {n.node_id for n in self.nodes}

        # Validate edge references
        for edge in self.edges:
            if edge.source_node not in node_ids:
                raise ValueError(
                    f"Edge source '{edge.source_node}' not in nodes."
                )
            if edge.target_node not in node_ids:
                raise ValueError(
                    f"Edge target '{edge.target_node}' not in nodes."
                )

        # Validate acyclicity via topological sort (Kahn's algorithm)
        in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
        adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}
        for edge in self.edges:
            adjacency[edge.source_node].append(edge.target_node)
            in_degree[edge.target_node] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        visited = 0
        while queue:
            node = queue.pop()
            visited += 1
            for neighbor in adjacency[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited != len(node_ids):
            raise ValueError("Workflow graph contains a cycle.")

        return self
