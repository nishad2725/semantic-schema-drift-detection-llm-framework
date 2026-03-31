---
name: add-profiler
description: Scaffold a new drift detector node following the existing LangGraph pattern
allowed-tools: Read, Edit, Bash, Glob
---

# Skill: add-profiler

Add a new drift detector to the LangGraph pipeline following the established patterns.

## Trigger
User asks to "add a new drift type", "add a profiler", "detect X drift", or "extend the pipeline to check for Y".

## Decision Tree

### Step 1 — Categorize the drift type
Ask (or infer) which insight category this belongs to:
- **Schema** → structural metadata (columns, types, row count): use `schema_insights`
- **Distribution** → value distribution or cardinality: use `distribution_insights`
- **Pattern** → string format, structure, or referential integrity: use `pattern_insights`

### Step 2 — Determine LLM vs deterministic
- If the check has a clear numerical threshold → deterministic (no LLM)
- If the check requires semantic interpretation → LLM via `with_structured_output(DriftInsight)`

### Step 3 — Identify the target node
| Category | Node file |
|---|---|
| schema_insights (early, before LLM) | `nodes/data_loader.py` |
| schema_insights (after column profiling) | `nodes/schema_profiler.py` |
| distribution_insights | `nodes/distribution_profiler.py` |
| pattern_insights | `nodes/pattern_profiler.py` |

## Implementation
1. Add the check as a new code block inside the identified node function.
2. Construct a `DriftInsight` with all required fields, including `source`.
3. Append to the list that the node returns in its dict.
4. Follow `python-standards.md`: type hints, docstrings, logging, no bare excepts.

## Constraints
- No new state keys. No new graph nodes unless the drift type is truly orthogonal.
- Nodes must remain pure: `(state: DriftState) -> dict`.
- LLM calls only via `get_llm()` from `langgraph_impl/llm_client.py`.

## Verification
After implementing:
1. Run `python -c "from langgraph_impl.graph import build_graph; build_graph(); print('OK')"` from repo root.
2. Run the pipeline: `python langgraph_impl/cli.py --reference data/reference_data.csv --new data/new_data_with_drift.csv`.
3. Confirm the new `DriftInsight` appears in the correct list in `drift_report.json`.
4. Update `.claude/rules/drift-domain.md` with the new threshold and rationale.
