# Drift Domain Rules

## Drift Type Taxonomy
Three state keys hold categorized drift signals, all fed into `reason_drift`:

- **`schema_insights`**: structural metadata changes — column additions/removals, data type changes, volume drift.
- **`distribution_insights`**: numerical and categorical value distribution — mean/std/percentile shifts, cardinality changes.
- **`pattern_insights`**: string format and structural changes — regex/format drift, referential integrity for identifier columns.

## Detection Thresholds (defaults — document when overriding)
| Check | Threshold | Severity |
|---|---|---|
| Volume drift | Row count Δ > 20% | Moderate; High if Δ > 40% |
| Cardinality drift | Unique value count Δ > 30% | Moderate; High if Δ > 60% |
| Referential integrity | > 50% of reference ID values absent from new dataset | High |

## Adding a New Drift Detector — Checklist
1. Decide which category it belongs to: schema / distribution / pattern.
2. Identify the corresponding node (`load_data` or `schema_profiler` for schema; `distribution_profiler` for distribution; `pattern_profiler` for pattern).
3. Prefer deterministic threshold checks over LLM calls where the signal is well-defined.
4. Create a `DriftInsight` with `source` set to `state["new_path"]` for changes in the new dataset, or `state["reference_path"]` if the signal originates in reference data.
5. Append to the appropriate list returned by the node dict. Do **not** add new state keys.
6. No changes to `graph.py`, `state.py`, or `drift_reasoner.py` are needed — new insights flow automatically into `all_insights`.
7. Update this file with the new threshold and rationale.

## Severity Conventions
| Level | Meaning |
|---|---|
| **High** | Data is likely unusable or joins will break. Immediate investigation required. |
| **Moderate** | Downstream models need retraining or validation. Schedule review. |
| **Low** | Informational — no immediate action, but monitor trend. |
| **None** | No drift detected. Always include this case in reports. |

## LLM Conservation
- Do not call the LLM for checks that can be done deterministically.
- Volume, dtype, and cardinality drift are always deterministic.
- Pattern, format, and semantic distribution assessment requires LLM.
- All LLM calls go through `llm_client.get_llm()` with temperature 0.1.

## Source Citation Rules
- `DriftInsight.source` must always be populated.
- Use `state["new_path"]` when the drift is caused by changes **in** the new dataset.
- Use `state["reference_path"]` when the signal identifies something missing **from** the reference.
- For column removal, cite `state["reference_path"]` (that is where the column was lost from).
- For column addition, cite `state["new_path"]` (that is where the column appeared).
