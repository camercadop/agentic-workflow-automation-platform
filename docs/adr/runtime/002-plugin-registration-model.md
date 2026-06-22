# 002-Plugin Registration Model

**Status:** Accepted
**Date:** 2026-06-18
**Authors:** Carlos Mercado <carlosmercadop714@gmail.com>
**Related ADRs:** 001, 003, 005

## Context
The platform operates under a strict build-time registration model for plugins:
- Plugins are produced during development time and validated against architectural contracts (ADR-005).
- At runtime, plugins exist as pre-compiled components referenced exclusively through the generated plugin registry.

## Decision
Adopt a **Build-Time Plugin Registration** approach:
- Plugins declare metadata, capabilities, and contract information through standardized manifests
- During CI/CD pipeline:
  1. Validate manifests against Plugin Contract Model (ADR-005) using the Validation Engine (ADR-009)
  2. Upon successful validation, the Registry Builder tool compiles the final Static Registry artifact from validated artifacts
  3. Package registry with application
- At startup, the Core Engine loads the pre-generated registry as the sole source of plugin registration information

## Consequences
**Positive**
- Zero runtime overhead for plugin discovery or registration
- Security enforced through pre-validation of manifests
- Predictable startup behavior with static configuration

**Negative**
- Build-time proportional to plugin count and complexity
- Full rebuild required for plugin changes
- Registry generation failures blocking releases

**Risks**
- Build pipeline slowdown as plugin count grows
- Validation defects could allow incompatible plugins into the generated registry

## Validation Criteria
- Verify that manifests are processed exclusively during build time
- Verify that no runtime manifest scanning or discovery occurs
- Verify that the Core Engine loads plugin definitions only from the generated registry
- Verify that registry generation fails if any manifest validation fails
- Verify that all validated plugins are correctly included in the generated registry

## Rationale
This model reflects the actual architecture:
1. **CI/CD**: Manifests are validated against Plugin Contract Model (ADR-005) and platform contracts by the Validation Engine (ADR-009)
2. **Registry Generation**: The Registry Builder tool compiles the final Static Registry from validated artifacts
3. **Runtime**: Core Engine loads plugin definitions exclusively from the pre-generated registry

This approach maintains core minimalism while providing deterministic configuration and security through build-time validation.

## Mandatory Rules
- All plugins must be registered through build‑time manifest processing.
- Only validated plugins may be included in the generated registry.
- At runtime, the Core Engine must load plugin definitions exclusively from the generated registry.
- Registry generation must fail when any plugin manifest fails validation.
- Runtime plugin discovery, scanning, and registration are prohibited.
