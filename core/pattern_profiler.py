"""Pattern profiling for drift detection using LLM."""

from langchain_core.prompts import ChatPromptTemplate
from core.llm_client import get_llm
from core.models import DriftInsight
from core.system_prompt import SYSTEM_PROMPT
import pandas as pd

llm = get_llm()

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Analyze the structure and intent of these string values.

Values:
{values}

Infer pattern and whether structure changed.
Explain downstream risk.
""")
])


def profile_patterns(ref_df: pd.DataFrame, cur_df: pd.DataFrame, source_id: str) -> list[DriftInsight]:
    """
    Profile pattern drift using LLM.
    
    Args:
        ref_df: Reference DataFrame
        cur_df: Current DataFrame
        source_id: Source identifier for citation
        
    Returns:
        List of drift insights
    """
    insights = []

    for col in ref_df.select_dtypes(include="object").columns:
        if col not in cur_df.columns:
            continue
            
        ref_vals = ref_df[col].dropna().astype(str).head(10).tolist()
        cur_vals = cur_df[col].dropna().astype(str).head(10).tolist()

        values_str = f"Reference: {ref_vals}\nCurrent: {cur_vals}"
        response = llm.with_structured_output(DriftInsight).invoke(
            PROMPT.format(values=values_str)
        )

        response = response.model_copy(update={"affected_columns": [col], "source": source_id})
        insights.append(response)

    return insights

