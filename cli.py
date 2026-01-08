"""Command-line interface for LLM drift detection framework."""

from ingestion.data_loader import load_dataset
from core.schema_profiler import profile_schema, detect_column_drift
from core.distribution_profiler import profile_distribution
from core.pattern_profiler import profile_patterns
from core.drift_reasoner import reason_overall_drift
from report.report_generator import generate_report


def main():
    """Main CLI entry point."""
    ref = load_dataset("data/reference_data_tc4.csv")
    cur = load_dataset("data/new_data_with_drift_tc4.csv")

    schema = profile_schema(ref, "reference_data_tc4.csv")
    column_drift = detect_column_drift(ref, cur, "reference_data_tc4.csv", "new_data_with_drift_tc4.csv")
    dist = profile_distribution(ref, cur, "reference_data_tc4.csv")
    pattern = profile_patterns(ref, cur, "reference_data_tc4.csv")


    summary = reason_overall_drift(
        [d.model_dump() for d in [column_drift] + dist + pattern],
        "reference_data_tc4.csv"
    )

    generate_report(schema, column_drift, dist, pattern, summary, "drift_report.json")


if __name__ == "__main__":
    main()

