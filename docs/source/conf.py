# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath("../.."))
from unittest.mock import MagicMock


class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return Mock()


MOCK_MODULES = [
    "langchain",
    "langchain.chains",
    "langchain.chains.combine_documents",
    "langchain.text_splitter",
    "langchain.agents",
    "langchain.schema",
    "langchain.tools",
    "langchain.tools.retriever",
    "langchain_core",
    "langchain_core.documents",
    "langchain_core.embeddings",
    "langchain_core.utils",
    "langchain_core.chat_history",
    "langchain_core.messages",
    "langchain_core.vectorstores",
    "langchain_core.callbacks",
    "langchain_core.callbacks.manager",
    "langchain_core.prompts",
    "langchain_core.runnables",
    "langchain_core.runnables.history",
    "langchain_core.language_models",
    "langchain_core.load",
    "langchain_core.load.load",
    "langchain_core.language_models.chat_models",
    "langchain_core.messages.ai",
    "langchain_core.messages.tool",
    "langchain_core.output_parsers",
    "langchain_core.load.serializable",
    "langchain_core.output_parsers.base",
    "langchain_core.runnables.config",
    "langchain_core.runnables.base",
    "langchain_core.output_parsers.openai_tools",
    "langchain_core.tools",
    "langchain_core.runnables.graph",
    "langchain_core.outputs",
    "langchain_core.utils.function_calling",
    "langchain_core.globals",
    "langchain_core.utils.json_schema",
    "langchain_core.language_models.llms",
    "langchain_core.runnables.utils",
    "langchain_community",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.recursive_url_loader",
    "langchain_community.document_transformers",
    "langchain_community.agent_toolkits",
    "langchain_community.agent_toolkits.load_tools",
    "langchain_community.agent_toolkits.sql",
    "langchain_community.agent_toolkits.sql.base",
    "langchain_community.utilities",
    "langchain_anthropic",
    "langchain_openai",
    "anthropic",
    "openai",
    "chromadb",
    "chromadb.config",
    "bs4",
    "numpy",
    "pandas",
    "sqlalchemy",
]


# Create base class for language models
class BaseLLM:
    pass


class BaseLanguageModel:
    pass


# Add the base classes to the mock system
sys.modules["langchain_core.language_models.base"] = type(
    "langchain_core.language_models.base",
    (),
    {"BaseLanguageModel": BaseLanguageModel, "BaseLLM": BaseLLM},
)

# Update all mock modules
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Project Indigo"
copyright = "2024 - Kyle Klein, Avesta Mirashrafi, Melissa Shanks, Grace Trieu, Karl Rosenberg, JunFan Lin, Sam Nelson"
author = "Kyle Klein, Avesta Mirashrafi, Melissa Stokes, Grace Trieu, Karl Rosenberg, JunFan Lin, Sam Nelson"
version = "1.0.0"
release = "1.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    # "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_copybutton",
]

# Add source file mappings
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# # Napoleon settings
# napoleon_google_docstring = True
# napoleon_numpy_docstring = True
# napoleon_include_init_with_doc = False
# napoleon_include_private_with_doc = False
# napoleon_include_special_with_doc = True
# napoleon_use_admonition_for_examples = False
# napoleon_use_admonition_for_notes = False
# napoleon_use_admonition_for_references = False
# napoleon_use_ivar = False
# napoleon_use_param = True
# napoleon_use_rtype = True
# napoleon_type_aliases = None

# Intersphinx settings
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "langchain": ("https://api.python.langchain.com/en/latest/", None),
}
templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# suppress_warnings = ["epub.unknown_project_files"]
