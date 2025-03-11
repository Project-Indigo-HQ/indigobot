"""
RAG-based LLM application - Chatbot for Social Services (CfSS)

This package provides a RAG-based chatbot that helps users find and access social
services information in the Portland, OR area. It includes web scraping, document
processing, and a conversational interface powered by an LLM.

Author: Team Indigo,
License: GPL3
"""

from typing import List

__author__ = "Team Indigo"
__license__ = "GPL3"

try:
    from ._version import version as __version__  # type: ignore
except ImportError:
    __version__ = "0.0.0"  # package is not installed

# Explicitly declare public exports
__all__: List[str] = [
    "__version__",
    "__author__",
    "__license__",
]
