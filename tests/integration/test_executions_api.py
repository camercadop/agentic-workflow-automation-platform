"""Integration tests for execution API endpoints."""

from fastapi.testclient import TestClient

from tests.integration.helpers import (
    assert_create_and_get,
    assert_delete,
    assert_delete_not_found,
    assert_invalid_body,
    assert_list_empty,
    assert_not_found,
)

PATH = "/executions/"
VALID_PAYLOAD = {"workflow_id": "wf-001", "context": {"input": "data"}}


def test_list_executions_empty(client: TestClient) -> None:
    assert_list_empty(client, PATH)


def test_create_and_get_execution(client: TestClient) -> None:
    data = assert_create_and_get(
        client, PATH, VALID_PAYLOAD, lookup_field="workflow_id", lookup_value="wf-001"
    )
    assert data["status"] == "pending"
    assert data["context"] == {"input": "data"}
    assert data["context_version"] == 1


def test_update_execution(client: TestClient) -> None:
    create_resp = client.post(PATH, json=VALID_PAYLOAD)
    execution_id = create_resp.json()["id"]

    resp = client.patch(f"/executions/{execution_id}", json={"status": "running"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "running"


def test_update_execution_not_found(client: TestClient) -> None:
    assert_not_found(client, "/executions")


def test_delete_execution(client: TestClient) -> None:
    assert_delete(client, PATH, VALID_PAYLOAD)


def test_delete_execution_not_found(client: TestClient) -> None:
    assert_delete_not_found(client, "/executions")


def test_get_execution_not_found(client: TestClient) -> None:
    assert_not_found(client, "/executions")


def test_create_execution_invalid_body(client: TestClient) -> None:
    assert_invalid_body(client, PATH)
