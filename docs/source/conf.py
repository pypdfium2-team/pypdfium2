# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html
# and https://docs.readthedocs.io/en/stable/environment-variables.html

import os
import sys
import time
from os.path import (
    join,
    dirname,
    abspath,
)

sys.path.insert(0, join(dirname(dirname(dirname(abspath(__file__)))), "setupsrc"))
from pl_setup.packaging_base import (
    run_cmd,
    SourceTree,
)


def _get_build_type():
    
    # RTD uses git checkout --force origin/... which results in a detached HEAD state, so we cannot easily get the branch name
    # Thus query for an RTD-specific environment variable instead
    rtd_version_name = os.environ.get("READTHEDOCS_VERSION_NAME", None)
    if rtd_version_name:
        return rtd_version_name
    
    branch = run_cmd(["git", "branch", "--show-current"], cwd=SourceTree, capture=True)
    if branch == "stable":
        return "stable"
    else:
        return "latest"


build_type = _get_build_type()

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
    "sphinxcontrib.programoutput",
    "myst_parser",
]

suppress_warnings = [
    "ref.myst",
    "myst.header",
]

add_module_names = False
autodoc_preserve_defaults = True
autodoc_inherit_docstrings = False
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


def setup(app):
    app.add_config_value("build_type", "latest", "env")
