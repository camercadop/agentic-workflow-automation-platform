# ADR 003 - Plugin Lifecycle Model

**Status:** Accepted
**Date:** 2026-06-19
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001, 002

## Context
The platform lacks a standardized mechanism to manage plugin initialization, activation, and cleanup, leading to unpredictable behavior during runtime. This is critical because the Plugin First Architecture (ADR 001) requires plugins to be independent yet managed components, and without control over their execution points, plugins cannot reliably initialize resources or clean up state. The system must ensure deterministic plugin behavior while supporting the build-time registration model (ADR 002) and core minimalism principles. Constraints include maintaining backward compatibility with existing plugins and ensuring the Core Engine remains agnostic to plugin implementations. This decision directly affects the architectural goals of Plugin Isolation and Core Minimalism by establishing clear boundaries for plugin lifecycle management.

## Decision
Adopt a standardized lifecycle state machine managed by the Core Engine with states: Registered, Activated, Active, Deactivated, Cleaned Up. Plugins may optionally implement hooks for state transitions.

## Consequences
**Positive**
- Standardized plugin behavior across the platform
- Reliable resource initialization and cleanup
- Predictable error handling and state management
- Minimal overhead for simple plugins

**Negative**
- Additional complexity for plugin developers
- Potential performance overhead during lifecycle transitions
- More boilerplate code required for plugin implementations

**Risks**
- Increased complexity may discourage third‑party plugin development
- Performance overhead during activation/deactivation phases

## Validation Criteria
- Verify that Core Engine transitions all plugins through states in the defined order.
- Verify that **implemented** hooks are invoked during state transitions.
- Verify that errors in implemented hooks halt state progression.
- Verify that error logs are generated for lifecycle failures.
- Verify that plugins can be transitioned to Deactivated and Cleaned Up after runtime errors.

## Alternatives Considered
- **Event-Driven Lifecycle**: Letting plugins define their own lifecycle events. Rejected because it violates Core Engine agnosticism and creates inconsistent behavior.
- **Passive Plugin Management**: No lifecycle hooks, relying on plugins for self‑management. Rejected because it undermines Plugin Isolation and makes error handling unpredictable.
- **Monolithic Lifecycle**: Single initialize/shutdown pair. Rejected because it lacks granularity for runtime state management.

## Rationale
A standardized lifecycle ensures deterministic plugin behavior while allowing plugins to implement only the hooks they need. The Active state represents the operational phase where plugins process workflow tasks, making the model more intuitive for developers. If a hook exists for a state transition, the Core Engine must invoke it; otherwise, the transition proceeds without a hook call.

## Mandatory Rules
- Core Engine manages the lifecycle state machine for all plugins.
- Plugins optionally implement hooks for state transitions.
- **Core Engine must invoke implemented hooks** when entering/exiting states (only if a hook exists).
- Errors in any implemented hook must be logged and prevent state progression.

## Allowed Changes
- Extend lifecycle hooks with additional optional hooks.
- Refine hook signatures and metadata.

## Forbidden Changes
- Skipping any hook that is part of a plugin’s hook contract.
- Allowing plugins to manage their own lifecycle without core coordination.

---

### ✅ **Terminology (Updates)**
| Term | Definition |
|------|------------|
| **Lifecycle State** | One of the sequential phases a plugin passes through: Registered → Activated → Active → Deactivated → Cleaned Up. |
| **Lifecycle Hook** | Optional function a plugin may implement to respond to state transitions (e.g., `on_activated`, `on_enter_activated`, `on_exit_deactivated`). |
| **Hook Contract** | The set of hooks a plugin implements, determined by the plugin’s own code and optional metadata. |

---

*This document has been updated to clarify that hook implementation is optional and to remove any ambiguity regarding mandatory hook usage.*