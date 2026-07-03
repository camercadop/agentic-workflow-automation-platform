"""Collection condition plugins — abstract base and concrete implementations."""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Collection
from typing import Any

from src.core.contracts import ConditionPlugin
from src.core.manifest import PluginManifest, PluginType
from src.core.registration import register_plugin


class CollectionCondition(ConditionPlugin):
    """Base class for conditions that operate on collection values.

    Subclasses should implement :meth:`compare` which receives the actual
    collection extracted from the input data and the expected value supplied
    during plugin construction.
    """

    def __init__(self, key: str = "", expected: Any = None) -> None:
        """Create a collection condition.

        Args:
            key: The dictionary key whose value will be inspected.
            expected: The expected value used by the concrete comparison.
        """
        self._key = key
        self._expected = expected

    @abstractmethod
    def compare(self, actual: Collection[Any], expected: Any) -> bool:
        """Compare the actual collection with the expected value.

        Implementations must return ``True`` when the condition is satisfied.
        """

    def evaluate(self, data: dict[str, Any]) -> bool:
        """Evaluate the condition against *data*.

        The value at ``self._key`` must be a :class:`collections.abc.Collection`.
        If the key is missing or the value is not a collection, ``False`` is
        returned.
        """
        actual = data.get(self._key)
        if not isinstance(actual, Collection):
            return False
        return self.compare(actual, self._expected)


@register_plugin
class ContainsInCollection(CollectionCondition):
    """Condition that passes if *expected* is an element of the collection.

    Example::
        data = {"tags": ["red", "blue"]}
        plugin = ContainsInCollection(key="tags", expected="red")
        assert plugin.evaluate(data)
    """

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="contains-in-collection-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Collection[Any], expected: Any) -> bool:
        """Return ``True`` if *expected* is present in *actual* collection."""
        return expected in actual


@register_plugin
class LengthEquals(CollectionCondition):
    """Condition that passes when ``len(collection) == expected``.

    ``expected`` should be an ``int`` representing the desired length.
    """

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="length-equals-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def compare(self, actual: Collection[Any], expected: Any) -> bool:
        """Return ``True`` when the collection length matches *expected*.

        ``expected`` is coerced to ``int``; non‑integer values result in ``False``.
        """
        try:
            exp_int = int(expected)
        except (TypeError, ValueError):
            return False
        return len(actual) == exp_int


@register_plugin
class IsEmpty(CollectionCondition):
    """Condition that passes when the collection is empty.

    The ``value`` argument is ignored; it is kept for signature compatibility.
    """

    @property
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""
        return PluginManifest(
            name="is-empty-condition",
            version="1.0.0",
            plugin_type=PluginType.CONDITION,
            permissions=[],
        )

    def __init__(self, key: str = "", expected: Any = None) -> None:  # noqa: D401
        """Create the plugin; *expected* is unused.

        Args:
            key: The key in the data dict to inspect.
            expected: Ignored; present for API compatibility.
        """
        super().__init__(key=key, expected=expected)

    def compare(self, actual: Collection[Any], expected: Any) -> bool:
        """Return ``True`` when *actual* collection has no elements."""
        return len(actual) == 0
