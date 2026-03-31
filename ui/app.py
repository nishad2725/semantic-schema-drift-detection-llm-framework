"""Streamlit UI for AI-Native Data Drift Monitoring."""

import json
import streamlit as st
import pandas as pd
from pathlib import Path


# ---------- Page Config ----------
st.set_page_config(
    page_title="AI-Native Data Drift Monitor",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧠 AI-Native Data Drift Monitoring")
st.caption("LLM-powered schema & data drift detection with source citations")


# ---------- Load Report ----------
@st.cache_data
def load_report(report_path: str = "drift_report.json"):
    """Load drift report from JSON file."""
    report_file = Path(report_path)
    if not report_file.exists():
        st.error(f"Report file not found: {report_path}")
        st.info("Run `python cli.py` (or `python langgraph_impl/cli.py`) to generate the report.")
        st.stop()
    with open(report_file, "r") as f:
        return json.load(f)


try:
    report = load_report()
except Exception as e:
    st.error(f"Error loading report: {e}")
    st.stop()

# ---------- Error banner ----------
if report.get("error"):
    st.error(f"Pipeline error: {report['error']}")
    st.warning("Report may be incomplete.")


# ---------- Helpers ----------
def severity_icon(severity: str) -> str:
    s = severity.lower()
    if s == "high":
        return "🔴"
    if s in ("moderate", "medium"):
        return "🟡"
    if s == "low":
        return "🟢"
    return "⚪"


def render_insight_box(insight: dict) -> None:
    """Render a single DriftInsight dict as a labeled box."""
    detected = insight.get("drift_detected", False)
    severity = insight.get("severity", "Unknown")
    explanation = insight.get("explanation", "No explanation available.")
    source = insight.get("source", "Unknown")
    cols = insight.get("affected_columns", [])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Drift Detected", "Yes" if detected else "No")
    with col2:
        st.metric("Severity", severity)

    if cols:
        st.markdown("**Affected Columns:** " + ", ".join(f"`{c}`" for c in cols))

    if detected:
        if severity.lower() == "high":
            st.error(explanation)
        elif severity.lower() in ("moderate", "medium"):
            st.warning(explanation)
        else:
            st.info(explanation)
    else:
        st.success(explanation)

    st.markdown(f"**Source Citation:** `[{source}]`")


# ---------- Sidebar: metadata + sources ----------
st.sidebar.header("📂 Run Metadata")
meta = report.get("metadata", {})
if meta:
    st.sidebar.markdown(f"**Reference:** `{Path(meta.get('reference_path', '')).name}`")
    st.sidebar.markdown(f"**New:** `{Path(meta.get('new_path', '')).name}`")
    generated = meta.get("generated_at", "")
    if generated:
        st.sidebar.markdown(f"**Generated:** {generated[:19].replace('T', ' ')} UTC")
    st.sidebar.markdown(f"**Framework:** `{meta.get('framework', 'unknown')}`")
else:
    st.sidebar.info("No metadata in report")

st.sidebar.divider()
st.sidebar.header("🗂 Sources")
sources = set()
for section in ("schema_insights", "distribution_insights", "pattern_insights", "all_insights"):
    for item in report.get(section, []):
        if isinstance(item, dict) and item.get("source"):
            sources.add(item["source"])
for item in report.get("schema_profile", []):
    if isinstance(item, dict) and item.get("source"):
        sources.add(item["source"])

if sources:
    for src in sorted(sources):
        name = Path(src).name
        icon = "📊" if "reference" in src.lower() else "🔄"
        st.sidebar.markdown(f"- {icon} `{name}`")
else:
    st.sidebar.info("No sources found in report")


# ---------- Overall severity banner ----------
overall_severity = report.get("overall_severity", "")
llm_summary = report.get("llm_summary", "")

if overall_severity:
    icon = severity_icon(overall_severity)
    if overall_severity.lower() == "high":
        st.error(f"{icon} **Overall Severity: {overall_severity}**")
    elif overall_severity.lower() in ("moderate", "medium"):
        st.warning(f"{icon} **Overall Severity: {overall_severity}**")
    else:
        st.success(f"{icon} **Overall Severity: {overall_severity}**")


# ---------- Schema Profile ----------
st.header("📐 Schema Understanding (LLM-Inferred)")

if report.get("schema_profile"):
    schema_df = pd.DataFrame(report["schema_profile"])
    display_cols = [c for c in
        ["column_name", "semantic_type", "data_role", "expected_format", "business_criticality", "source"]
        if c in schema_df.columns]
    st.dataframe(schema_df[display_cols], use_container_width=True, hide_index=True)
    st.info(
        "💡 Schema inferred dynamically by the LLM without predefined contracts. "
        "This enables support for unknown client schemas."
    )
else:
    st.warning("No schema profile data available.")


# ---------- Schema Insights ----------
st.header("📋 Schema Drift (Column Structure, Volume & Type Changes)")

schema_insights = report.get("schema_insights", [])
if schema_insights:
    for insight in schema_insights:
        cols = insight.get("affected_columns", [])
        col_label = cols[0] if cols else "Dataset-level"
        sev = insight.get("severity", "")
        with st.expander(f"{severity_icon(sev)} {col_label} — {sev}"):
            render_insight_box(insight)
else:
    st.success("✅ No schema drift detected.")


# ---------- Distribution Drift ----------
st.header("📊 Distribution Drift (Numeric & Cardinality)")

distribution_insights = report.get("distribution_insights", [])
if distribution_insights:
    for insight in distribution_insights:
        col_name = (insight.get("affected_columns") or ["Unknown"])[0]
        sev = insight.get("severity", "")
        with st.expander(f"{severity_icon(sev)} Column: **{col_name}** — {sev}"):
            render_insight_box(insight)
else:
    st.success("✅ No distribution drift detected.")


# ---------- Pattern Drift ----------
st.header("🔤 Pattern Drift (Format, Structure & Referential Integrity)")

pattern_insights = report.get("pattern_insights", [])
if pattern_insights:
    for insight in pattern_insights:
        col_name = (insight.get("affected_columns") or ["Unknown"])[0]
        sev = insight.get("severity", "")
        with st.expander(f"{severity_icon(sev)} Column: **{col_name}** — {sev}"):
            render_insight_box(insight)
else:
    st.success("✅ No pattern drift detected.")


# ---------- Overall Summary ----------
st.header("🧠 Overall Drift Assessment")

if overall_severity or llm_summary:
    col1, col2 = st.columns(2)
    with col1:
        all_insights = report.get("all_insights", [])
        detected_count = sum(1 for i in all_insights if i.get("drift_detected"))
        st.metric("Insights with Drift", f"{detected_count} / {len(all_insights)}")
    with col2:
        st.metric("Overall Severity", overall_severity or "N/A")

    if llm_summary:
        st.markdown("**AI-Generated Summary:**")
        sev = overall_severity or ""
        if sev.lower() == "high":
            st.error(llm_summary)
        elif sev.lower() in ("moderate", "medium"):
            st.warning(llm_summary)
        else:
            st.info(llm_summary)

    # Affected columns across all insights
    affected = []
    for i in report.get("all_insights", []):
        if i.get("drift_detected"):
            affected.extend(i.get("affected_columns", []))
    affected = sorted(set(affected))
    if affected:
        st.markdown("**All Affected Columns:** " + ", ".join(f"`{c}`" for c in affected))
else:
    st.warning("No overall assessment available.")


# ---------- Footer ----------
st.divider()
st.caption(
    "💡 This UI demonstrates AI-native drift reasoning with transparent explanations "
    "and document-level citations. The UI is intentionally minimal to showcase the core "
    "intelligence: observable drift, explainable AI reasoning, and trustworthy citations."
)

with st.expander("ℹ️ About This UI"):
    st.markdown("""
    **Purpose:**
    - Visualize AI-generated drift insights from the LangGraph pipeline
    - Display source citations for transparency
    - Make drift detection results human-consumable

    **Drift Types Displayed:**
    - Schema: column additions/removals, data type changes, volume shift
    - Distribution: numeric distribution, cardinality changes
    - Pattern: string format/structure, referential integrity

    **Report Format:** Generated by `langgraph_impl/nodes/report_generator.py`

    **Note:** This UI is intentionally minimal. Its goal is to visualize AI-generated drift
    insights and citations, not to replace a production dashboard.
    """)
