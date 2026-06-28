"""Shared test helpers for API integration tests."""

from typing import Any

from fastapi.testclient import TestClient

NOT_FOUND_ID = "00000000-0000-0000-0000-000000000000"


def assert_not_found(client: TestClient, path: str) -> None:
    response = client.get(f"{path}/{NOT_FOUND_ID}")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "RESOURCE_NOT_FOUND"


def assert_invalid_body(client: TestClient, path: str) -> None:
    response = client.post(path, json={})
    assert response.status_code == 422


def assert_list_empty(client: TestClient, path: str) -> None:
    response = client.get(path)
    assert response.status_code == 200
    assert response.json() == []


def assert_create_and_get(
    client: TestClient,
    path: str,
    payload: dict[str, Any],
    id_field: str = "id",
    lookup_field: str | None = None,
    lookup_value: Any = None,
) -> dict[str, Any]:
    """Create a resource and verify it can be fetched by ID."""
    create_resp = client.post(path, json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data[id_field] is not None

    get_resp = client.get(f"{path.rstrip('/')}/{data[id_field]}")
    assert get_resp.status_code == 200
    if lookup_field and lookup_value is not None:
        assert get_resp.json()[lookup_field] == lookup_value

    return data


def assert_delete(client: TestClient, path: str, payload: dict[str, Any]) -> None:
    """Create a resource, delete it, and verify it's gone."""
    create_resp = client.post(path, json=payload)
    entity_id = create_resp.json()["id"]

    delete_resp = client.delete(f"{path.rstrip('/')}/{entity_id}")
    assert delete_resp.status_code == 204

    get_resp = client.get(f"{path.rstrip('/')}/{entity_id}")
    assert get_resp.status_code == 404


def assert_delete_not_found(client: TestClient, path: str) -> None:
    response = client.delete(f"{path}/{NOT_FOUND_ID}")
    assert response.status_code == 404
    detail = response.json()["detail"]
    assert detail["code"] == "RESOURCE_NOT_FOUND"
