"""Unit tests for workflow graph definition (ADR-007)."""

import pytest
from pydantic import ValidationError
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode


class TestWorkflowDefinitionValid:
    def test_single_node_no_edges(self) -> None:
        wf = WorkflowDefinition(
            name="simple",
            nodes=[WorkflowNode(node_id="a", plugin_name="plugin-a")],
        )
        assert len(wf.nodes) == 1
        assert wf.edges == []

    def test_linear_pipeline(self) -> None:
        wf = WorkflowDefinition(
            name="linear",
            nodes=[
                WorkflowNode(node_id="a", plugin_name="trigger"),
                WorkflowNode(node_id="b", plugin_name="action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="a",
                    source_port="out",
                    target_node="b",
                    target_port="in",
                ),
            ],
        )
        assert len(wf.edges) == 1

    def test_branching_dag(self) -> None:
        wf = WorkflowDefinition(
            name="branch",
            nodes=[
                WorkflowNode(node_id="a", plugin_name="trigger"),
                WorkflowNode(node_id="b", plugin_name="cond"),
                WorkflowNode(node_id="c", plugin_name="action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="a",
                    source_port="out",
                    target_node="b",
                    target_port="in",
                ),
                WorkflowEdge(
                    source_node="a",
                    source_port="out",
                    target_node="c",
                    target_port="in",
                ),
            ],
        )
        assert len(wf.nodes) == 3

    def test_metadata_and_version(self) -> None:
        wf = WorkflowDefinition(
            name="versioned",
            version="2.1.0",
            nodes=[WorkflowNode(node_id="a", plugin_name="p")],
            metadata={"author": "test"},
        )
        assert wf.version == "2.1.0"
        assert wf.metadata["author"] == "test"


class TestWorkflowDefinitionInvalid:
    def test_cycle_detected(self) -> None:
        with pytest.raises(ValidationError, match="cycle"):
            WorkflowDefinition(
                name="cyclic",
                nodes=[
                    WorkflowNode(node_id="a", plugin_name="p"),
                    WorkflowNode(node_id="b", plugin_name="p"),
                ],
                edges=[
                    WorkflowEdge(
                        source_node="a",
                        source_port="out",
                        target_node="b",
                        target_port="in",
                    ),
                    WorkflowEdge(
                        source_node="b",
                        source_port="out",
                        target_node="a",
                        target_port="in",
                    ),
                ],
            )

    def test_edge_references_unknown_source(self) -> None:
        with pytest.raises(ValidationError, match="source"):
            WorkflowDefinition(
                name="bad-src",
                nodes=[WorkflowNode(node_id="a", plugin_name="p")],
                edges=[
                    WorkflowEdge(
                        source_node="ghost",
                        source_port="out",
                        target_node="a",
                        target_port="in",
                    ),
                ],
            )

    def test_edge_references_unknown_target(self) -> None:
        with pytest.raises(ValidationError, match="target"):
            WorkflowDefinition(
                name="bad-tgt",
                nodes=[WorkflowNode(node_id="a", plugin_name="p")],
                edges=[
                    WorkflowEdge(
                        source_node="a",
                        source_port="out",
                        target_node="ghost",
                        target_port="in",
                    ),
                ],
            )

    def test_empty_nodes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowDefinition(name="empty", nodes=[])

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            WorkflowDefinition(
                name="",
                nodes=[WorkflowNode(node_id="a", plugin_name="p")],
            )
