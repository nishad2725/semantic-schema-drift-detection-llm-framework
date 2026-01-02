"""Data models for the drift detection framework."""

from pydantic import BaseModel
from typing import List, Optional

class ColumnProfile(BaseModel):
    """Profile of a single column."""
    column_name: str
    semantic_type: str
    data_role: str
    expected_format: str
    business_criticality: str
    source: str


class DriftInsight(BaseModel):
    """Insight about detected drift."""
    drift_detected: bool
    severity: str
    explanation: str
    affected_columns: List[str]
    source: str

