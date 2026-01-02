"""Schema profiling for drift detection using LLM."""

from langchain_core.prompts import ChatPromptTemplate
from core.llm_client import get_llm
from core.models import ColumnProfile
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

