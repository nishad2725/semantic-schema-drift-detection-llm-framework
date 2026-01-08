"""LLM client for interacting with language models."""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from core.system_prompt import SYSTEM_PROMPT


load_dotenv()


def get_llm():
    """Get configured LLM instance."""
    api_key = os.getenv("OPENAI_API_KEY")

    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.1
    )

