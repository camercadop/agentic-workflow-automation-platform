"""Integration tests for plugin API endpoints."""

from fastapi.testclient import TestClient

from tests.integration.helpers import (
    assert_create_and_get,
    assert_delete,
    assert_delete_not_found,
    assert_invalid_body,
    assert_list_empty,
    assert_not_found,
)

PATH = "/plugins/"
VALID_PAYLOAD = {"name": "test-plugin", "version": "1.0.0", "plugin_type": "action"}


def test_list_plugins_empty(client: TestClient) -> None:
    assert_list_empty(client, PATH)


def test_create_and_get_plugin(client: TestClient) -> None:
    payload = {**VALID_PAYLOAD, "manifest": {"key": "value"}}
    data = assert_create_and_get(
        client, PATH, payload, lookup_field="name", lookup_value="test-plugin"
    )
    assert data["version"] == "1.0.0"
    assert data["plugin_type"] == "action"
    assert data["lifecycle_state"] == "registered"
    assert data["manifest"] == {"key": "value"}


def test_update_plugin(client: TestClient) -> None:
    create_resp = client.post(PATH, json=VALID_PAYLOAD)
    plugin_id = create_resp.json()["id"]

    resp = client.patch(f"/plugins/{plugin_id}", json={"lifecycle_state": "activated"})
    assert resp.status_code == 200
    assert resp.json()["lifecycle_state"] == "activated"


def test_update_plugin_not_found(client: TestClient) -> None:
    assert_not_found(client, "/plugins")


def test_delete_plugin(client: TestClient) -> None:
    assert_delete(client, PATH, VALID_PAYLOAD)


def test_delete_plugin_not_found(client: TestClient) -> None:
    assert_delete_not_found(client, "/plugins")


def test_get_plugin_not_found(client: TestClient) -> None:
    assert_not_found(client, "/plugins")


def test_create_plugin_invalid_body(client: TestClient) -> None:
    assert_invalid_body(client, PATH)


def test_create_plugin_duplicate_name(client: TestClient) -> None:
    client.post(PATH, json=VALID_PAYLOAD)
    resp = client.post(PATH, json=VALID_PAYLOAD)
    assert resp.status_code == 409
    detail = resp.json()["detail"]
    assert detail["code"] == "RESOURCE_ALREADY_EXISTS"
