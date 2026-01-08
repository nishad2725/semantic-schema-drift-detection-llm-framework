"""Schema profiling for drift detection using LLM."""

from langchain_core.prompts import ChatPromptTemplate
from core.llm_client import get_llm
from core.models import ColumnProfile, DriftInsight
from core.system_prompt import SYSTEM_PROMPT
import pandas as pd

llm = get_llm()

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Column name: {column}
Sample values:
{samples}

Infer:
- semantic meaning
- role (identifier, metric, category)
- expected format
- business criticality

Return JSON.
""")
])

COLUMN_DRIFT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Schema changes detected:
{changes}

Analyze the impact of these column changes:
- Determine if drift is detected
- Assess severity (High/Moderate/Low)
- Explain why these changes matter for downstream analytics or ML
- Identify affected columns

Return JSON.
""")
])


def profile_schema(df: pd.DataFrame, source_id: str) -> list[ColumnProfile]:
    """
    Profile schema using LLM inference.
    
    Args:
        df: DataFrame to profile
        source_id: Source identifier for citation
        
    Returns:
        List of column profiles
    """
    profiles = []

    for col in df.columns:
        samples = df[col].dropna().astype(str).head(10).tolist()
        response = llm.with_structured_output(ColumnProfile).invoke(
            PROMPT.format(column=col, samples=samples)
        )
        response = response.model_copy(update={"source": source_id, "column_name": col})
        profiles.append(response)

    return profiles


def detect_column_drift(ref_df: pd.DataFrame, cur_df: pd.DataFrame, 
                       ref_source_id: str, cur_source_id: str) -> DriftInsight:
    """
    Detect column drift between reference and current datasets.
    
    Args:
        ref_df: Reference DataFrame
        cur_df: Current DataFrame
        ref_source_id: Reference dataset source identifier for citation
        cur_source_id: Current dataset source identifier for citation
        
    Returns:
        DriftInsight about column changes
    """
    ref_columns = set(ref_df.columns)
    cur_columns = set(cur_df.columns)
    
    added_columns = cur_columns - ref_columns
    removed_columns = ref_columns - cur_columns
    
    # If no changes, return a no-drift insight
    if not added_columns and not removed_columns:
        return DriftInsight(
            drift_detected=False,
            severity="Low",
            explanation="No column changes detected. Schema structure remains consistent.",
            affected_columns=[],
            source=cur_source_id
        )
    
    # Determine the appropriate source citation:
    # - If there are added columns, cite the new dataset (where they come from)
    # - If only removed columns, cite the reference dataset (where they were removed from)
    # - If both, prioritize the new dataset since added columns are more significant
    if added_columns:
        citation_source = cur_source_id
    else:
        citation_source = ref_source_id
    
    # Build description of changes
    changes_description = []
    if added_columns:
        # Get sample values for new columns
        new_cols_info = []
        for col in added_columns:
            samples = cur_df[col].dropna().astype(str).head(5).tolist()
            new_cols_info.append(f"- Added column '{col}' with sample values: {samples}")
        changes_description.append(f"New columns added:\n" + "\n".join(new_cols_info))
    
    if removed_columns:
        changes_description.append(f"Removed columns: {', '.join(removed_columns)}")
    
    changes_str = "\n\n".join(changes_description)
    
    # Use LLM to reason about the impact
    response = llm.with_structured_output(DriftInsight).invoke(
        COLUMN_DRIFT_PROMPT.format(changes=changes_str)
    )
    
    # Update with actual affected columns and correct source citation
    affected_cols = list(added_columns) + list(removed_columns)
    response = response.model_copy(update={
        "affected_columns": affected_cols,
        "source": citation_source
    })
    
    return response

