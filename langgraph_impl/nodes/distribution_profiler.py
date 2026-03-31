"""Node: profile_distributions — statistical distribution drift and cardinality drift."""

import logging

import numpy as np
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from langgraph_impl.llm_client import get_llm
from langgraph_impl.models import DriftInsight
from langgraph_impl.state import DriftState
from langgraph_impl.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_DIST_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Analyze distribution drift for column '{column}':

Reference statistics:
{ref_stats}

New dataset statistics:
{cur_stats}

Determine if meaningful drift exists. Note any significant changes in mean, standard deviation,
range, or percentiles. Explain the downstream risk.

Return JSON with fields: drift_detected, severity, explanation, affected_columns, source.
"""),
])


def profile_distributions(state: DriftState) -> dict:
    """Detect numerical distribution drift and categorical cardinality drift.

    For each numeric column: computes describe() stats and uses LLM to assess drift.
    For each object column: checks if unique value count changed by more than 30% (deterministic).

    Note: For large datasets (>500k rows), referential integrity checks are skipped
    for performance reasons. Cardinality checks remain fast via nunique().

    Args:
        state: Current DriftState containing reference_df, new_df, new_path.

    Returns:
        Dict with key: distribution_insights.
    """
    ref_df: pd.DataFrame = state["reference_df"]
    new_df: pd.DataFrame = state["new_df"]
    new_source = state["new_path"]

    llm = get_llm()
    insights: list[DriftInsight] = []

    # --- LLM: numerical distribution drift ---
    for col in ref_df.select_dtypes(include=np.number).columns:
        if col not in new_df.columns:
            continue

        ref_stats = ref_df[col].describe().to_dict()
        cur_stats = new_df[col].describe().to_dict()

        ref_str = "\n".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                            for k, v in ref_stats.items())
        cur_str = "\n".join(f"{k}: {v:.4f}" if isinstance(v, float) else f"{k}: {v}"
                            for k, v in cur_stats.items())

        try:
            response: DriftInsight = llm.with_structured_output(DriftInsight).invoke(
                _DIST_PROMPT.format_messages(
                    column=col,
                    ref_stats=ref_str,
                    cur_stats=cur_str,
                )
            )
            response = response.model_copy(update={"affected_columns": [col], "source": new_source})
            insights.append(response)
            logger.debug("Distribution drift for '%s': detected=%s", col, response.drift_detected)
        except Exception as exc:
            logger.warning("LLM distribution assessment failed for '%s': %s", col, exc)

    # --- Deterministic: cardinality drift for categorical columns ---
    for col in ref_df.select_dtypes(include="object").columns:
        if col not in new_df.columns:
            continue

        ref_card = ref_df[col].nunique()
        new_card = new_df[col].nunique()

        if ref_card == 0:
            continue

        pct = abs(new_card - ref_card) / ref_card
        if pct > 0.30:
            severity = "High" if pct > 0.60 else "Moderate"
            insights.append(
                DriftInsight(
                    drift_detected=True,
                    severity=severity,
                    explanation=(
                        f"Cardinality of '{col}' changed by {pct:.1%} "
                        f"(reference: {ref_card} unique values, new: {new_card}). "
                        "Suggests new categories, consolidation, or encoding change."
                    ),
                    affected_columns=[col],
                    source=new_source,
                )
            )
            logger.info("Cardinality drift in '%s': %.1f%%", col, pct * 100)

    return {"distribution_insights": insights}
