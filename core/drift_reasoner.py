"""Drift reasoning using LLM to explain detected drift."""

from langchain_core.prompts import ChatPromptTemplate
from core.llm_client import get_llm
from core.models import DriftInsight
from core.system_prompt import SYSTEM_PROMPT

llm = get_llm()

PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", """
Given the following drift signals:
{signals}

Summarize:
- overall severity
- root causes
- recommended actions
""")
])


def reason_overall_drift(signals: list, source_id: str) -> DriftInsight:
    """
    Generate overall drift reasoning using LLM.
    
    Args:
        signals: List of drift signals (dicts or DriftInsight objects)
        source_id: Source identifier for citation
        
    Returns:
        Overall drift insight
    """
    # Convert signals to dicts if they're Pydantic models
    signal_dicts = [s.model_dump() if hasattr(s, 'model_dump') else (s.dict() if hasattr(s, 'dict') else s) for s in signals]
    
    import json
    signals_str = json.dumps(signal_dicts, indent=2)
    
    response = llm.with_structured_output(DriftInsight).invoke(
        PROMPT.format(signals=signals_str)
    )
    # Update source field using model_copy
    response = response.model_copy(update={"source": source_id})
    return response

