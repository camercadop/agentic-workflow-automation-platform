# file_ops Skill

## Skill Name
file_ops

## Description
Provides capabilities for creating, reading, modifying, and managing project files. This skill enables agents to perform file system operations necessary for implementing changes, creating documentation, and managing the codebase.

## Usage
Agents can invoke this skill to:
- Create new files with specified content
- Read existing files to understand current state
- Modify existing files by replacing specific content
- Insert code into existing files at specific locations
- Delete files when necessary
- Create directory structures

## Parameters
- `filePath`: Absolute path to the file to operate on
- `content`: Content to write when creating or replacing a file
- `oldString`: Exact text to replace (for modify operations)
- `newString`: Exact text to replace with (for modify operations)
- `code`: Code snippet to insert (for insert operations)
- `explanation`: Brief description of the change being made
- `editType`: Type of edit (`insert`, `delete`, or `edit`)

## Examples
1. Creating a new Python module:
   ```
   filePath: "/src/core/new_feature.py"
   content: "# New feature implementation\n..."
   ```

2. Modifying an existing function:
   ```
   filePath: "/src/core/existing_module.py"
   oldString: "def old_function():\n    pass"
   newString: "def old_function():\n    # New implementation\n    return result"
   explanation: "Updated function to implement new business logic"
   ```

3. Inserting code into a class:
   ```
   filePath: "/src/models/user.py"
   code: "    def new_method(self):\n        return self.value"
   explanation: "Added new method to User class"
   ```

## Return Values
- Success confirmation or error details
- For read operations: the file content
- For write operations: confirmation of changes made

## Notes
- All file paths should be absolute within the workspace
- When modifying files, provide sufficient context in `oldString` to ensure uniqueness
- The skill is designed to be safe and predictable, avoiding unintended side effects
