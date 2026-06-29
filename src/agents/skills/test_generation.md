# test_generation Skill

## Skill Name
test_generation

## Description
Provides capabilities for generating unit and integration tests from source code. This skill enables agents to automatically create test cases that validate functionality, edge cases, and error conditions.

## Usage
Agents can invoke this skill to:
- Generate unit tests for functions, methods, and classes
- Create integration tests for component interactions
- Generate test cases for edge cases and error conditions
- Create mock objects for external dependencies
- Generate test fixtures and setup/teardown code

## Parameters
- `sourceCode`: The source code to generate tests for (can be file path or code snippet)
- `testType`: Type of tests to generate (`unit`, `integration`, `edge_case`)
- `framework`: Testing framework to use (`pytest` for this project)
- `coverageTarget`: Desired coverage percentage (default: 80%)
- `includeMocks`: Whether to include mock dependencies (boolean)
- `focusAreas`: Specific functions or classes to focus on testing

## Examples
1. Generating unit tests for a plugin:
   ```
   sourceCode: "/src/plugins/actions/email_sender.py"
   testType: "unit"
   framework: "pytest"
   focusAreas: ["send_email", "validate_config"]
   ```

2. Generating integration tests for workflow execution:
   ```
   sourceCode: "/src/core/executor.py"
   testType: "integration"
   framework: "pytest"
   includeMocks: true
   ```

3. Generating edge case tests:
   ```
   sourceCode: "/src/plugins/transformers/data_mapper.py"
   testType: "edge_case"
   framework: "pytest"
   ```

## Return Values
- Generated test code as a string
- File paths where tests should be saved
- Coverage estimates for the generated tests
- Any warnings about untestable code

## Notes
- Generated tests should follow the project's testing conventions
- Tests should be placed in the appropriate `tests/` directory structure
- Generated tests must be reviewable and editable by human developers
- The skill aims to increase test coverage while maintaining test quality
- Tests should include meaningful assertions, not just coverage hooks
