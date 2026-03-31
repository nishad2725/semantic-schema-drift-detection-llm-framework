"""Node: profile_patterns — string pattern drift and referential integrity drift."""

import logging

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from langgraph_impl.llm_client import get_llm
from langgraph_impl.models import ColumnProfile, DriftInsight
from langgraph_impl.state import DriftState
from langgraph_impl.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_PATTERN_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Analyze structure and pattern drift for column '{column}':

Reference values (sample):
{ref_values}

New dataset values (sample):
{cur_values}

Infer whether the format, structure, or semantic pattern of values has changed.
Explain the downstream risk (e.g., ID matching failures, parsing errors).

Return JSON with fields: drift_detected, severity, explanation, affected_columns, source.
"""),
])

_REFERENTIAL_INTEGRITY_THRESHOLD = 0.50
_LARGE_DATASET_ROW_LIMIT = 500_000


def profile_patterns(state: DriftState) -> dict:
    """Detect string pattern drift and referential integrity drift for identifier columns.

    For each object column: sends 10 samples from both datasets to LLM.
    For identifier columns (data_role=="identifier" from column_profiles):
      checks if >50% of reference values are absent from new dataset, or vice versa.
      Skipped for datasets exceeding 500k rows (performance guard).

    Args:
        state: Current DriftState containing reference_df, new_df, column_profiles, new_path.

    Returns:
        Dict with key: pattern_insights.
    """
    ref_df: pd.DataFrame = state["reference_df"]
    new_df: pd.DataFrame = state["new_df"]
    new_source = state["new_path"]
    column_profiles: list[ColumnProfile] = state.get("column_profiles", [])

    llm = get_llm()
    insights: list[DriftInsight] = []

    # --- LLM: string pattern drift ---
    for col in ref_df.select_dtypes(include="object").columns:
        if col not in new_df.columns:
            continue

        ref_vals = ref_df[col].dropna().astype(str).head(10).tolist()
        cur_vals = new_df[col].dropna().astype(str).head(10).tolist()

        try:
            response: DriftInsight = llm.with_structured_output(DriftInsight).invoke(
                _PATTERN_PROMPT.format_messages(
                    column=col,
                    ref_values=ref_vals,
                    cur_values=cur_vals,
                )
            )
            response = response.model_copy(update={"affected_columns": [col], "source": new_source})
            insights.append(response)
            logger.debug("Pattern drift for '%s': detected=%s", col, response.drift_detected)
        except Exception as exc:
            logger.warning("LLM pattern assessment failed for '%s': %s", col, exc)

    # --- Deterministic: referential integrity drift for identifier columns ---
    id_cols = {
        p.column_name
        for p in column_profiles
        if p.data_role.lower() == "identifier"
    }

    large_dataset = len(ref_df) > _LARGE_DATASET_ROW_LIMIT or len(new_df) > _LARGE_DATASET_ROW_LIMIT
    if large_dataset and id_cols:
        logger.info(
            "Skipping referential integrity check — dataset exceeds %d rows",
            _LARGE_DATASET_ROW_LIMIT,
        )

    if not large_dataset:
        for col in id_cols:
            if col not in ref_df.columns or col not in new_df.columns:
                continue

            ref_vals_set = set(ref_df[col].dropna().astype(str))
            new_vals_set = set(new_df[col].dropna().astype(str))

            if not ref_vals_set:
                continue

            lost = ref_vals_set - new_vals_set
            novel = new_vals_set - ref_vals_set
            lost_pct = len(lost) / len(ref_vals_set)
            novel_pct = len(novel) / max(len(new_vals_set), 1)

            if lost_pct > _REFERENTIAL_INTEGRITY_THRESHOLD or novel_pct > _REFERENTIAL_INTEGRITY_THRESHOLD:
                insights.append(
                    DriftInsight(
                        drift_detected=True,
                        severity="High",
                        explanation=(
                            f"Referential integrity drift in '{col}': "
                            f"{lost_pct:.1%} of reference values absent in new dataset, "
                            f"{novel_pct:.1%} of new values are novel. "
                            "Joins and lookups using this key will produce mismatches."
                        ),
                        affected_columns=[col],
                        source=new_source,
                    )
                )
                logger.info(
                    "Referential integrity drift in '%s': lost=%.1f%%, novel=%.1f%%",
                    col,
                    lost_pct * 100,
                    novel_pct * 100,
                )

    return {"pattern_insights": insights}
