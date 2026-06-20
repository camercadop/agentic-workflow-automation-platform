# C4 Model Level 0 - System Context Diagram

```mermaid
C4Context
    Person(dev, "Developer", "Writes plugins and workflow definitions")
    Person(arch, "Architect", "Defines contracts, governance and architectural guidelines")

    System_Boundary(pfa, "Plugin-First Workflow Automation Platform") {
        System(pfa_sys, "Workflow Automation Platform", "Executes plugin-driven workflows to automate business tasks")
    }

    System_Ext(ext, "External Systems", "Third-party services (APIs, databases, etc.) invoked by plugins during workflow execution")

    Rel(dev, pfa_sys, "writes code for")
    Rel(arch, pfa_sys, "defines contracts & governance for")
    Rel(pfa_sys, ext, "invokes")
```
