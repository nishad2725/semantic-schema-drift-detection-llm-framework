"""Report generation for drift detection results."""

import json
from core.models import ColumnProfile, DriftInsight


def generate_report(schema: list[ColumnProfile], distributions: list[DriftInsight], 
                   patterns: list[DriftInsight], summary: DriftInsight, 
                   output_path: str) -> None:
    """
    Generate a drift detection report.
    
    Args:
        schema: Schema profiles
        distributions: Distribution drift insights
        patterns: Pattern drift insights
        summary: Overall summary insight
        output_path: Path to save the report
    """
    report = {
        "schema_profile": [s.model_dump() for s in schema],
        "distribution_drift": [d.model_dump() for d in distributions],
        "pattern_drift": [p.model_dump() for p in patterns],
        "overall_summary": summary.model_dump()
    }

    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

