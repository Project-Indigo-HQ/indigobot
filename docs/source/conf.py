# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from unittest.mock import MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Indigobot"
copyright = "2025, Team Indigo"
author = "Team Indigo"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.ifconfig",
    "sphinx.ext.githubpages",
    "sphinx.ext.autosummary",
]

templates_path = ["_templates"]
autosummary_generate = True
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_favicon = "_static/favicon.png"
html_logo = "_static/logo.png"
html_theme_options = {
    "logo_only": False,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "style_nav_header_background": "#2980B9",
}

# Set environment variable to indicate documentation build
os.environ["SPHINX_BUILD"] = "1"

# Add the mock modules directory to the path
sys.path.insert(0, os.path.abspath("_mock_modules"))

# This is critical - we need to make sure the actual module is imported
# before any mocking happens, so the real docstrings are used
import indigobot


# Mock modules that might not be available during documentation build
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return MagicMock()
        
    def __bool__(self):
        return False
        
    def __iter__(self):
        return iter([])
        
    def __getitem__(self, key):
        return MagicMock()
        
    def __str__(self):
        return ""


# Create more comprehensive mocking
MOCK_MODULES = [
    # Base langchain modules
    "langchain",
    "langchain.tools",
    "langchain.tools.retriever",
    "langchain.schema",
    "langchain.text_splitter",
    "langchain.chains",
    "langchain.chains.combine_documents",
    # Langchain core modules
    "langchain_core",
    "langchain_core.document_loaders",
    "langchain_core.documents",
    "langchain_core.embeddings",
    "langchain_core.vectorstores",
    "langchain_core.callbacks",
    "langchain_core.prompts",
    "langchain_core.runnables",
    "langchain_core.language_models",
    "langchain_core.messages",
    "langchain_core.output_parsers",
    # Langchain community modules
    "langchain_community",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.recursive_url_loader",
    # Other langchain packages
    "langchain_openai",
    "langchain_chroma",
    "langchain_text_splitters",
    "langchain_google_community",
    "langchain_google_community.bigquery",
    # External dependencies
    "langgraph",
    "langgraph.graph",
    "langgraph.checkpoint",
    "fastapi",
    "fastapi.responses",
    "uvicorn",
    "pydantic",
    "pydantic.main",
    "pydantic.BaseModel",
    "pydantic.fields",
    "pydantic.config",
    "slowapi",
    "slowapi.errors",
    "slowapi.middleware",
    "slowapi.util",
    "requests",
    "requests.exceptions",
    "bs4",
    "googlemaps",
    "unidecode",
]

# Only mock modules that don't exist
for mod_name in MOCK_MODULES:
    if mod_name not in sys.modules:
        sys.modules[mod_name] = Mock()

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "show-inheritance": True,
}

# Don't fail on missing modules
autodoc_mock_imports = MOCK_MODULES

# Intersphinx settings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}
