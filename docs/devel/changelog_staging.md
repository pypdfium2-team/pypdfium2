<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- Main list character: dash (-) -->

# Changelog for next release

*API breaking changes*
- Rendering:
  * `PdfDocument.render()`, the parallel multi-page renderer, has been removed from the public API.
    Please use `PdfPage.render()` instead, and consider caller-side, process based parallelization.
    Parallel rendering to files is still available through the CLI (an API entrypoint is provided).
    See below for more info.
  * `PdfBitmap.get_info()` and `PdfBitmapInfo` have been removed since they only existed on behalf of data transfer in `PdfDocument.render()`.
- `PdfDocument.get_toc()`: Replaced bookmark namedtuples with method-oriented wrapper classes `PdfBookmark` and `PdfDest`,
  so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects.
  Also provide signed count as-is rather than needlessly splitting it in two variables (unsigned int `n_kids` and bool `is_closed`).
- Setup: renamed `$PDFIUM_PLATFORM` to `$PDFIUM_BINARY`.

*Improvements and new features*
- (Planned) PDFium functions are now protected by a mutex to make them safe for use in a threaded context.
  `pypdfium2.raw` is now a wrapper around the actual bindings file `_raw_unsafe.py`.
  In this course, filtering has been installed to free the namespace of unwanted members.
- `PdfDocument`: Added support for new input types `mmap`, `bytearray`, `memoryview` and `SharedMemory`. See the docs for more info.
- Embedders may now call into the command-line API using the entrypoint function `pypdfium2.main()`.
- CLI: Implemented configurable input type for testing.
- Major CLI renderer improvements:
  * Moved saving from main process into jobs. This avoids unnecessary data transfer and prevents images from queuing up in memory.
  * Avoid full state data transfer and object re-initialization for each job. Instead, use a pool initializer and exploit global variables.
  * Added options to configure parallelization and output prefix.
  * Fixed parallel rendering with byte buffers on Linux by avoiding the process start method `fork`.
- sourcebuild: fixed build with system libraries.
- Improved setup code.

*Rationale for the removal of PdfDocument.render()*
TODO
