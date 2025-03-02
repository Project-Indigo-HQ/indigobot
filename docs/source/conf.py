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

project = "IndigoBot"
copyright = "2025, IndigoBot Team"
author = "IndigoBot Team"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
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

# Mock modules that might not be available during documentation build
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return MagicMock()


# Create more comprehensive mocking
MOCK_MODULES = [
    # Base langchain modules
    "langchain", "langchain.tools", "langchain.tools.retriever", "langchain.schema",
    "langchain.text_splitter", "langchain.chains", "langchain.chains.combine_documents",
    
    # Langchain core modules
    "langchain_core", "langchain_core.document_loaders", "langchain_core.documents",
    "langchain_core.embeddings", "langchain_core.vectorstores", "langchain_core.callbacks",
    "langchain_core.prompts", "langchain_core.runnables", "langchain_core.language_models",
    "langchain_core.messages", "langchain_core.output_parsers",
    
    # Langchain community modules
    "langchain_community", "langchain_community.document_loaders",
    "langchain_community.document_loaders.recursive_url_loader",
    
    # Other langchain packages
    "langchain_openai", "langchain_chroma", "langchain_text_splitters",
    "langchain_google_community", "langchain_google_community.bigquery",
    
    # External dependencies
    "langgraph", "langgraph.graph", "langgraph.checkpoint",
    "fastapi", "fastapi.responses", "uvicorn", 
    "pydantic", "pydantic.main", "pydantic.BaseModel",
    "bs4", "googlemaps", "unidecode",
    
    # Project modules
    "indigobot.config", "indigobot.context", "indigobot.places_tool", "indigobot.quick_api",
    "indigobot.utils", "indigobot.utils.custom_loader", "indigobot.utils.jf_crawler",
    "indigobot.utils.redundancy_check", "indigobot.utils.refine_html", "indigobot.utils.test_data_check"
]

# Update all mock modules
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

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
