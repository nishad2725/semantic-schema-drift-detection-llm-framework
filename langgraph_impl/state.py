"""DriftState TypedDict — single source of truth for all graph state."""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING
from typing_extensions import TypedDict

if TYPE_CHECKING:
    import pandas as pd
    from langgraph_impl.models import ColumnProfile, DriftInsight


class DriftState(TypedDict):
    """State object passed through every node in the drift detection graph.

    DataFrames (reference_df, new_df) are held in-memory only.
    Do not attach a LangGraph checkpointer without a custom DataFrame serializer.
    """

    # --- Inputs ---
    reference_path: str
    new_path: str

    # --- Loaded data (not checkpointed) ---
    reference_df: Optional[object]   # pd.DataFrame
    new_df: Optional[object]         # pd.DataFrame

    # --- Schema profiling ---
    column_profiles: list           # list[ColumnProfile]
    schema_insights: list           # list[DriftInsight]: volume + dtype + column structure

    # --- Parallel profiler outputs ---
    distribution_insights: list     # list[DriftInsight]: numeric distribution + cardinality
    pattern_insights: list          # list[DriftInsight]: format/pattern + referential integrity

    # --- Consolidated ---
    all_insights: list              # list[DriftInsight]: merged by reason_drift node

    # --- Reasoner outputs ---
    overall_severity: str           # "High" | "Moderate" | "Low" | "None"
    llm_summary: str

    # --- Report ---
    report_path: str

    # --- Error handling ---
    error: Optional[str]
