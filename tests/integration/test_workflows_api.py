"""Integration tests for workflow API endpoints."""

from fastapi.testclient import TestClient

from tests.integration.helpers import NOT_FOUND_ID

VALID_WORKFLOW = {
    "name": "test-workflow",
    "nodes": [
        {"node_id": "trigger", "plugin_name": "manual-trigger"},
        {"node_id": "action", "plugin_name": "log-action"},
    ],
    "edges": [
        {
            "source_node": "trigger",
            "source_port": "payload",
            "target_node": "action",
            "target_port": "data",
        }
    ],
}


def test_list_workflows_empty(client: TestClient) -> None:
    resp = client.get("/workflows/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_workflow(client: TestClient) -> None:
    resp = client.post("/workflows/", json=VALID_WORKFLOW)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "test-workflow"
    assert len(data["nodes"]) == 2
    assert len(data["edges"]) == 1


def test_get_workflow(client: TestClient) -> None:
    create_resp = client.post("/workflows/", json=VALID_WORKFLOW)
    wf_id = create_resp.json()["id"]

    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "test-workflow"


def test_get_workflow_not_found(client: TestClient) -> None:
    resp = client.get(f"/workflows/{NOT_FOUND_ID}")
    assert resp.status_code == 404


def test_update_workflow(client: TestClient) -> None:
    create_resp = client.post("/workflows/", json=VALID_WORKFLOW)
    wf_id = create_resp.json()["id"]

    resp = client.patch(f"/workflows/{wf_id}", json={"version": "2.0.0"})
    assert resp.status_code == 200
    assert resp.json()["version"] == "2.0.0"


def test_update_workflow_not_found(client: TestClient) -> None:
    resp = client.patch(f"/workflows/{NOT_FOUND_ID}", json={"version": "2.0.0"})
    assert resp.status_code == 404


def test_delete_workflow(client: TestClient) -> None:
    create_resp = client.post("/workflows/", json=VALID_WORKFLOW)
    wf_id = create_resp.json()["id"]

    resp = client.delete(f"/workflows/{wf_id}")
    assert resp.status_code == 204

    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 404


def test_delete_workflow_not_found(client: TestClient) -> None:
    resp = client.delete(f"/workflows/{NOT_FOUND_ID}")
    assert resp.status_code == 404


def test_execute_workflow(client: TestClient) -> None:
    create_resp = client.post("/workflows/", json=VALID_WORKFLOW)
    wf_id = create_resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/execute", json={"initial_data": {"msg": "hello"}}
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["workflow_id"] == wf_id
    assert data["status"] == "completed"
    assert "results" in data


def test_execute_workflow_not_found(client: TestClient) -> None:
    resp = client.post(f"/workflows/{NOT_FOUND_ID}/execute", json={"initial_data": {}})
    assert resp.status_code == 404


def test_create_workflow_invalid_body(client: TestClient) -> None:
    resp = client.post("/workflows/", json={})
    assert resp.status_code == 422


def test_create_workflow_invalid_dag(client: TestClient) -> None:
    """Workflow with edge referencing non-existent node should fail."""
    payload = {
        "name": "bad-dag",
        "nodes": [{"node_id": "trigger", "plugin_name": "manual-trigger"}],
        "edges": [
            {
                "source_node": "trigger",
                "source_port": "out",
                "target_node": "nonexistent",
                "target_port": "in",
            }
        ],
    }
    resp = client.post("/workflows/", json=payload)
    # ValueError from WorkflowDefinition is caught by value_error_handler -> 404
    assert resp.status_code in (400, 404, 422)
