# LLM Client

LLM integration layer implementing the agentic tool-calling loop.

## Modules

| Module | Purpose |
|--------|---------|
| `client.py` | LLM client — sends messages, handles tool calls in a loop until final response |
| `tools.py` | Tool implementations (read/write files, list dirs, run commands) with sandboxing |
| `tool_schemas.json` | JSON schemas describing available tools for the LLM |
