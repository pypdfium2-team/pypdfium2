# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html
# and https://docs.readthedocs.io/en/stable/environment-variables.html

import os
import sys
import time
# import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "setupsrc"))
from pypdfium2_setup.base import (
    get_helpers_info,
    get_next_changelog,
)

# RTD modifies conf.py, so we have to ignore dirty state if on RTD
is_rtd = os.environ.get("READTHEDOCS", "").lower() == "true"
tag_info = get_helpers_info()
next_changelog = get_next_changelog()
have_changes = tag_info["n_commits"] != 0 or (tag_info["dirty"] and not is_rtd) or next_changelog

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
    "sphinx.ext.ifconfig",
    "myst_parser",
    "sphinxcontrib.programoutput",
    "sphinx_issues",
]

issues_github_path = "pypdfium2-team/pypdfium2"

suppress_warnings = [
    "myst.header",
    "myst.xref_missing",
]

add_module_names = False
autodoc_preserve_defaults = True
autodoc_inherit_docstrings = True
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-rst_prolog
# .. |br| raw:: html
#    <br/>
rst_prolog = f"""
.. |have_changes| replace:: {have_changes}
"""

# def remove_namedtuple_aliases(app, what, name, obj, skip, options):
#     if type(obj) is collections._tuplegetter:
#         return True
#     return skip

def setup(app):
    # app.connect('autodoc-skip-member', remove_namedtuple_aliases)
    app.add_config_value("have_changes", True, "env")
