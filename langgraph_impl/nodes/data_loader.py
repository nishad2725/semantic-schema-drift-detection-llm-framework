"""Node: load_data — loads reference and new datasets, detects volume drift."""

import logging
from pathlib import Path

import pandas as pd

from langgraph_impl.models import DriftInsight
from langgraph_impl.state import DriftState

logger = logging.getLogger(__name__)


def _load(path: str) -> pd.DataFrame:
    """Load a dataset from CSV, Excel, or pipe-delimited TXT.

    Args:
        path: File path to load.

    Returns:
        Loaded DataFrame.

    Raises:
        ValueError: If the file extension is not supported.
    """
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in (".xls", ".xlsx"):
        return pd.read_excel(path)
    if ext == ".txt":
        return pd.read_csv(path, delimiter="|")
    raise ValueError(f"Unsupported file format: {ext}")


def load_data(state: DriftState) -> dict:
    """Load reference and new datasets and detect volume drift.

    Populates reference_df and new_df. If row counts differ by more than 20%,
    a DriftInsight is appended to schema_insights.

    Args:
        state: Current DriftState.

    Returns:
        Dict with keys: reference_df, new_df, schema_insights, error.
    """
    try:
        ref_df = _load(state["reference_path"])
        new_df = _load(state["new_path"])
        logger.info(
            "Loaded datasets — reference: %d rows, new: %d rows",
            len(ref_df),
            len(new_df),
        )

        schema_insights: list[DriftInsight] = []

        # Volume drift check (deterministic — no LLM)
        ref_count = len(ref_df)
        new_count = len(new_df)
        if ref_count > 0:
            pct_change = abs(new_count - ref_count) / ref_count
            if pct_change > 0.20:
                severity = "High" if pct_change > 0.40 else "Moderate"
                schema_insights.append(
                    DriftInsight(
                        drift_detected=True,
                        severity=severity,
                        explanation=(
                            f"Row count changed by {pct_change:.1%} "
                            f"(reference: {ref_count:,}, new: {new_count:,}). "
                            "Significant volume shift may indicate data truncation, "
                            "source system change, or ingestion error."
                        ),
                        affected_columns=[],
                        source=state["new_path"],
                    )
                )
                logger.info("Volume drift detected: %.1f%%", pct_change * 100)

        return {
            "reference_df": ref_df,
            "new_df": new_df,
            "schema_insights": schema_insights,
            "error": None,
        }

    except Exception as exc:
        logger.exception("Data loading failed")
        return {
            "reference_df": None,
            "new_df": None,
            "schema_insights": [],
            "error": str(exc),
        }
