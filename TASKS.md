<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

PyPDFium2 Tasks
===============

(These are various tasks for the maintainer to keep in mind, in no specific order.)

* Ask Linux distributors to package PDFium, as this could greatly simplify the installation of PyPDFium2 for many users. Since most distributions are already compiling PDFium for their Chromium package anyway, it should be feasible to build PDFium as a dynamically linked library and add a development package containing the header files. We could then add a custom setup file that will create bindings using the system-provided PDFium headers.
* Set the version appropriately when doing a source build (i. e. append current PDFium commit hash to version string).
* Add means for automatic system dependency installation on Linux. Prompt the user for the admin password using `sudo`, `pkexec` or similar.
* Move Changelog and Contributing Guidelines into the Sphinx documentation.
* Think about how to prevent further growth of the repository root directory.
* Decide what to do about the kind of failed `compcheck.py` utility.
* Look into setting up Github Actions CI.
* Create a `.readthedocs.yaml` configuration file (issue #32).
* Add capabilities to render a certain area of a page (issue #38).
* Allow for only returning bytes rather than creating an `Image.Image` object when rendering, so that callers may use the data in any way they like, without having to go through an intermediate PIL object (e. g. directly inject the data into a GUI widget buffer).
* Investigate what can be done regarding compatibility with legacy setuptools versions (issue #52).
* Think about further extending support for older Python versions (see changelog).
