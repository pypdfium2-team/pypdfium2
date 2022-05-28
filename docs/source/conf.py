# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import time

project = "pypdfium2"
author = "pypdfium2-team"
copyright = "%s %s" % (time.strftime("%Y"), author)

html_theme = "sphinx_rtd_theme"
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinxcontrib.programoutput",
    "myst_parser",
]

autodoc_preserve_defaults = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "member-order": "bysource",
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
}
