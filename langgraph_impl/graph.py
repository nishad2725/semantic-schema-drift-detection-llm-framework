"""LangGraph StateGraph construction for the drift detection pipeline."""

import logging

from langgraph.graph import END, START, StateGraph

from langgraph_impl.nodes.data_loader import load_data
from langgraph_impl.nodes.distribution_profiler import profile_distributions
from langgraph_impl.nodes.drift_reasoner import reason_drift
from langgraph_impl.nodes.pattern_profiler import profile_patterns
from langgraph_impl.nodes.report_generator import generate_report
from langgraph_impl.nodes.schema_profiler import profile_schema
from langgraph_impl.state import DriftState

logger = logging.getLogger(__name__)


def _route_after_load(state: DriftState) -> str:
    """Conditional routing after load_data.

    If data loading failed (error is set), skip all profilers and write
    a partial error report immediately. Otherwise continue to schema profiling.

    Args:
        state: Current DriftState.

    Returns:
        Node name to route to: "generate_report" or "profile_schema".
    """
    if state.get("error"):
        logger.warning("Load error detected — routing to generate_report: %s", state["error"])
        return "generate_report"
    return "profile_schema"


def build_graph():
    """Construct and compile the drift detection StateGraph.

    Graph topology:
        START → load_data → [conditional] → profile_schema
                                         → generate_report (on error)
        profile_schema → profile_distributions ─┐
                       → profile_patterns       ─┤→ reason_drift → generate_report → END

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    graph = StateGraph(DriftState)

    # --- Register nodes ---
    graph.add_node("load_data", load_data)
    graph.add_node("profile_schema", profile_schema)
    graph.add_node("profile_distributions", profile_distributions)
    graph.add_node("profile_patterns", profile_patterns)
    graph.add_node("reason_drift", reason_drift)
    graph.add_node("generate_report", generate_report)

    # --- Entry ---
    graph.add_edge(START, "load_data")

    # --- Conditional: error fast-path ---
    graph.add_conditional_edges(
        "load_data",
        _route_after_load,
        {
            "generate_report": "generate_report",
            "profile_schema": "profile_schema",
        },
    )

    # --- Fan-out: schema → parallel profilers ---
    graph.add_edge("profile_schema", "profile_distributions")
    graph.add_edge("profile_schema", "profile_patterns")

    # --- Fan-in: both profilers must complete before reason_drift ---
    graph.add_edge("profile_distributions", "reason_drift")
    graph.add_edge("profile_patterns", "reason_drift")

    # --- Final steps ---
    graph.add_edge("reason_drift", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()
