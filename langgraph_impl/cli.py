"""CLI entry point for the LangGraph drift detection pipeline."""

import argparse
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Parse arguments, invoke the drift detection graph, and print a summary."""
    parser = argparse.ArgumentParser(
        description="LangGraph-based semantic drift detection pipeline."
    )
    parser.add_argument(
        "--reference",
        default="data/reference_data.csv",
        help="Path to the reference dataset (default: data/reference_data.csv)",
    )
    parser.add_argument(
        "--new",
        dest="new_path",
        default="data/new_data_with_drift.csv",
        help="Path to the new dataset (default: data/new_data_with_drift.csv)",
    )
    parser.add_argument(
        "--output",
        default="drift_report.json",
        help="Output path for the drift report JSON (default: drift_report.json)",
    )
    args = parser.parse_args()

    from langgraph_impl.graph import build_graph

    initial_state = {
        "reference_path": args.reference,
        "new_path": args.new_path,
        "reference_df": None,
        "new_df": None,
        "column_profiles": [],
        "schema_insights": [],
        "distribution_insights": [],
        "pattern_insights": [],
        "all_insights": [],
        "overall_severity": "",
        "llm_summary": "",
        "report_path": args.output,
        "error": None,
    }

    logger.info("Starting drift detection pipeline")
    logger.info("  Reference : %s", args.reference)
    logger.info("  New       : %s", args.new_path)
    logger.info("  Output    : %s", args.output)

    graph = build_graph()
    final_state = graph.invoke(initial_state)

    # --- Summary output ---
    print("\n" + "=" * 60)
    print("DRIFT DETECTION SUMMARY")
    print("=" * 60)

    if final_state.get("error"):
        print(f"  ERROR: {final_state['error']}")
        print(f"  Report (partial): {final_state.get('report_path', 'N/A')}")
        sys.exit(1)

    print(f"  Overall Severity  : {final_state.get('overall_severity', 'N/A')}")
    print(f"  Schema insights   : {len(final_state.get('schema_insights', []))}")
    print(f"  Distribution      : {len(final_state.get('distribution_insights', []))}")
    print(f"  Pattern insights  : {len(final_state.get('pattern_insights', []))}")
    print(f"  Total insights    : {len(final_state.get('all_insights', []))}")
    print(f"  Report written to : {final_state.get('report_path', 'N/A')}")
    print()
    summary = final_state.get("llm_summary", "")
    if summary:
        print("LLM Summary:")
        for line in summary.strip().splitlines():
            print(f"  {line}")
    print("=" * 60)


if __name__ == "__main__":
    main()
