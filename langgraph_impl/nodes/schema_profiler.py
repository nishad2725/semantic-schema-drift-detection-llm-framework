"""Node: profile_schema — LLM column inference, column drift, and data type drift."""

import logging

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate

from langgraph_impl.llm_client import get_llm
from langgraph_impl.models import ColumnProfile, DriftInsight
from langgraph_impl.state import DriftState
from langgraph_impl.system_prompt import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_COLUMN_PROFILE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Column name: {column}
Sample values:
{samples}

Infer:
- semantic meaning (semantic_type)
- role (data_role: identifier, metric, category, timestamp, text, or other)
- expected format (expected_format)
- business criticality (business_criticality: critical, high, medium, or low)

Return JSON with fields: column_name, semantic_type, data_role, expected_format, business_criticality, source.
"""),
])

_COLUMN_DRIFT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Schema changes detected between reference and new dataset:
{changes}

Analyze the impact of these column changes:
- Determine if drift is detected (drift_detected: true/false)
- Assess severity (High / Moderate / Low)
- Explain why these changes matter for downstream analytics or ML
- List the affected column names

Return JSON with fields: drift_detected, severity, explanation, affected_columns, source.
"""),
])


def profile_schema(state: DriftState) -> dict:
    """Infer semantic column profiles, detect column structure drift, and detect data type drift.

    Extends schema_insights (initialized by load_data) with:
    - One DriftInsight for added/removed columns (LLM-reasoned)
    - One DriftInsight per dtype-changed column pair (deterministic)

    Args:
        state: Current DriftState containing reference_df, new_df, schema_insights.

    Returns:
        Dict with keys: column_profiles, schema_insights.
    """
    ref_df: pd.DataFrame = state["reference_df"]
    new_df: pd.DataFrame = state["new_df"]
    ref_source = state["reference_path"]
    new_source = state["new_path"]

    llm = get_llm()
    profiles: list[ColumnProfile] = []
    new_insights: list[DriftInsight] = []

    # --- LLM: per-column semantic profiling ---
    for col in ref_df.columns:
        samples = ref_df[col].dropna().astype(str).head(10).tolist()
        try:
            response: ColumnProfile = llm.with_structured_output(ColumnProfile).invoke(
                _COLUMN_PROFILE_PROMPT.format_messages(column=col, samples=samples)
            )
            response = response.model_copy(update={"source": ref_source, "column_name": col})
            profiles.append(response)
            logger.debug("Profiled column '%s': role=%s", col, response.data_role)
        except Exception as exc:
            logger.warning("Failed to profile column '%s': %s", col, exc)
            profiles.append(
                ColumnProfile(
                    column_name=col,
                    semantic_type="unknown",
                    data_role="unknown",
                    expected_format="unknown",
                    business_criticality="low",
                    source=ref_source,
                )
            )

    # --- LLM: column addition/removal drift ---
    ref_cols = set(ref_df.columns)
    new_cols = set(new_df.columns)
    added = new_cols - ref_cols
    removed = ref_cols - new_cols

    if added or removed:
        changes_parts = []
        if added:
            cols_info = []
            for col in added:
                samples = new_df[col].dropna().astype(str).head(5).tolist()
                cols_info.append(f"- Added '{col}' with samples: {samples}")
            changes_parts.append("New columns added:\n" + "\n".join(cols_info))
        if removed:
            changes_parts.append(f"Removed columns: {', '.join(removed)}")

        citation = new_source if added else ref_source
        try:
            col_drift: DriftInsight = llm.with_structured_output(DriftInsight).invoke(
                _COLUMN_DRIFT_PROMPT.format_messages(changes="\n\n".join(changes_parts))
            )
            col_drift = col_drift.model_copy(update={
                "affected_columns": list(added) + list(removed),
                "source": citation,
            })
            new_insights.append(col_drift)
            logger.info(
                "Column drift detected — added: %s, removed: %s", list(added), list(removed)
            )
        except Exception as exc:
            logger.warning("LLM column drift assessment failed: %s", exc)
            new_insights.append(
                DriftInsight(
                    drift_detected=True,
                    severity="Moderate",
                    explanation=f"Column changes detected but LLM assessment failed: {exc}",
                    affected_columns=list(added) + list(removed),
                    source=citation,
                )
            )
    else:
        logger.info("No column addition/removal detected")

    # --- Deterministic: data type drift ---
    common_cols = ref_cols & new_cols
    dtype_changes = []
    dtype_affected = []
    for col in common_cols:
        ref_dtype = str(ref_df[col].dtype)
        new_dtype = str(new_df[col].dtype)
        if ref_dtype != new_dtype:
            dtype_changes.append(f"'{col}': {ref_dtype} → {new_dtype}")
            dtype_affected.append(col)

    if dtype_changes:
        new_insights.append(
            DriftInsight(
                drift_detected=True,
                severity="Moderate",
                explanation=(
                    f"Data type changes detected: {'; '.join(dtype_changes)}. "
                    "Type coercions may cause silent failures in downstream parsing."
                ),
                affected_columns=dtype_affected,
                source=new_source,
            )
        )
        logger.info("Data type drift in %d column(s)", len(dtype_affected))

    return {
        "column_profiles": profiles,
        "schema_insights": state["schema_insights"] + new_insights,
    }
