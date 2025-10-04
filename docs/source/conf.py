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

sys.path.insert(0, str(Path(__file__).parents[2]/"setupsrc"/"pypdfium2_setup"))
from base import (
    get_helpers_info,
    get_next_changelog,
)

# RTD modifies conf.py, so we have to ignore dirty state if on RTD
is_rtd = os.environ.get("READTHEDOCS", "").lower() == "true"
tag_info = get_helpers_info()
have_changes = tag_info["n_commits"] != 0 or (tag_info["dirty"] and not is_rtd) or (not tag_info["beta"] and bool(get_next_changelog()))

project = "pypdfium2"
author = "pypdfium2-team"
copyright = "%s %s" % (time.strftime("%Y"), author)

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']
html_css_files = [
    'custom.css',
]
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

myst_enable_extensions = ["colon_fence"]
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

# # https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-rst_prolog
# # .. |br| raw:: html
# #    <br/>
# assert type(have_changes) is bool
# rst_prolog = f"""
# .. |have_changes| replace:: {have_changes}
# """

# def remove_namedtuple_aliases(app, what, name, obj, skip, options):
#     if type(obj) is collections._tuplegetter:
#         return True
#     return skip


# Issue https://github.com/executablebooks/MyST-Parser/issues/845
# GitHub admonitions with Sphinx/MyST
# Workaround template adapted from (with some changes):
# https://github.com/python-project-templates/yardang/blob/f77348d45dcf0eb130af304f79c0bfb92ab90e0c/yardang/conf.py.j2#L156-L188

# https://spdx.github.io/spdx-spec/v2.3/file-tags/#h3-snippet-tags-format
# SPDX-SnippetBegin
# SPDX-License-Identifier: Apache-2.0
# SPDX-SnippetCopyrightText: Tim Paine / the yardang authors <t.paine154@gmail.com">

_GITHUB_ADMONITIONS = {
    "> [!NOTE]": "note",
    "> [!TIP]": "tip",
    "> [!IMPORTANT]": "important",
    "> [!WARNING]": "warning",
    "> [!CAUTION]": "caution",
}

def convert_gh_admonitions(app, relative_path, parent_docname, contents):
    # TODO handle nested directives -> recursion
    # loop through content lines, replace github admonitions
    for i, orig_content in enumerate(contents):
        orig_line_splits = orig_content.split("\n")
        replacing = False
        for j, line in enumerate(orig_line_splits):
            # look for admonition key
            line_roi = line.lstrip()
            for admonition_key in _GITHUB_ADMONITIONS:
                if line_roi.startswith(admonition_key):
                    line = line.replace(admonition_key, ":::{" + _GITHUB_ADMONITIONS[admonition_key] + "}")
                    # start replacing quotes in subsequent lines
                    replacing = True
                    break
            else:  # no break
                if not replacing:
                    continue
                # remove GH directive to match MyST directive
                # since we are replacing on the original line, this will preserve the right indent, if any
                if line_roi.startswith("> "):
                    line = line.replace("> ", "", 1)
                elif line_roi.rstrip() == ">":
                    line = line.replace(">", "", 1)
                else:
                    # missing "> ", so stop replacing and terminate directive
                    line = f":::\n{line}"
                    replacing = False
            # swap line back in splits
            orig_line_splits[j] = line
        # swap line back in original
        contents[i] = "\n".join(orig_line_splits)

# SPDX-SnippetEnd


def setup(app):
    app.add_css_file("custom.css")
    # app.connect('autodoc-skip-member', remove_namedtuple_aliases)
    app.connect("include-read", convert_gh_admonitions)
    app.add_config_value("have_changes", True, "env")
