# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with:
```env
OPENAI_API_KEY=your_api_key_here
```

## Running

**CLI (primary entry point):**
```bash
python cli.py
```
Outputs `drift_report.json`. Dataset paths are currently hardcoded in `cli.py` — the CLI accepts `--reference` and `--new` flags per the README but these are not yet wired up in the argument parser.

**Streamlit UI (optional):**
```bash
streamlit run ui/app.py
```

## Architecture

The framework detects three types of drift between a reference and new dataset using LLMs to reason over statistical signals:

**Pipeline (orchestrated by `cli.py`):**
1. `ingestion/data_loader.py` — loads CSV/Excel/TXT files into DataFrames
2. `core/schema_profiler.py` — LLM infers semantic types per column (`ColumnProfile`), then compares schemas to detect added/removed columns (`DriftInsight`)
3. `core/distribution_profiler.py` — statistical drift for numerical columns (KS test, mean/std shift, null drift)
4. `core/pattern_profiler.py` — pattern/structure drift for string/identifier columns (format regex, entropy, value set changes)
5. `core/drift_reasoner.py` — LLM synthesizes all `DriftInsight` signals into an overall severity assessment
6. `report/report_generator.py` — serializes everything to `drift_report.json`

**Key models (`core/models.py`):**
- `ColumnProfile`: semantic type, data role, expected format, business criticality
- `DriftInsight`: boolean detection flag, severity, AI explanation, affected columns, source citation

**LLM layer:**
- `core/llm_client.py` — wraps `langchain-openai` ChatOpenAI (GPT-4o, temperature 0.1)
- `core/system_prompt.py` — defines the LLM's persona as a "data reliability engineer"; treated as first-class logic

## Extending the Framework

To add a new drift detector:
1. Create `core/<name>_profiler.py` — extract signals, return `DriftInsight` objects
2. Call it in `cli.py` and pass results to `reason_overall_drift()`
3. Update `core/system_prompt.py` if the new signal type needs LLM context

No existing profilers need modification.

## Sample Data

`data/` contains paired reference/new datasets for testing:
- `reference_data.csv` + `new_data_with_drift.csv` (primary — B2C→B2B shift)
- `reference_data_tc2/3/4.csv` + matching `new_data_with_drift_tc2/3/4.csv`

## LangGraph Rebuild (`langgraph_impl/`)

Full LangGraph rewrite of the drift detection pipeline.

**Entry point:**
```bash
python langgraph_impl/cli.py --reference data/reference_data.csv --new data/new_data_with_drift.csv
```

**Install deps:**
```bash
pip install -r langgraph_impl/requirements.txt
```

**Architecture:** `DriftState` TypedDict flows through a compiled `StateGraph`. Each node is a pure function returning only the keys it updates. Two profiler nodes (`profile_distributions`, `profile_patterns`) run in parallel after `profile_schema`, with a barrier before `reason_drift`.

**Nodes (in order):**
`load_data` → `profile_schema` → [`profile_distributions` ‖ `profile_patterns`] → `reason_drift` → `generate_report`

**Drift types detected (7 total):**
- Schema: column addition/removal, data type change, volume shift (>20%)
- Distribution: numeric distribution, cardinality change (>30%)
- Pattern: string format/structure, referential integrity for identifier columns

**Key files:**
- `langgraph_impl/state.py` — `DriftState` TypedDict (single source of truth)
- `langgraph_impl/graph.py` — `build_graph()`: StateGraph construction and compilation
- `langgraph_impl/nodes/` — one file per node, all pure functions
- `langgraph_impl/models.py` — `ColumnProfile`, `DriftInsight`, `DriftSummary`

**`.claude/` config (at repo root):**
- `.claude/rules/` — `python-standards.md`, `langgraph-patterns.md`, `drift-domain.md`
- `.claude/skills/` — `run-drift-pipeline`, `add-profiler`, `generate-drift-report`
- `.claude/agents/` — `drift-pipeline-agent`, `profiler-builder-agent`, `report-analyst-agent`

**Extending:** Add new drift checks inside the appropriate node — no changes to `graph.py`, `state.py`, or `drift_reasoner.py` needed. See `.claude/skills/add-profiler/SKILL.md` for the step-by-step pattern.
