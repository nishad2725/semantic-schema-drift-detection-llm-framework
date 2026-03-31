"""LLM client factory for the drift detection framework."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


def get_llm(model: str = "gpt-4o", temperature: float = 0.1) -> ChatOpenAI:
    """Return a configured ChatOpenAI instance.

    Args:
        model: OpenAI model identifier. Defaults to gpt-4o.
        temperature: Sampling temperature. Defaults to 0.1 for deterministic output.

    Returns:
        Configured ChatOpenAI instance.
    """
    load_dotenv()
    return ChatOpenAI(model=model, temperature=temperature)
