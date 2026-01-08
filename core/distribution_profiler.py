"""Distribution profiling for drift detection using LLM."""

import numpy as np
from langchain_core.prompts import ChatPromptTemplate
from core.llm_client import get_llm
from core.models import DriftInsight
from core.system_prompt import SYSTEM_PROMPT
import pandas as pd

llm = get_llm()

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Reference statistics:
{ref_stats}

Current statistics:
{cur_stats}

Determine if meaningful drift exists.
Give me values for mean standard deviation for the columns with drift.
Explain why.
""")
])


def profile_distribution(ref_df: pd.DataFrame, cur_df: pd.DataFrame, source_id: str) -> list[DriftInsight]:
    """
    Profile distribution drift using LLM.
    
    Args:
        ref_df: Reference DataFrame
        cur_df: Current DataFrame
        source_id: Source identifier for citation
        
    Returns:
        List of drift insights
    """
    insights = []

    for col in ref_df.select_dtypes(include=np.number).columns:
        if col not in cur_df.columns:
            continue
            
        ref_stats = ref_df[col].describe().to_dict()
        cur_stats = cur_df[col].describe().to_dict()

        ref_stats_str = "\n".join([f"{k}: {v}" for k, v in ref_stats.items()])
        cur_stats_str = "\n".join([f"{k}: {v}" for k, v in cur_stats.items()])

        response = llm.with_structured_output(DriftInsight).invoke(
            PROMPT.format(ref_stats=ref_stats_str, cur_stats=cur_stats_str)
        )
        # Update fields using model_copy
        response = response.model_copy(update={"affected_columns": [col], "source": source_id})
        insights.append(response)

    return insights

