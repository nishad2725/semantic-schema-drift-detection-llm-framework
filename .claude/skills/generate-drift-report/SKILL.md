---
name: generate-drift-report
description: Read drift_report.json and explain findings in plain English with severity prioritization
allowed-tools: Read, Bash
---

# Skill: generate-drift-report

Parse and summarize a `drift_report.json` file in plain English.

## Trigger
User asks to "explain the drift report", "summarize the results", "what does the report say", or "show me the findings".

## Steps
1. Read the specified `drift_report.json` (default: `drift_report.json` in the repo root).
2. Check for `error` field — if present, escalate to `drift-pipeline-agent` before analysis.
3. Extract and present:
   - `overall_severity` and `llm_summary`
   - Count of insights per category with severity breakdown
   - All affected columns grouped by severity

## Output Format
Present as a structured markdown summary:

```
## Overall Assessment
Severity: <overall_severity>

<llm_summary>

## High Severity Findings
- <finding 1>
- <finding 2>

## Moderate Severity Findings
- ...

## Affected Columns Summary
- Columns with High drift: [...]
- Columns with Moderate drift: [...]

## Recommended Actions
- <action 1 based on llm_summary>
- <action 2>
```

## Constraints
- Do not re-run the pipeline — work only from the existing report JSON.
- Do not invent findings not present in the JSON.
- High severity findings always appear first.
- If `error` is non-null, show it prominently before any other analysis.
