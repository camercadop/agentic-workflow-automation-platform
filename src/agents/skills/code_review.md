# code_review Skill

## Skill Name
code_review

## Description
Provides capabilities for analyzing code against project standards, architectural principles, and best practices. This skill enables agents to conduct automated code reviews, identify potential issues, and suggest improvements.

## Usage
Agents can invoke this skill to:
- Check code for adherence to coding standards (PEP 8, type hints, etc.)
- Validate compliance with architectural principles (ADRs, Plugin First, etc.)
- Identify potential bugs, code smells, or maintainability issues
- Check for proper error handling and resource management
- Verify test coverage and test quality
- Ensure documentation is adequate and up-to-date
- Detect violations of project-specific rules

## Parameters
- `code`: The code to review (can be file path, code snippet, or diff)
- `reviewType`: Type of review to perform (`standards`, `architecture`, `security`, `performance`, `comprehensive`)
- `standards`: Specific standards to check against (list, e.g., ["PEP8", "mypy", "project_conventions"])
- `adrs`: Specific ADRs to validate against (list of ADR numbers)
- `focusAreas`: Specific aspects to focus on (e.g., ["error_handling", "security", "testability"])
- `severityThreshold`: Minimum severity level to report (`low`, `medium`, `high`, `critical`)

## Examples
1. Checking a new plugin for architectural compliance:
   ```
   code: "/src/plugins/actions/new_plugin.py"
   reviewType: "architecture"
   adrs: ["001", "002", "004"]
   focusAreas: ["plugin_contracts", "isolation"]
   ```

2. Performing a comprehensive code review:
   ```
   code: "/src/core/executor.py"
   reviewType: "comprehensive"
   standards: ["PEP8", "mypy", "project_conventions"]
   severityThreshold: "medium"
   ```

3. Checking for security vulnerabilities:
   ```
   code: "/src/api/routes/plugins.py"
   reviewType: "security"
   focusAreas: ["input_validation", "authentication", "data_exposure"]
   ```

## Return Values
- List of issues found, each with:
  - `severity`: `low`, `medium`, `high`, `critical`
  - `category`: `standards`, `architecture`, `bug`, `security`, `performance`, `maintainability`
  - `message`: Description of the issue
  - `location`: File path and line number (if applicable)
  - `suggestion`: Recommended fix or improvement
- Summary statistics (counts by severity and category)
- Overall assessment (pass/fail based on thresholds)
- Links to relevant ADRs or documentation for guidance

## Notes
- The skill should be configurable to match project-specific rules and conventions
- Reviews should be educational, not just punitive - explain why something is an issue
- The skill should minimize false positives while catching real issues
- For architectural reviews, reference specific ADRs and principles
- The skill should support both preventive (pre-commit) and detective (post-commit) reviews
- Integration with existing tools (ruff, mypy, pytest) is preferred where applicable
