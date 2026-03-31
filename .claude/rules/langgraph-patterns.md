# LangGraph Patterns

## Node Functions
- Every node is a pure function: `(state: DriftState) -> dict`.
- Return **only** the keys that the node modifies — do not return the full state object.
- Never mutate the state object in place. Always construct new values and return them.
- Nodes must be importable individually for unit testing without invoking the graph.

## State Design
- `DriftState` is the single source of truth. No auxiliary state objects or inter-node function calls.
- Lists in state are append-only across nodes. Use `state["key"] + new_items` for sequential accumulation.
- DataFrames stored as `Optional[object]` are **not checkpointed**. Document this in node docstrings.
- All keys must be present in the initial state dict passed to `graph.invoke()`.

## Parallel Fan-Out
- Use `graph.add_edge(source, dest)` twice for a static two-branch fan-out.
- Do **not** use `Send()` for a fixed number of parallel branches — `Send()` is for dynamic fan-out over variable-length collections.
- LangGraph creates an implicit barrier at nodes with multiple incoming edges; both branches must complete before the join node fires.
- The two parallel branches must write to **different** state keys to avoid merge conflicts.

## Conditional Routing
- Routing functions have signature `(state: DriftState) -> str`.
- The returned string must match a key in the `path_map` dict passed to `add_conditional_edges`.
- Always handle the error path by routing to `generate_report`, not `END` — a partial report is more useful than silence.

## LLM Calls
- All LLM instantiation goes through `llm_client.get_llm()`. Never instantiate `ChatOpenAI` directly in node files.
- Use `llm.with_structured_output(PydanticModel)` for all structured outputs.
- Always use a `ChatPromptTemplate` — never call `llm.invoke()` with a raw string.
- Wrap LLM calls in try/except and fall back to a manually-constructed model instance on failure.

## Graph Compilation
- `build_graph()` in `graph.py` returns `graph.compile()` — the compiled graph, not the builder.
- The compiled graph is invoked in `cli.py`, never in `graph.py` itself.
- Do not pass a `checkpointer` to `graph.compile()` unless DataFrame serialization is explicitly handled.
- Entry point is always `graph.add_edge(START, "first_node")`.
