<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Tasks

These are various tasks for the maintainer to keep in mind, in no specific order.
Also see the issues panel and inline `TODO`/`FIXME` marks in source code.

### Main Code
* Add a matrix-based rendering method, and perhaps a support method around it for common transformations (crop, margins, rotate, mirror, ...).
* Add helpers for interruptible rendering.

### Setup Infrastructure
* craft_packages: add means to skip platforms for which artefacts are missing.
* update_pdfium: only generate the bindings file once for all platforms.
* update_pdfium/setup: re-think the general concept (thoughts following the addition of support for custom pdfium version and V8 support). Include version and V8 status in data dirname?
* packaging_base: consider using a class for `VerNamespace`.
* Use the logging module rather than `print()`.

### Tests
* Rewrite tests completely
* Test auto-casting
* Add an improved image test file that should ideally contain all kinds of PDF images

### Documentation
* Add/rewrite remaining Readme sections.

### GitHub Workflows
* build_packages: Re-think the problem outlined in https://github.com/orgs/community/discussions/38443. Maybe we should avoid setting a temporary tag during the build stage, to avoid confusion?
* Add a testing workflow to be run on PRs (Test suite, code coverage, ...)
* Consider testing pypy interpreter as well

### Miscellaneous
* Add means to plug in PDFium headers/binaries from an arbitrary location.
* Check if we should use `FPDFPage_HasTransparency()` on rendering.
