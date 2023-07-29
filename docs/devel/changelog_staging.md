<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*API breaking changes*
- (Planned) Rendering: The parallel, document-level method `PdfDocument.render()` has been removed from the public API.
  Please use `PdfPage.render()` instead, and consider caller-side, process based parallelization.
  Parallel rendering to files is still available through the CLI (an API entrypoint is provided, see below).
- `PdfDocument.get_toc()`: Replaced bookmark namedtuples with method-oriented wrapper classes `PdfBookmark` and `PdfDest`.
- Setup: renamed `$PDFIUM_PLATFORM` to `$PDFIUM_BINARY`.

*Improvements and new features*
- PDFium functions are now protected by a mutex to make them safe for use in a threaded context.
  `pypdfium2.raw` is now a wrapper around the actual bindings file `_raw_unsafe.py`.
  In this course, filtering has been installed to free the namespace of unwanted members.
- `PdfDocument`: Added support for new input types `mmap`, `bytearray`, `memoryview` and `SharedMemory`. See the docs for more info.
- Embedders may now call into the command-line API using the entrypoint function `pypdfium2.main()`.
- CLI: Implemented configurable input type for testing.
- CLI/renderer:
  * Added options to configure parallelization and output prefix.
  * Fixed parallel rendering with byte buffers on Linux by avoiding the process start method `fork`.
- sourcebuild: fixed build with system libraries.
- Improved setup code.

*Rationales*
- `PdfDocument.render()` got removed because ... TODO
- The TOC/Bookmark API was changed because ... TODO
