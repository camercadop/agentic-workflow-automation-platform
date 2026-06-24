# ADR 005: Plugin Contract Definitions

**Status:** Accepted
**Date:** 2026-06-19
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** [001, 002, 003, 004]

## Context
The platform lacks standardized plugin contracts, leading to inconsistent interfaces and integration challenges. Without a common specification, plugins are difficult to maintain and version, hindering scalability.

We must balance this standardization with backward compatibility and flexibility. The goal is to improve modularity and maintainability by defining clear, predictable boundaries between the platform and its plugins.

## What is a Plugin Contract?
A Plugin Contract is a versioned architectural specification that defines the boundaries, guarantees, and interaction models between plugins and the platform. It unifies the Registry, Lifecycle, Plugin Runtime API, and Security contracts (from ADR-002, ADR-003, and ADR-004) into a single model that enables the platform to assess compatibility.

## Plugin Contract Model Decomposition
The Plugin Contract Model is composed of four constituent contracts, each addressing a distinct interaction concern. The contract decomposition is owned exclusively by this ADR; source ADRs define interfaces and behavior, not contracts.

- **Registry Contract** (sourced from ADR-002): Defines how plugins self-describe metadata for automatic registration during the build process. This contract is used for registry generation and does not imply runtime scanning or dynamic plugin discovery.
- **Lifecycle Contract** (sourced from ADR-003): Specifies the state machine and hooks governing plugin initialization, activation, and cleanup.
- **Plugin Runtime API Contract** (sourced from ADR-004, Plugin Runtime API Interface — platform services facet): Governs shared interaction protocols such as Event Bus, Metadata, Context, and Logging.
- **Security Contract** (sourced from ADR-004, Plugin Runtime API Interface — resource access facet): Governs permissions, isolation levels, and sandbox boundaries for plugin security and resource access.

The Plugin Runtime API Contract and Security Contract are two separate contracts projected from the single Plugin Runtime API Interface defined in ADR-004. ADR-004 defines one unified interface; this ADR decomposes it into two contracts to enable independent governance and validation (e.g., separate validation gates in ADR-009). Plugins interact with both concerns through that single interface.

These contracts together form the unified Plugin Contract Model.

## Decision
We will standardize the Plugin Contract as an architectural boundary specification that unifies the interaction models and boundaries defined in ADR-002, ADR-003, and ADR-004. Rather than defining concrete method signatures, we establish:

- **Interaction boundaries** as first-class architectural concepts, expressed through sandbox definitions from ADR-004 (Security Contract) and lifecycle hooks from ADR-003 (Lifecycle Contract)
- **Configuration and metadata schemas** as part of the boundary contract
- **Plugin Runtime API usage patterns** (Event Bus, Metadata, Context, Logging) as shared interaction protocols (Plugin Runtime API Contract)
- **Versioning and compatibility rules** governing boundary evolution

This approach emphasizes defining clear architectural contracts for how plugins relate to the platform and each other, rather than focusing on implementation details.

## Consequences
**Positive**
- Unifies Registry Contract (ADR-002), Lifecycle (ADR-003), Plugin Runtime API (ADR-004), and Security (ADR-004) contracts into a single versioned contract
- Clear compatibility boundaries for plugin updates and platform evolution
- Reduced integration testing effort through standardized contracts
- Plugin compatibility is determined against the Plugin Contract Model rather than implementation details

**Negative**
- Initial development overhead to define and document the unified contract
- Need to refactor existing plugins to align with the consolidated contract specification

**Risks**
- Over-specification might limit innovative plugin patterns requiring non-standard interfaces
- Versioning complexity if contract evolution isn't carefully managed

## Rationale
Standardizing contracts will improve the overall architecture by making plugins more predictable and easier to manage.
The trade-off is the initial effort required to define and implement these contracts, but it pays off in long-term maintainability.

## Validation Criteria
- All new plugins must comply with the Plugin Contract Model.
- Existing plugins are migrated to use the contracts within the next two release cycles.
- Contract compliance is verified through automated tests in the CI pipeline.

## Alternatives Considered
- **Fragmented Model** – Keep plugin-specific contracts without standardization – Rejected due to integration challenges and increased technical debt.
- **Dynamic Discovery Model** – Use a dynamic, configuration-based interface without static contracts – Rejected for lack of type safety and unpredictable runtime behavior.
- **Deferred Definition Model** – Defer contract definition until a later phase – Rejected because early definition reduces architectural rework and provides a clear roadmap for developers.

## Mandatory Rules
- All plugins must comply with the Plugin Contract Model defined in this ADR. This includes:
  - Complying with the Lifecycle Contract (ADR-003), including optional lifecycle hooks where implemented
  - Adhering to Registry Contract standards (ADR-002)
  - Adhering to Security standards (ADR-004)
  - Following Plugin Runtime API usage patterns (Event Bus, Metadata, Context, Logging)
- Breaking changes to the Plugin Contract Model require a new ADR revision

## Allowed Changes
- Adding new optional interaction patterns to the Plugin Contract Model
- Refining schema definitions or metadata structures without altering existing contract semantics
- Updating versioning or compatibility rules in a backward‑compatible manner

## Forbidden Changes
- Removing or fundamentally altering any defined interaction boundary or versioning rule without a deprecation period
- Changing the major version semantics in a way that breaks existing plugin compatibility
- Introducing breaking modifications to the Plugin Contract Model without appropriate migration guidance
