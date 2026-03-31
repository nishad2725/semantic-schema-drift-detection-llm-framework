# Python Standards

## Type Hints
- All function signatures must include parameter types and return type annotations.
- Use `list[X]` and `dict[K, V]` (lowercase, Python 3.10+), not `List[X]` from `typing`.
- Use `Optional[X]` or `X | None` for nullable fields.
- Use `TypedDict` for state objects, never plain `dict`.

## Docstrings
- Every public function, class, and module must have a Google-style docstring.
- Include `Args:`, `Returns:`, and `Raises:` sections where applicable.
- One-line docstrings are acceptable for trivial helpers.

## Logging
- Use `logging.getLogger(__name__)` at module level — never use `print()` in library or node code.
- Log pipeline milestones at `INFO`, per-column detail at `DEBUG`, failures at `WARNING` or `ERROR`.
- Include structured context in log messages (column name, row count, file path).

## Error Handling
- Node functions must never raise uncaught exceptions.
- Catch exceptions, log with `logger.exception()`, and return `{"error": str(exc)}` to propagate through state.
- Do not swallow errors silently.
- Validate at system boundaries (file load, LLM response) — trust internal logic.

## Imports
- Standard library first, then third-party, then local — separated by blank lines.
- All LangChain imports must come from `langgraph`, `langchain-openai`, or `langchain-core`.
- Never import from the top-level `langchain` package in this project.

## Code Style
- Maximum line length: 100 characters.
- No bare `except:` — always catch specific exception types or `Exception`.
- Prefer early returns over deeply nested conditionals.
