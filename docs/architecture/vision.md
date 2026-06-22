# Architectural Vision

## System Description
The system is a plugin-driven orchestration engine designed to execute non-linear workflows. It consists of a minimal **Core Engine** that handles the lifecycle of workflows and a set of **Isolated Plugins** (Triggers, Conditions, Transformers, and Actions) that implement the business logic. The system acts as a host for plugins, providing them with an execution context and managing their sequencing based on a workflow definition, without the Core knowing the internal logic of any plugin.

## Purpose
Define the immutable architectural boundaries of the **agentic workflow automation platform**: a minimal Core Engine that provides only build-time registration, static registry generation, runtime registry loading, execution context, workflow definition, and orchestration, while all business logic resides in isolated plugins. This vision establishes non-negotiable architectural truths that must guide every design decision.

## Core Principles
- **Plugin Isolation**: Plugins operate within strict boundaries to prevent leakage into Core; the technical implementation of isolation will be defined in a future ADR
- **Core Minimalism**: Core Engine contains no business logic; only infrastructure contracts and lifecycle management
- **Governance Boundaries**: Clear separation between architectural decisions (architect‑led) and plugin implementations
- **Execution Context**: Per‑plugin‑instance isolation boundary that provides isolated memory, threading, and sandbox scopes for each plugin execution
- **Workflow Context**: Mediated data‑propagation container managed by the workflow runtime, used to pass state between plugin instances without direct sharing
- **Non‑Linear Compliance**: Workflow execution model supports branching/merging without Core modification

## Non-Goals Explicitly Stated
- Production workflow features
- End-user UI components
- Infrastructure deployment
- Core Engine business logic

## Vision Enforcement
Architectural violations must trigger automated governance rejections. The specific validation checkpoints and enforcement mechanisms will be defined in future ADRs.
