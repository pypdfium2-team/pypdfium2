<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order.
Also see the issues panel and inline `TODO`/`FIXME` marks in source code.

### Main Code
* Add a matrix-based rendering method, and perhaps a support method around it for common transformations (crop, margins, rotate, mirror, ...).
* Add helpers for interruptible rendering.
* Check if we should use `FPDFPage_HasTransparency()` on rendering.

### Setup Infrastructure
* update_pdfium: build bindings on native OS hosts so we can use OS preprocessor defines, to expose OS-specific members
* Add means to plug in PDFium headers/binaries from an arbitrary location.
* craft_packages: add means to skip platforms for which artefacts are missing.
* update_pdfium/setup: re-think `data/` cache. Consider including version and V8 status in data dirname? Consider caching multiple versions?
* Use the logging module rather than `print()`.

### Tests
* Rewrite tests completely
* Test auto-casting
* Add an improved image test file that should ideally contain all kinds of PDF images

### Documentation
* Add/rewrite remaining Readme sections.

### GitHub Workflows
* build_packages: Try to avoid setting a temporary tag during the build stage, to prevent confusion
* Add a testing workflow to be run on PRs (Test suite, code coverage, ...)
* Consider testing PyPy interpreter as well

### Miscellaneous
