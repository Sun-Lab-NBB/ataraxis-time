# Configuration file for the Sphinx documentation builder.
import importlib_metadata

# -- Project information -----------------------------------------------------
project = 'ataraxis-time'
# noinspection PyShadowingBuiltins
copyright = '2024, Ivan Kondratyev (Inkaros) & Sun Lab'
author = 'Ivan Kondratyev (Inkaros)'
release = importlib_metadata.version("ataraxis-time")  # Extracts project version from the metadata .toml file.

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',  # To build documentation from python source code docstrings.
    'sphinx.ext.napoleon',  # To read google-style docstrings (works with autodoc module).
    'breathe',  # To read doxygen-generated xml files (so that C++ documentation can be parsed by sphinx).
    'sphinx_rtd_theme',  # To format the documentation html using ReadTheDocs format.
    'sphinx_click'  # To read docstrings and command-line arguments from click-wrapped python functions.
]

# Breathe configuration
breathe_projects = {"ataraxis-time": "./doxygen/xml"}  # Specifies the source of the C++ documentation.
breathe_default_project = "ataraxis-time"  # Specifies default project name if C++ documentation is not available.

templates_path = ['_templates']
exclude_patterns = []

# Google-style docstring parsing configuration for napoleon extension
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'  # Directs sphinx to use RTD theme
