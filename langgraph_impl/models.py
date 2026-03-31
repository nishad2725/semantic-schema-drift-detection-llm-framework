"""Data models for the LangGraph drift detection framework."""

from pydantic import BaseModel
from typing import List


class ColumnProfile(BaseModel):
    """Semantic profile of a single dataset column, inferred by LLM."""

    column_name: str
    semantic_type: str
    data_role: str
    expected_format: str
    business_criticality: str
    source: str


class DriftInsight(BaseModel):
    """Detected drift signal for one or more columns."""

    drift_detected: bool
    severity: str
    explanation: str
    affected_columns: List[str]
    source: str


class DriftSummary(BaseModel):
    """Overall drift synthesis produced by the drift_reasoner node."""

    overall_severity: str
    llm_summary: str
    affected_columns: List[str]
    drift_detected: bool
