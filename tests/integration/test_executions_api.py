"""Integration tests for execution API endpoints."""

from fastapi.testclient import TestClient

from tests.integration.helpers import (
    assert_create_and_get,
    assert_invalid_body,
    assert_list_empty,
    assert_not_found,
)

PATH = "/executions/"


def test_list_executions_empty(client: TestClient) -> None:
    assert_list_empty(client, PATH)


def test_create_and_get_execution(client: TestClient) -> None:
    payload = {"workflow_id": "wf-001", "context": {"input": "data"}}
    data = assert_create_and_get(
        client, PATH, payload, lookup_field="workflow_id", lookup_value="wf-001"
    )
    assert data["status"] == "pending"
    assert data["context"] == {"input": "data"}
    assert data["context_version"] == 1


def test_get_execution_not_found(client: TestClient) -> None:
    assert_not_found(client, "/executions")


def test_create_execution_invalid_body(client: TestClient) -> None:
    assert_invalid_body(client, PATH)
