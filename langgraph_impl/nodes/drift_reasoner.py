"""Node: reason_drift — LLM synthesis of all drift signals into overall severity."""

import json
import logging

from langchain_core.prompts import ChatPromptTemplate

from langgraph_impl.llm_client import get_llm
from langgraph_impl.models import DriftInsight, DriftSummary
from langgraph_impl.state import DriftState
from langgraph_impl.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_VALID_SEVERITIES = {"High", "Moderate", "Low", "None"}

_REASON_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Given the following drift signals detected in dataset '{source_id}':

{signals}

Synthesize an overall assessment:
1. overall_severity: one of High / Moderate / Low / None
2. llm_summary: 2-4 sentences covering root causes and recommended actions
3. affected_columns: combined list of all columns with meaningful drift (drift_detected=true only)
4. drift_detected: true if any signal has drift_detected=true

Be concise and actionable. Return structured JSON.
"""),
])


def reason_drift(state: DriftState) -> dict:
    """Merge all drift signals and synthesize an overall severity assessment via LLM.

    Flattens schema_insights, distribution_insights, and pattern_insights into all_insights,
    then passes them to the LLM for holistic reasoning. Populates overall_severity and llm_summary
    as flat state keys (not a DriftInsight object).

    Args:
        state: Current DriftState with all three insight lists populated.

    Returns:
        Dict with keys: all_insights, overall_severity, llm_summary.
    """
    all_insights: list[DriftInsight] = (
        state.get("schema_insights", [])
        + state.get("distribution_insights", [])
        + state.get("pattern_insights", [])
    )

    if not all_insights:
        logger.info("No drift insights to reason over — returning 'None' severity")
        return {
            "all_insights": [],
            "overall_severity": "None",
            "llm_summary": "No drift signals detected across schema, distribution, or pattern checks.",
        }

    signals_str = json.dumps([i.model_dump() for i in all_insights], indent=2)
    source_id = state.get("new_path", "unknown")

    llm = get_llm()
    try:
        summary: DriftSummary = llm.with_structured_output(DriftSummary).invoke(
            _REASON_PROMPT.format_messages(signals=signals_str, source_id=source_id)
        )
        # Normalize severity to prevent unexpected values
        severity = summary.overall_severity if summary.overall_severity in _VALID_SEVERITIES else "Unknown"
        logger.info("Overall drift severity: %s", severity)
        return {
            "all_insights": all_insights,
            "overall_severity": severity,
            "llm_summary": summary.llm_summary,
        }
    except Exception as exc:
        logger.exception("LLM drift reasoning failed")
        return {
            "all_insights": all_insights,
            "overall_severity": "Unknown",
            "llm_summary": f"LLM reasoning failed: {exc}",
        }
