"""Smoke test to verify project setup."""


def test_project_imports() -> None:
    """Verify core packages are importable."""
    import src.core
    import src.plugins
    import src.api

    assert src.core is not None
    assert src.plugins is not None
    assert src.api is not None
