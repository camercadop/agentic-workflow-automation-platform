# 002-Plugin Discovery Mechanism

**Status:** Accepted
**Date:** 2026-06-18
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001

## Context
The platform lacks an automatic way to discover and register plugins, forcing developers to manually update configuration files whenever new extensibility components are added. This manual process introduces delays, increases the chance of human error, and creates a direct coupling between the Core Engine and each plugin, preventing true plugin isolation. Implementing a discovery mechanism is essential to align with the documented architectural goal of maintaining a minimal core while supporting dynamic extensibility. It must operate efficiently during startup, handle malformed or missing manifests without halting the engine, and enforce security by never executing untrusted code during the discovery phase.

## Decision
Adopt a **Manifest-Based Discovery** approach where plugins self‑describe their capabilities and metadata through a standardized manifest. The Core Engine will identify these manifests through a defined discovery process to dynamically register plugins at startup, ensuring the engine remains agnostic to specific plugin implementations while maintaining a registry of available capabilities.

## Consequences
**Positive**
- Eliminates manual configuration errors during plugin deployment
- Maintains Core Engine minimalism by decoupling plugin registration
- Security advantage of no code execution during discovery phase

**Negative**
- Potential performance overhead from manifest validation
- Complexity in handling malformed or incomplete manifests
- Possible discovery delays during startup if manifests are large

**Risks**
- Performance degradation during discovery if manifests are large or complex
- Potential security gaps if manifest validation is insufficient
- Disk I/O bottlenecks during discovery phase impacting startup time

## Rationale
Manifest-based discovery provides automatic plugin registration without requiring core modifications, aligning with the Plugin First philosophy. It balances simplicity with extensibility by allowing plugins to declare their capabilities while keeping the discovery process secure and deterministic.

## Validation Criteria
- Verify that plugins are discovered without manual configuration
- Verify that the discovery process handles missing manifests gracefully
- Verify that the discovery process handles malformed manifests gracefully
- Verify that discovered plugins are registered in the plugin registry
- Verify that the Core Engine does not execute plugin code during discovery

## Alternatives Considered
- **Hard‑coded Registration** – Manually editing configuration files to register plugins. Rejected because it directly contradicts the Plugin First philosophy of automatic discovery.
- **Centralized External Registry** – Delegating discovery to an external service. Rejected for adding unnecessary infrastructure complexity during the prototype phase.
- **Conditional Runtime Loading** – Discovering plugins only when first needed. Rejected because it complicates error handling and makes startup behavior nondeterministic.

## Mandatory Rules
- Plugins must be discoverable without manual configuration or Core Engine modification.
- The discovery process must be resilient to individual plugin failures.
- Only plugins whose manifests successfully pass validation are eligible for registration.
- The discovery mechanism must produce an audit trail of discovery events.

## Allowed Changes
- Adjust the discovery process implementation details as long as automatic discovery remains intact.
- Extend the manifest format to include additional plugin metadata.
- Improve how failed discoveries are reported and logged.

## Forbidden Changes
- Require manual editing of discovery configurations.
- Skip manifest validation to accelerate startup.
- Allow plugins without manifests to be loaded.
