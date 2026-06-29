# adr_writing Skill

## Skill Name
adr_writing

## Description
Provides capabilities for creating Architectural Decision Records (ADRs) in the standard format used by this project. This skill enables agents to document architectural decisions, alternatives considered, and consequences in a consistent manner.

## Usage
Agents can invoke this skill to:
- Create new ADRs following the project template
- Document architectural decisions made during development
- Record alternatives considered and their trade-offs
- Document consequences of decisions (positive, negative, neutral)
- Link related ADRs or supersede previous decisions

## Parameters
- `title`: Title of the ADR (should be concise and descriptive)
- `context`: Description of the situation motivating the decision
- `decision`: The chosen approach or solution
- `status`: Current status (e.g., "Proposed", "Accepted", "Superseded", "Deprecated")
- `consequences`:
  - `positive`: Positive outcomes of the decision
  - `negative`: Negative outcomes or trade-offs
  - `neutral`: Neutral outcomes or observations
- `alternatives`: Alternative approaches considered (optional)
- `related`: Related ADRs or documents (optional)
- `supersedes`: ADR number being superseded (if applicable)

## Examples
1. Creating a new ADR for plugin registration approach:
   ```
   title: "Plugin Registration Mechanism"
   context: "The system needs a way to discover and load plugins at startup"
   decision: "Use build-time registration with @register_plugin decorator"
   status: "Accepted"
   consequences:
     positive:
       - "Plugins are validated at build time"
       - "No runtime discovery overhead"
       - "Clear contract between plugins and core"
     negative:
       - "Requires rebuild to add new plugins"
       - "Less flexible than runtime discovery"
   alternatives:
     - "Runtime plugin discovery via directory scanning"
     - "Configuration-based plugin registration"
   ```

2. Superseding a previous ADR:
   ```
   title: "Workflow Execution Engine"
   context: "Initial workflow executor had limitations with complex DAGs"
   decision: "Implement topological sorting with parallel execution groups"
   status: "Accepted"
   supersedes: "001-workflow-execution-approach"
   consequences:
     positive:
       - "Supports complex workflow DAGs"
       - "Enables parallel execution where possible"
       - "Better error isolation"
   ```

## Return Values
- Formatted ADR content ready for saving to `/docs/adr/`
- Suggested ADR number based on existing ADRs
- Validation of ADR format compliance

## Notes
- ADRs should be stored in `/docs/adr/` with sequential numbering
- Follow the template in `/docs/adr/template.md`
- ADRs are immutable once accepted; create new ADRs to supersede
- Keep ADRs focused on a single decision
- Link related ADRs when appropriate
- Use clear, concise language suitable for technical decision-making
