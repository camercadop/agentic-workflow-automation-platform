"""Plugin Registry and Lifecycle Management (ADR-002, ADR-003)."""

from enum import StrEnum

from src.core.contracts import PluginBase


class LifecycleState(StrEnum):
    """Plugin lifecycle states per ADR-003."""

    REGISTERED = "registered"
    ACTIVATED = "activated"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    CLEANED_UP = "cleaned_up"


# Valid state transitions (current -> allowed next states)
_TRANSITIONS: dict[LifecycleState, LifecycleState] = {
    LifecycleState.REGISTERED: LifecycleState.ACTIVATED,
    LifecycleState.ACTIVATED: LifecycleState.ACTIVE,
    LifecycleState.ACTIVE: LifecycleState.DEACTIVATED,
    LifecycleState.DEACTIVATED: LifecycleState.CLEANED_UP,
}


class LifecycleError(Exception):
    """Raised when an invalid lifecycle transition is attempted."""


class PluginEntry:
    """A registered plugin with its current lifecycle state."""

    __slots__ = ("plugin", "state")

    def __init__(self, plugin: PluginBase) -> None:
        """Initialize entry with plugin in REGISTERED state.

        Args:
            plugin: The plugin instance to wrap.
        """
        self.plugin = plugin
        self.state = LifecycleState.REGISTERED

    @property
    def name(self) -> str:
        """The plugin's registered name."""
        return self.plugin.manifest.name


class PluginRegistry:
    """Static plugin registry loaded at startup (ADR-002).

    Manages plugin registration and lifecycle transitions (ADR-003).
    No runtime discovery is performed.
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._entries: dict[str, PluginEntry] = {}

    @property
    def plugins(self) -> dict[str, PluginEntry]:
        """Return a copy of all registered plugin entries."""
        return dict(self._entries)

    def register(self, plugin: PluginBase) -> None:
        """Register a plugin (build-time validated).

        Args:
            plugin: The plugin instance to register.

        Raises:
            ValueError: If a plugin with the same name is already registered.
        """
        name = plugin.manifest.name
        if name in self._entries:
            raise ValueError(f"Plugin '{name}' is already registered.")
        self._entries[name] = PluginEntry(plugin)

    def get(self, name: str) -> PluginEntry:
        """Retrieve a registered plugin entry by name.

        Args:
            name: The plugin's registered name.

        Returns:
            The plugin entry.

        Raises:
            KeyError: If the plugin is not found.
        """
        if name not in self._entries:
            raise KeyError(f"Plugin '{name}' not found in registry.")
        return self._entries[name]

    def activate(self, name: str) -> None:
        """Activate a plugin and invoke its on_activate hook.

        Transitions the plugin to ACTIVATED state.

        Args:
            name: The plugin's registered name.

        Raises:
            LifecycleError: If the plugin is not in REGISTERED state.
        """
        entry = self.get(name)
        self._transition(entry, LifecycleState.ACTIVATED)
        entry.plugin.on_activate()

    def mark_active(self, name: str) -> None:
        """Mark a plugin as active and ready for execution.

        Transitions the plugin to ACTIVE state.

        Args:
            name: The plugin's registered name.

        Raises:
            LifecycleError: If the plugin is not in ACTIVATED state.
        """
        entry = self.get(name)
        self._transition(entry, LifecycleState.ACTIVE)

    def deactivate(self, name: str) -> None:
        """Deactivate a plugin and invoke its on_deactivate hook.

        Transitions the plugin to DEACTIVATED state.

        Args:
            name: The plugin's registered name.

        Raises:
            LifecycleError: If the plugin is not in ACTIVE state.
        """
        entry = self.get(name)
        self._transition(entry, LifecycleState.DEACTIVATED)
        entry.plugin.on_deactivate()

    def cleanup(self, name: str) -> None:
        """Clean up a plugin and invoke its on_cleanup hook.

        Transitions the plugin to CLEANED_UP state.

        Args:
            name: The plugin's registered name.

        Raises:
            LifecycleError: If the plugin is not in DEACTIVATED state.
        """
        entry = self.get(name)
        self._transition(entry, LifecycleState.CLEANED_UP)
        entry.plugin.on_cleanup()

    def _transition(self, entry: PluginEntry, target: LifecycleState) -> None:
        """Validate and apply a state transition."""
        allowed = _TRANSITIONS.get(entry.state)
        if allowed != target:
            raise LifecycleError(
                f"Cannot transition '{entry.name}' from {entry.state} to {target}."
            )
        entry.state = target
