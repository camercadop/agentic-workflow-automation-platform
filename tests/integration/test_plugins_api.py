"""Integration tests for plugin API endpoints."""

from fastapi.testclient import TestClient

from tests.integration.helpers import (
    assert_create_and_get,
    assert_invalid_body,
    assert_list_empty,
    assert_not_found,
)

PATH = "/plugins/"


def test_list_plugins_empty(client: TestClient) -> None:
    assert_list_empty(client, PATH)


def test_create_and_get_plugin(client: TestClient) -> None:
    payload = {
        "name": "test-plugin",
        "version": "1.0.0",
        "plugin_type": "action",
        "manifest": {"key": "value"},
    }
    data = assert_create_and_get(
        client, PATH, payload, lookup_field="name", lookup_value="test-plugin"
    )
    assert data["version"] == "1.0.0"
    assert data["plugin_type"] == "action"
    assert data["lifecycle_state"] == "registered"
    assert data["manifest"] == {"key": "value"}


def test_get_plugin_not_found(client: TestClient) -> None:
    assert_not_found(client, "/plugins")


def test_create_plugin_invalid_body(client: TestClient) -> None:
    assert_invalid_body(client, PATH)
