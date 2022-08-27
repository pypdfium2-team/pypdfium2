<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Support model
    *API-breaking changes*
    - PDFium is now provied with an external, python-allocated buffer for rendering. This has numerous advantages, most notably that callers don't need to free resources anymore. `PdfPage.render_base()` now directly returns a ctypes ubyte array; `BitmapDataHolder` has been removed.
    - If the target page of a bookmark cannot be identified, `PdfDocument.get_toc()` now assigns `None` rather than `-1`, to avoid accidental reverse list indexing and to enforce that callers properly handle this case.
    *Other changes*
    - Improved code style and consistency regarding interaction with PDFium/ctypes.
- Setup code
    - When doing an automatic release, repository changes are now only pushed after successful wheel building, to avoid leaving the repository in an invalid state in case some earlier step fails.
    - PDFium's commit log is now shown with GitHub releases.
    - Polished `setup.py` code to be much cleaner and easier to understand.
    - Restructured some setup-related sources.
    - Tweaked dependency pinning.
- Documentation
    - Rewrote the project's `README.md`. Added more support model examples and an extensive guide regarding the raw PDFium/ctypes API.
    - Improved docstrings and included type hints.
