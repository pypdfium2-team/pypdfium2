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
    - If a negative index is passed to `PdfDocument.new_page()`, it is now interpreted in reversed direction, rather than inserting at the beginning.
    - `PdfPage.count_objects()` was removed. Use `PdfPage.get_objects()` or the raw PDFium API instead.
    - The `get_type()` method of `PdfPageObject` was replaced with a `type` attribute.
    
    *Other changes*
    - New rendering parameters added: `color_scheme`, `fill_to_stroke`, `force_halftone`, `draw_forms`, `rev_byteorder`, `extra_flags`, `allocator`, and `memory_limit`.
    - Added new `render_to()` functions to `PdfPage` and `PdfDocument` that take a custom bitmap converter, to transform the ctypes array to a different object. A set of built-in converters is provided with the `BitmapConv` class. Confer the updated API documentation for details. The previous rendering functions (`render_topil()` `render_tobytes()`, ...) are still around as deprecated aliases but may be removed eventually.
    - New rendering target `numpy.ndarray` added.
    - The `PIL.Image.Image` target now accepts a `prefer_la` parameter to request automatic conversion of `BGRA`/`RGBA` to `LA` if rendering in greyscale with alpha channel (PDFium does not support `LA` natively).
    - New method `PdfDocument.get_page_size()` to retrieve page size by index without needing to load a `PdfPage` (uses `FPDF_GetPageSizeByIndexF()` under the hood).
    - All document-level methods that take a page index now accept negative values for reverse indexing (except the rendering methods).
    - `PdfPage.get_objects()` can now recursively descend into Form XObjects.
    - Form environments are now initialised/exited on document level rather than on page rendering. *In the course of this work, a segmentation fault source was eliminated, related to a formerly undocumented requirement of PDFium regarding object lifetime. Whether the segmentation fault would actually take place was dependent on Python garbage collection behaviour. This did not appear to happen under normal circumstances, so the issue remained unnoticed for a long time.*
    - Improved code style and consistency regarding interaction with PDFium/ctypes.

- Setup code
    - `$PYP_TARGET_PLATFORM` was renamed to `$PDFIUM_BINARY`, the value `sdist` was renamed to `none`.
    - When doing an automatic release, repository changes are now only pushed after successful wheel building, to avoid leaving the repository in an invalid state in case some earlier step fails.
    - pypdfium2 now declares a no-op setuptools extension to prevent wheel content from landing in a `purelib` folder. Some systems use this information to separate platform-dependent packages from pure-python packages (i. e. `/usr/lib64` instead of `/usr/lib`). Confer PEP 427.
    - Autorelease now properly takes existing beta tags into account for its version changes.
    - PDFium's commit log is now shown with GitHub releases.
    - The wheel packaging script now restores in-tree artefacts from a possible editable install.
    - Platform files are now detected in a more robust way. If missing, a proper exception will be raised.
    - Platform data directories are now annotated with a text file storing the pdfium version, to prevemt a possible mismatch between the state of `version.py` and the actual version of the used binary. The update and build scripts do not directly change the main version file anymore, but defer the changes to `setup.py`.
    - Missing platform files are now always procured implicitly on installation. If platform files exist already but are outdated, they will be updated by default. You may opt out by creating an empty file called `.lock_autoupdate.txt` in `data/`.
    - A `MANIFEST.in` file was added to avoid being dependent on `setuptools_scm`.
    - On setup, dependency checks are now only done for system commands. The wonky implicit installation of missing Python packages was removed. If opting out of build isolation, callers should properly install setup dependencies beforehand.
    - Significant code quality improvements.

- Documentation
    - Rewrote the project's `README.md`. Added more support model examples and an extensive guide regarding the raw PDFium/ctypes API.
    - Improved docstrings and included type hints.
