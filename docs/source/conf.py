# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import importlib.metadata
from unittest.mock import MagicMock

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath("../.."))

# Try to get the version from package metadata
try:
    version = importlib.metadata.version("indigobot")
except importlib.metadata.PackageNotFoundError:
    version = "1.0.0"  # Fallback version


class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return Mock()


# Set environment variable to indicate documentation build
os.environ["SPHINX_BUILD"] = "1"


MOCK_MODULES = [
    "langchain",
    "langchain.chains",
    "langchain.chains.combine_documents",
    "langchain_core",
    "langchain_community",
    "langchain_community.document_loaders.async_html",
    "langchain_community.document_loaders.html",
    "langchain_text_splitters",
    "langchain_anthropic",
    "unidecode",
    "bs4",
    "beautifulsoup4",
    "fastapi",
    "uvicorn",
    "langchain_core.messages",
    "langgraph.graph.message",
    "langchain_openai",
    "anthropic",
    "openai",
    "chromadb",
    "typing_extensions",
    "langgraph",
    "langgraph.checkpoint",
    "langgraph.checkpoint.memory",
    "langgraph.graph",
    "indigobot.config",
    "indigobot.__main__",
    "requests",
    "requests.exceptions",
    "bs4",
    "pydantic",
    "pydantic.main",
    "pydantic._internal",
    "pydantic._internal._config",
    "langgraph",
    "langgraph.graph",
    "langgraph.graph.graph",
    "langgraph.pregel",
    "langgraph.checkpoint",
    "langgraph.checkpoint.memory",
    "langchain_core._api",
    "langchain_core._api.deprecation",
    "langchain_chroma",
    "langchain_anthropic",
    "langchain_google_genai",
    "langchain_openai",
    "langchain.text_splitter",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.recursive_url_loader",
    "langchain_community.document_transformers",
    "langchain_core.documents",
    "langchain_core.embeddings",
    "langchain_core.vectorstores",
    "langchain_core.callbacks",
    "langchain_core.callbacks.manager",
    "langchain_core.prompts",
    "langchain_core.runnables",
    "langchain_core.runnables.history",
    "langchain_core.language_models",
    "langchain_core.messages",
    "langchain_core.messages.ai",
    "langchain_core.messages.tool",
    "langchain_core.output_parsers",
    "langchain_core.load",
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
    "langchain_core.tracers",
    "langchain.text_splitter",
    "langchain.agents",
    "langchain.schema",
    "langchain.tools",
    "langchain.tools.retriever",
    "langchain_core",
    "langchain_core.documents",
    "langchain_core.embeddings",
    "langchain_core.utils",
    "requests.packages",
    "langchain_core.chat_history",
    "langchain_core.messages",
    "langchain_core.vectorstores",
    "langchain_core.callbacks",
    "langchain_core.callbacks.manager",
    "langchain_core.prompts",
    "langchain_core.runnables",
    "requests.packages.urllib3.util",
    "requests.packages.urllib3.util.retry",
    "requests.adapters",
    "requests.packages.urllib3",
    "langchain_core.runnables.history",
    "langchain_core.language_models",
    "langchain_core.retrievers",
    "langchain_core.load",
    "langgraph.graph.message",
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
    "langchain_core.tracers",
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
    "langchain_google_genai",
    "langchain_google_genai.chat_models",
    "langchain_google_genai.llms",
    "anthropic",
    "openai",
    "chromadb",
    "chromadb.config",
    "bs4",
    "numpy",
    "pandas",
    "sqlalchemy",
    "langchain_core.tracers._streaming",
    "langchain_core.tracers.base",
    "langchain_core.tracers.schemas",
    "langchain_core.tracers.stdout",
    "langchain_core.tracers.langchain",
    "langchain_core.tracers.context",
    "langchain_text_splitters",
    "langchain_text_splitters.base",
    "langchain.chains.combine_documents",
    "langchain.chains.combine_documents.base",
    "langchain.chains.combine_documents.reduce",
]


# Create mock classes for Chroma
class MockChroma:
    def __init__(self, *args, **kwargs):
        pass


sys.modules["langchain_chroma"] = type(
    "langchain_chroma",
    (),
    {"Chroma": MockChroma},
)


# Create unified mock base for language models
class MockBase(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()


# Create base mock class for all language models and transformers
class BaseMock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

    def __call__(self, *args, **kwargs):
        return self


class StateGraph(BaseMock):
    def add_edge(self, *args, **kwargs):
        return self

    def add_node(self, *args, **kwargs):
        return self

    def compile(self, *args, **kwargs):
        return self


class MemorySaver(BaseMock):
    pass


class Config(BaseMock):
    RAG_DIR = "/mock/rag/dir"
    llms = {"gpt": BaseMock()}
    vectorstores = {"gpt": BaseMock()}
    r_url_list = []
    url_list = []


class Main(BaseMock):
    @staticmethod
    def load():
        return BaseMock()

    @staticmethod
    def api():
        return BaseMock()

    @staticmethod
    def main(skip_loader: bool = False, skip_api: bool = False) -> None:
        return None


class BeautifulSoup(BaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__()

    def find(self, *args, **kwargs):
        return self

    def get_text(self, *args, **kwargs):
        return ""


class FastAPI(BaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__()


class BaseModel(BaseMock):
    def __init__(self, *args, **kwargs):
        super().__init__()


# Create mock for Pydantic ConfigDict
class ConfigDict(BaseMock):
    pass


# Register ConfigDict mock
sys.modules["pydantic._internal._config"] = type(
    "pydantic._internal._config",
    (),
    {"ConfigDict": ConfigDict},
)


# Create specific mock classes inheriting from BaseMock
class BaseLanguageModel(BaseMock):
    pass


class BaseLLM(BaseMock):
    pass


class BaseGoogleGenerativeAI(BaseMock):
    pass


class BaseDocumentTransformer(BaseMock):
    pass


class TextSplitter(BaseMock):
    pass


class AsyncHtmlLoader(BaseMock):
    pass


class RecursiveUrlLoader(BaseMock):
    pass


# Add the mock classes to the system
sys.modules.update(
    {
        "fastapi": type(
            "fastapi",
            (),
            {
                "FastAPI": FastAPI,
                "HTTPException": Exception,
            },
        ),
        "pydantic": type(
            "pydantic",
            (),
            {
                "BaseModel": BaseModel,
            },
        ),
        "bs4": type("bs4", (), {"BeautifulSoup": BeautifulSoup}),
        "langchain_core.language_models.base": type(
            "langchain_core.language_models.base",
            (),
            {
                "BaseLanguageModel": BaseLanguageModel,
                "BaseLLM": BaseLLM,
            },
        ),
        "langchain_google_genai.llms": type(
            "langchain_google_genai.llms",
            (),
            {
                "_BaseGoogleGenerativeAI": BaseGoogleGenerativeAI,
            },
        ),
        "langchain_core.documents.transformers": type(
            "langchain_core.documents.transformers",
            (),
            {
                "BaseDocumentTransformer": BaseDocumentTransformer,
            },
        ),
        "langchain_text_splitters": type(
            "langchain_text_splitters",
            (),
            {
                "TextSplitter": TextSplitter,
                "RecursiveCharacterTextSplitter": TextSplitter,
            },
        ),
        "langchain_community.document_loaders": type(
            "langchain_community.document_loaders",
            (),
            {
                "AsyncHtmlLoader": AsyncHtmlLoader,
                "RecursiveUrlLoader": RecursiveUrlLoader,
            },
        ),
    }
)

# Update all mock modules
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Project Indigo"
copyright = "2024 - Kyle Klein, Avesta Mirashrafi, Melissa Shanks, Grace Trieu, Karl Rosenberg, JunFan Lin, Sam Nelson"
author = "Kyle Klein, Avesta Mirashrafi, Melissa Shanks, Grace Trieu, Karl Rosenberg, JunFan Lin, Sam Nelson"
release = version

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
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx.ext.inheritance_diagram",
    "sphinx.ext.autosummary",
]

# Enable todo items
todo_include_todos = True

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Add source file mappings
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

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
html_favicon = "_static/favicon.ico"
html_logo = "_static/logo.png"
html_theme_options = {
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': True,
    'style_nav_header_background': '#2980B9',
}

# Suppress warnings
suppress_warnings = ["epub.unknown_project_files"]

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}
