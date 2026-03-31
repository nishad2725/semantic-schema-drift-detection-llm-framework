---
name: run-drift-pipeline
description: Run the full LangGraph drift detection pipeline on a reference/new dataset pair
allowed-tools: Bash, Read, Glob
---

# Skill: run-drift-pipeline

Run the LangGraph drift detection pipeline against a reference and new dataset pair.

## Trigger
User asks to "run drift detection", "analyze drift", "compare datasets", or "detect drift between X and Y".

## Pre-flight Checks
1. Confirm both `--reference` and `--new` file paths exist and are readable.
2. Confirm `OPENAI_API_KEY` is set in the environment or `.env` file at the repo root.
3. Confirm the `.venv` is active or dependencies from `langgraph_impl/requirements.txt` are installed.

## Execution
Run from the **repo root** (not from `langgraph_impl/`):
```bash
python langgraph_impl/cli.py \
  --reference <reference_path> \
  --new <new_path> \
  --output drift_report.json
```

Default paths if not specified:
- Reference: `data/reference_data.csv`
- New: `data/new_data_with_drift.csv`
- Output: `drift_report.json`

## Post-run
1. Report the `overall_severity` and insight counts from the summary table printed to stdout.
2. Offer to display the `drift_report.json` summary using the `generate-drift-report` skill.

## Error Handling
- If `error` is present in the JSON output: show the error and suggest checking file paths and `OPENAI_API_KEY`.
- If LLM call fails: verify the API key is valid and the `gpt-4o` model is accessible on the account.
- If imports fail: run `pip install -r langgraph_impl/requirements.txt` in the active venv.
