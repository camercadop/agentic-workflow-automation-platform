"""Tests for the Governance & Validation Framework (ADR-009)."""

from typing import Any

from src.core.contracts import ActionPlugin, TriggerPlugin
from src.core.manifest import PluginManifest, PluginType, PortSchema
from src.core.workflow import WorkflowDefinition, WorkflowEdge, WorkflowNode
from src.governance.engine import ValidationEngine
from src.governance.gates import (
    ContractValidationGate,
    ExecutionContextValidationGate,
    ManifestValidationGate,
    SecurityValidationGate,
    WorkflowValidationGate,
)

# --- Test Fixtures ---


class ValidAction(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="valid-action",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            permissions=["network:example.com"],
            inputs=[PortSchema(name="payload", data_type="dict")],
            outputs=[PortSchema(name="result", data_type="dict")],
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True}


class ValidTrigger(TriggerPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="valid-trigger",
            version="2.0.0",
            plugin_type=PluginType.TRIGGER,
            outputs=[PortSchema(name="payload", data_type="dict")],
        )

    def check(self) -> dict[str, Any]:
        return {"fired": True}


class BadVersionPlugin(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="bad-version",
            version="not-semver",
            plugin_type=PluginType.ACTION,
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {}


class WrongContractPlugin(TriggerPlugin):
    """Declares CONDITION type but subclasses TriggerPlugin."""

    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="wrong-contract",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
        )

    def check(self) -> dict[str, Any]:
        return {}


class BadPermissionsPlugin(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="bad-perms",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            permissions=["no-colon", "network:x", "network:x"],
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {}


class BadResourcePlugin(ActionPlugin):
    @property
    def manifest(self) -> PluginManifest:
        return PluginManifest(
            name="bad-resources",
            version="1.0.0",
            plugin_type=PluginType.ACTION,
            metadata={
                "resource_requirements": {
                    "max_memory_mb": -10,
                    "max_threads": 0,
                },
            },
        )

    def execute(self, data: dict[str, Any]) -> dict[str, Any]:
        return {}


# --- Manifest Validation Gate ---


class TestManifestValidationGate:
    def setup_method(self) -> None:
        self.gate = ManifestValidationGate()

    def test_valid_plugin_passes(self) -> None:
        assert self.gate.validate_plugin(ValidAction()) == []

    def test_invalid_version_fails(self) -> None:
        errors = self.gate.validate_plugin(BadVersionPlugin())
        assert any("semver" in e for e in errors)


# --- Contract Validation Gate ---


class TestContractValidationGate:
    def setup_method(self) -> None:
        self.gate = ContractValidationGate()

    def test_valid_plugin_passes(self) -> None:
        assert self.gate.validate_plugin(ValidAction()) == []

    def test_wrong_contract_type_fails(self) -> None:
        errors = self.gate.validate_plugin(WrongContractPlugin())
        assert any("subclass" in e.lower() for e in errors)


# --- Security Validation Gate ---


class TestSecurityValidationGate:
    def setup_method(self) -> None:
        self.gate = SecurityValidationGate()

    def test_valid_permissions_pass(self) -> None:
        assert self.gate.validate_plugin(ValidAction()) == []

    def test_invalid_permission_format(self) -> None:
        errors = self.gate.validate_plugin(BadPermissionsPlugin())
        assert any("scope:resource" in e for e in errors)

    def test_duplicate_permissions(self) -> None:
        errors = self.gate.validate_plugin(BadPermissionsPlugin())
        assert any("duplicate" in e.lower() for e in errors)


# --- Execution Context Validation Gate ---


class TestExecutionContextValidationGate:
    def setup_method(self) -> None:
        self.gate = ExecutionContextValidationGate()

    def test_no_resources_passes(self) -> None:
        assert self.gate.validate_plugin(ValidAction()) == []

    def test_invalid_resources_fail(self) -> None:
        errors = self.gate.validate_plugin(BadResourcePlugin())
        assert len(errors) == 2
        assert any("max_memory_mb" in e for e in errors)
        assert any("max_threads" in e for e in errors)

    def test_valid_resources_pass(self) -> None:
        class GoodResources(ActionPlugin):
            @property
            def manifest(self) -> PluginManifest:
                return PluginManifest(
                    name="good-res",
                    version="1.0.0",
                    plugin_type=PluginType.ACTION,
                    metadata={
                        "resource_requirements": {
                            "max_memory_mb": 512,
                            "max_threads": 4,
                        },
                    },
                )

            def execute(self, data: dict[str, Any]) -> dict[str, Any]:
                return {}

        assert self.gate.validate_plugin(GoodResources()) == []


# --- Workflow Validation Gate ---


class TestWorkflowValidationGate:
    def setup_method(self) -> None:
        self.gate = WorkflowValidationGate()
        self.plugins: dict[str, Any] = {
            "valid-trigger": ValidTrigger(),
            "valid-action": ValidAction(),
        }

    def test_valid_workflow_passes(self) -> None:
        wf = WorkflowDefinition(
            name="test-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="valid-trigger"),
                WorkflowNode(node_id="a", plugin_name="valid-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="payload",
                ),
            ],
        )
        errors = self.gate.validate_workflow(wf, self.plugins)
        assert errors == []

    def test_unregistered_plugin_fails(self) -> None:
        wf = WorkflowDefinition(
            name="bad-wf",
            nodes=[WorkflowNode(node_id="x", plugin_name="nonexistent")],
        )
        errors = self.gate.validate_workflow(wf, self.plugins)
        assert any("unregistered" in e.lower() for e in errors)

    def test_invalid_port_fails(self) -> None:
        wf = WorkflowDefinition(
            name="port-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="valid-trigger"),
                WorkflowNode(node_id="a", plugin_name="valid-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="nonexistent-port",
                    target_node="a",
                    target_port="payload",
                ),
            ],
        )
        errors = self.gate.validate_workflow(wf, self.plugins)
        assert any("nonexistent-port" in e for e in errors)


# --- Validation Engine ---


class TestValidationEngine:
    def test_valid_plugin_report_passes(self) -> None:
        engine = ValidationEngine()
        report = engine.validate_plugin(ValidAction())
        assert report.passed is True
        assert report.errors == []

    def test_invalid_plugin_report_fails(self) -> None:
        engine = ValidationEngine()
        report = engine.validate_plugin(WrongContractPlugin())
        assert report.passed is False
        assert len(report.errors) > 0

    def test_all_gates_always_run(self) -> None:
        engine = ValidationEngine()
        report = engine.validate_plugin(BadPermissionsPlugin())
        gate_names = [gr.gate_name for gr in report.gate_results]
        assert "Manifest Validation Gate" in gate_names
        assert "Contract Validation Gate" in gate_names
        assert "Security Validation Gate" in gate_names
        assert "Execution Context Validation Gate" in gate_names

    def test_workflow_validation(self) -> None:
        engine = ValidationEngine()
        plugins = {"valid-trigger": ValidTrigger(), "valid-action": ValidAction()}
        wf = WorkflowDefinition(
            name="engine-wf",
            nodes=[
                WorkflowNode(node_id="t", plugin_name="valid-trigger"),
                WorkflowNode(node_id="a", plugin_name="valid-action"),
            ],
            edges=[
                WorkflowEdge(
                    source_node="t",
                    source_port="payload",
                    target_node="a",
                    target_port="payload",
                ),
            ],
        )
        report = engine.validate_workflow(wf, plugins)
        assert report.passed is True
