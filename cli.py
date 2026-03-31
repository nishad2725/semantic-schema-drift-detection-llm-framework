"""Command-line interface for LLM drift detection framework.

Delegates to the LangGraph pipeline in langgraph_impl/.
"""

import sys
from langgraph_impl.cli import main

if __name__ == "__main__":
    main()

