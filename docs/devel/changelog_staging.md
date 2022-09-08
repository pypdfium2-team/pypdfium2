<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Support model
    
    *API-breaking changes*
    - PDFium is now provided with an external, python-allocated buffer for rendering. This has numerous advantages, most notably that callers don't need to free resources anymore. `PdfPage.render_base()` now directly returns a ctypes ubyte array; `BitmapDataHolder` has been removed.
    - Changed rendering parameters
        - `annotations` was renamed to `draw_annots`
        - `colour` was renamed to `color` and now only takes a list of 4 values for simplicity - it may not be 3 values or `None` anymore
        - `no_antialias` has been replaced with separate boolean options `no_smoothtext`, `no_smoothimage`, and `no_smoothpath`
    - If the target page of a bookmark cannot be identified, `PdfDocument.get_toc()` now assigns `None` rather than `-1`, to avoid accidental reverse list indexing and to enforce that callers properly handle this case.
    
    *Other changes*
    - Improved code style and consistency regarding interaction with PDFium/ctypes.
    - New rendering parameters added: `color_scheme`, `fill_to_stroke`, `force_halftone`, `draw_forms`, `rev_byteorder`, `extra_flags`, and `memory_limit`.
    - New rendering functions `render_tonumpy()` added, returning a shaped NumPy array.
    - Form environments are now initialised/exited on document level rather than on page rendering. *In the course of this work, a segmentation fault source was eliminated, related to a formerly undocumented requirement of PDFium regarding object lifetime. Whether the segmentation fault would actually take place was dependant on Python garbage collection behaviour. This did not appear to happen under normal circumstances, so the issue remained unnoticed for a long time.*

- Setup code
    - When doing an automatic release, repository changes are now only pushed after successful wheel building, to avoid leaving the repository in an invalid state in case some earlier step fails.
    - Autorelease now properly takes existing beta tags into account for its version changes.
    - PDFium's commit log is now shown with GitHub releases.
    - Miscellaneous setup improvements.

- Documentation
    - Rewrote the project's `README.md`. Added more support model examples and an extensive guide regarding the raw PDFium/ctypes API.
    - Improved docstrings and included type hints.
