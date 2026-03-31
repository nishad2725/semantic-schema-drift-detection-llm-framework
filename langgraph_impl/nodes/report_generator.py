"""Node: generate_report — serializes DriftState to drift_report.json."""

import json
import logging
from datetime import datetime, timezone

from langgraph_impl.state import DriftState

logger = logging.getLogger(__name__)


def generate_report(state: DriftState) -> dict:
    """Write all drift findings from state to a JSON report file.

    Handles partial state gracefully — if an error occurred earlier in the pipeline,
    the available fields are still written so the report is always produced.

    Args:
        state: Current DriftState (may be partially populated if error occurred).

    Returns:
        Dict with key: report_path.
    """
    output_path = state.get("report_path", "drift_report.json")

    def _dump_list(key: str) -> list:
        return [i.model_dump() for i in state.get(key, [])]

    report = {
        "metadata": {
            "reference_path": state.get("reference_path", ""),
            "new_path": state.get("new_path", ""),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "framework": "langgraph_impl",
        },
        "schema_profile": _dump_list("column_profiles"),
        "schema_insights": _dump_list("schema_insights"),
        "distribution_insights": _dump_list("distribution_insights"),
        "pattern_insights": _dump_list("pattern_insights"),
        "all_insights": _dump_list("all_insights"),
        "overall_severity": state.get("overall_severity", "Unknown"),
        "llm_summary": state.get("llm_summary", ""),
        "error": state.get("error"),
    }

    try:
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Drift report written to: %s", output_path)
    except Exception as exc:
        logger.exception("Failed to write report to '%s'", output_path)
        output_path = "drift_report_fallback.json"
        with open(output_path, "w") as f:
            json.dump({"error": str(exc), "partial_report": report}, f, indent=2)

    return {"report_path": output_path}
