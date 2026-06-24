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
        self.plugin = plugin
        self.state = LifecycleState.REGISTERED

    @property
    def name(self) -> str:
        return self.plugin.manifest.name


class PluginRegistry:
    """Static plugin registry loaded at startup (ADR-002).

    Manages plugin registration and lifecycle transitions (ADR-003).
    No runtime discovery is performed.
    """

    def __init__(self) -> None:
        self._entries: dict[str, PluginEntry] = {}

    @property
    def plugins(self) -> dict[str, PluginEntry]:
        return dict(self._entries)

    def register(self, plugin: PluginBase) -> None:
        """Register a plugin (build-time validated). Raises ValueError on duplicate."""
        name = plugin.manifest.name
        if name in self._entries:
            raise ValueError(f"Plugin '{name}' is already registered.")
        self._entries[name] = PluginEntry(plugin)

    def get(self, name: str) -> PluginEntry:
        """Retrieve a registered plugin entry by name."""
        if name not in self._entries:
            raise KeyError(f"Plugin '{name}' not found in registry.")
        return self._entries[name]

    def activate(self, name: str) -> None:
        """Transition plugin: Registered -> Activated (invokes on_activate hook)."""
        entry = self.get(name)
        self._transition(entry, LifecycleState.ACTIVATED)
        entry.plugin.on_activate()

    def mark_active(self, name: str) -> None:
        """Transition plugin: Activated -> Active."""
        entry = self.get(name)
        self._transition(entry, LifecycleState.ACTIVE)

    def deactivate(self, name: str) -> None:
        """Transition plugin: Active -> Deactivated (invokes on_deactivate hook)."""
        entry = self.get(name)
        self._transition(entry, LifecycleState.DEACTIVATED)
        entry.plugin.on_deactivate()

    def cleanup(self, name: str) -> None:
        """Transition plugin: Deactivated -> CleanedUp (invokes on_cleanup hook)."""
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
