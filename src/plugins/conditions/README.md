# Condition Plugins

Plugins that evaluate data and return a boolean to control workflow branching.

## Implementations

| Plugin | Description |
|--------|-------------|
| `true_condition.py` | Always returns `True` (passthrough) |
| `comparisons.py` | Numeric/equality comparisons (eq, gt, lt, gte, lte) |
| `string_condition.py` | String matching (contains, starts_with, ends_with, regex) |
| `logical_condition.py` | Logical combinators (and, or, not) over nested conditions |
| `collection_condition.py` | Collection checks (contains, is_empty, length comparisons) |
