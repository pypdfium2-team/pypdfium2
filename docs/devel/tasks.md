<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order.
Also see the issues panel and inline `TODO` marks in source code.

### Main Code
* Consider making internal helpers public as well (consts, utils, autoclose).
* Add a matrix-based rendering method, and perhaps a support method around it for common transformations (crop, margins, rotate, mirror, ...).
* Add helpers for interruptible rendering.

### Setup Infrastructure
* Migrate everything to pathlib
* craft_wheels: add means to skip platforms for which artefacts are missing.
* update_pdfium: only generate the bindings file once for all platforms.
* update_pdfium: add option to download a custom pdfium-binaries release (i. e. not the latest).
* packaging_base: consider using a class for `VerNamespace`.
* Use the logging module rather than `print()`.

### Tests
* Rewrite tests completely
* Unify rendering tests with `RenderTestCase` class and a single, parametrized function

### Documentation
* Add/rewrite remaining Readme sections.

### GitHub Workflows
* build_packages: consider splitting up autorelease in two stages to avoid a temporary branch, then transfer changes as patch.
* Add a testing workflow to be run on PRs (Test suite, code coverage, ...)
* Consider testing pypy interpreter as well

### Miscellaneous
* Add means to plug in PDFium headers/binaries from an arbitrary location.
* Check if we should use `FPDFPage_HasTransparency()` on rendering.
