# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: CC-BY-4.0

# Configuration file for the Sphinx documentation builder.
# See https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import time
from os.path import (
    join,
    dirname,
    abspath,
)

sys.path.insert(0, join(dirname(dirname(dirname(abspath(__file__)))), "setupsrc"))
from pl_setup.packaging_base import (
    SourceTree,
    run_cmd,
)


def get_branch():
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=SourceTree, capture=True)
    if branch == "HEAD":
        # attempt to resolve detached head state (may happen in RTD build)
        output = run_cmd(["git", "branch"], cwd=SourceTree, capture=True)
        line = [l[2:] for l in output.split("\n") if l.startswith("* ")][0]
        branch = line.replace("(HEAD detached at origin/", "").replace(")", "").strip()
    print(branch, file=sys.stderr)
    return branch


branch_name = get_branch()

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
    "member-order": "bysource",
}
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}


def setup(app):
    app.add_config_value("branch_name", "", "env")
