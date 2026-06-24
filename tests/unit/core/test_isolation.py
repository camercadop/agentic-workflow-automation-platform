from src.core.isolation import DefaultIsolationService, PolicyIsolationService
from src.core.manifest import PluginManifest, PluginType


def _make_manifest(permissions: list[str] | None = None) -> PluginManifest:
    return PluginManifest(
        name="test-plugin",
        version="1.0.0",
        plugin_type=PluginType.ACTION,
        permissions=permissions or [],
    )


class TestPolicyIsolationService:
    def test_allow_declared_permissions(self) -> None:
        svc = PolicyIsolationService()
        manifest = _make_manifest(["file:/tmp/data", "network:api.example.com"])
        assert svc.authorize(manifest, ["file:/tmp/data"]) is True
        assert svc.authorize(manifest, ["network:api.example.com"]) is True
        assert (
            svc.authorize(manifest, ["file:/tmp/data", "network:api.example.com"])
            is True
        )

    def test_deny_undeclared_permissions(self) -> None:
        svc = PolicyIsolationService()
        manifest = _make_manifest(["file:/tmp/data"])
        assert svc.authorize(manifest, ["network:api.example.com"]) is False
        assert svc.authorize(manifest, ["env:SECRET"]) is False

    def test_deny_all_when_no_permissions(self) -> None:
        svc = PolicyIsolationService()
        manifest = _make_manifest([])
        assert svc.authorize(manifest, ["file:/tmp/data"]) is False

    def test_allow_empty_resource_request(self) -> None:
        svc = PolicyIsolationService()
        manifest = _make_manifest([])
        assert svc.authorize(manifest, []) is True


class TestDefaultIsolationService:
    def test_grants_all_requests(self) -> None:
        svc = DefaultIsolationService()
        manifest = _make_manifest([])
        assert svc.authorize(manifest, ["file:/tmp"]) is True
        assert svc.authorize(manifest, ["denied:resource"]) is True
