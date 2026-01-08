"""Streamlit UI for AI-Native Data Drift Monitoring."""

import streamlit as st
import json
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
        st.info("Please run `python cli.py` first to generate the drift report.")
        st.stop()
    
    with open(report_file, "r") as f:
        return json.load(f)


# Try to load the report
try:
    report = load_report()
except Exception as e:
    st.error(f"Error loading report: {e}")
    st.stop()

# ---------- Sidebar ----------
st.sidebar.header("📂 Data Sources")
sources = set()

# Collect all sources from the report
for section in ["schema_profile", "column_drift", "distribution_drift", "pattern_drift", "overall_summary"]:
    section_data = report.get(section, [])
    if isinstance(section_data, list):
        for item in section_data:
            if isinstance(item, dict) and "source" in item:
                sources.add(item.get("source"))
    elif isinstance(section_data, dict) and "source" in section_data:
        sources.add(section_data.get("source"))

if sources:
    st.sidebar.markdown("**Reference Sources:**")
    for src in sorted(sources):
        # Highlight reference vs new data
        if "reference" in src.lower():
            st.sidebar.markdown(f"- **[{src}]** 📊")
        elif "new" in src.lower() or "drift" in src.lower():
            st.sidebar.markdown(f"- **[{src}]** 🔄")
        else:
            st.sidebar.markdown(f"- **[{src}]**")
else:
    st.sidebar.info("No sources found in report")

# ---------- Schema Profile ----------
st.header("📐 Schema Understanding (LLM-Inferred)")

if report.get("schema_profile"):
    schema_df = pd.DataFrame(report["schema_profile"])
    
    # Display with better formatting
    st.dataframe(
        schema_df[["column_name", "semantic_type", "data_role", "expected_format", "business_criticality", "source"]],
        use_container_width=True,
        hide_index=True
    )
    
    st.info(
        "💡 Schema inferred dynamically by the LLM without predefined contracts. "
        "This enables support for unknown client schemas."
    )
else:
    st.warning("No schema profile data available.")

# ---------- Column Drift ----------
st.header("📋 Column Drift Detection")

column_drift = report.get("column_drift", {})

if column_drift:
    drift_detected = column_drift.get("drift_detected", False)
    severity = column_drift.get("severity", "Unknown")
    affected_cols = column_drift.get("affected_columns", [])
    
    # Color code based on severity
    if severity.lower() == "high":
        severity_color = "🔴"
    elif severity.lower() == "medium":
        severity_color = "🟡"
    else:
        severity_color = "🟢"
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Drift Detected", "Yes" if drift_detected else "No")
    with col2:
        st.metric("Severity", severity)
    
    if affected_cols:
        st.markdown("**Affected Columns:**")
        # Separate added and removed columns if possible
        # For now, just show all affected columns
        cols_display = ", ".join([f"`{col}`" for col in affected_cols])
        st.markdown(cols_display)
    
    st.markdown("**AI Explanation:**")
    
    # Color code the explanation box
    if drift_detected:
        if severity.lower() == "high":
            st.error(column_drift.get("explanation", "No explanation available."))
        elif severity.lower() == "medium":
            st.warning(column_drift.get("explanation", "No explanation available."))
        else:
            st.info(column_drift.get("explanation", "No explanation available."))
    else:
        st.success(column_drift.get("explanation", "No explanation available."))
    
    st.markdown(f"**Source Citation:** `[{column_drift.get('source', 'Unknown')}]`")
else:
    st.success("✅ No column drift detected.")

# ---------- Distribution Drift ----------
st.header("📊 Distribution Drift Detection")

distribution_drifts = report.get("distribution_drift", [])

if distribution_drifts:
    for drift in distribution_drifts:
        col_name = drift.get("affected_columns", ["Unknown"])[0]
        drift_detected = drift.get("drift_detected", False)
        severity = drift.get("severity", "Unknown")
        
        # Color code based on severity
        if severity.lower() == "high":
            severity_color = "🔴"
        elif severity.lower() == "medium":
            severity_color = "🟡"
        else:
            severity_color = "🟢"
        
        with st.expander(f"{severity_color} Column: **{col_name}**"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Drift Detected", "Yes" if drift_detected else "No")
            with col2:
                st.metric("Severity", severity)
            
            st.markdown("**AI Explanation:**")
            st.write(drift.get("explanation", "No explanation available."))
            
            st.markdown(f"**Source Citation:** `[{drift.get('source', 'Unknown')}]`")
else:
    st.success("✅ No distribution drift detected.")

# ---------- Pattern Drift ----------
st.header("🔤 Pattern Drift Detection (Identifiers / Codes)")

pattern_drifts = report.get("pattern_drift", [])

if pattern_drifts:
    for drift in pattern_drifts:
        col_name = drift.get("affected_columns", ["Unknown"])[0]
        drift_detected = drift.get("drift_detected", False)
        severity = drift.get("severity", "Unknown")
        
        # Color code based on severity
        if severity.lower() == "high":
            severity_color = "🔴"
        elif severity.lower() == "medium":
            severity_color = "🟡"
        else:
            severity_color = "🟢"
        
        with st.expander(f"{severity_color} Column: **{col_name}**"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Drift Detected", "Yes" if drift_detected else "No")
            with col2:
                st.metric("Severity", severity)
            
            st.markdown("**AI Explanation:**")
            st.write(drift.get("explanation", "No explanation available."))
            
            st.markdown(f"**Source Citation:** `[{drift.get('source', 'Unknown')}]`")
else:
    st.success("✅ No pattern drift detected.")

# ---------- Overall Summary ----------
st.header("🧠 Overall Drift Assessment")

summary = report.get("overall_summary", {})

if summary:
    drift_detected = summary.get("drift_detected", False)
    severity = summary.get("severity", "Unknown")
    
    # Create columns for metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall Drift Detected", "Yes" if drift_detected else "No")
    with col2:
        st.metric("Overall Severity", severity)
    
    st.markdown("**AI-Generated Summary:**")
    
    # Color code the explanation box
    if drift_detected:
        if severity.lower() == "high":
            st.error(summary.get("explanation", "No explanation available."))
        elif severity.lower() == "medium":
            st.warning(summary.get("explanation", "No explanation available."))
        else:
            st.info(summary.get("explanation", "No explanation available."))
    else:
        st.success(summary.get("explanation", "No explanation available."))
    
    affected_cols = summary.get("affected_columns", [])
    if affected_cols:
        st.markdown("**Affected Columns:**")
        cols_display = ", ".join([f"`{col}`" for col in affected_cols])
        st.markdown(cols_display)
    
    st.markdown(f"**Primary Source:** `[{summary.get('source', 'Unknown')}]`")
else:
    st.warning("No overall summary available.")

# ---------- Footer ----------
st.divider()
st.caption(
    "💡 This UI demonstrates AI-native drift reasoning with transparent explanations "
    "and document-level citations. The UI is intentionally minimal to showcase the core "
    "intelligence: observable drift, explainable AI reasoning, and trustworthy citations."
)

# ---------- Additional Info ----------
with st.expander("ℹ️ About This UI"):
    st.markdown("""
    **Purpose:**
    - Visualize AI-generated drift insights
    - Display source citations for transparency
    - Make drift detection results human-consumable
    
    **Key Features:**
    - Schema inference without predefined contracts
    - Distribution and pattern drift detection
    - AI-powered explanations with citations
    - Severity-based color coding
    
    **Note:** This UI is intentionally minimal. Its goal is to visualize AI-generated drift 
    insights and citations, not to replace a production dashboard.
    """)
