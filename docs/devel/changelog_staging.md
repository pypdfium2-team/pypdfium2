<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- Main list character: dash (-) -->

# Changelog for next release

*API breaking changes*
- Rendering:
  * `PdfDocument.render()`, the parallel multi-page rendering API, has been removed.
    Please use `PdfPage.render()` instead, and consider caller-side multiprocessing. See below for more info.
  * `PdfBitmap.get_info()` and `PdfBitmapInfo` have been removed since they only existed on behalf of data transfer in `PdfDocument.render()`.
- Pageobjects:
  * Renamed `PdfObject.get_pos()` to `.get_bounds()`.
  * Renamed `PdfImage.get_size()` to `.get_px_size()`.
- `PdfDocument.get_toc()`: Replaced bookmark namedtuples with method-oriented wrapper classes `PdfBookmark` and `PdfDest`,
  so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects.
  Also provide signed count as-is rather than needlessly splitting it in two variables (unsigned int `n_kids` and bool `is_closed`).
- Setup: renamed `$PDFIUM_PLATFORM` to `$PDFIUM_BINARY`.

*Bug fixes*
- Fixed XFA init (relevant for V8/XFA enabled builds only). This issue was caused by a typo in a struct field. Thanks to Benoît Blanchon.
- Fixed sourcebuild with system libraries.

*Improvements and new features*
- PDFium functions are now protected by a mutex to make them safe for use in a threaded context.
  `pypdfium2.raw` is now a wrapper around the actual bindings file `raw_unsafe.py`.
  In this course, filtering has been installed to free the namespace of unwanted members.
- For V8/XFA enabled builds, expose V8/XFA exclusive members in the bindings file by passing ctypesgen the pre-processor defines in question.
- Added `PdfPosConv` helper for bidirectional translation between bitmap and page coordinates.
  This wraps pdfium's `FPDF_DeviceToPage()` / `FPDF_PageToDevice()` APIs, which are limited to integer device coordinates.
  Generic float based coordinate normalization is not supported yet.
- `PdfObject`: Added `.get_quad_points()`.
- `PdfDocument`: Added support for new input types `mmap`, `bytearray`, `memoryview` and `SharedMemory`. See the docs for more info.
- CLI: Implemented configurable input type for testing.
- Major CLI renderer improvements:
  * Moved saving from main process into jobs. This avoids unnecessary data transfer and prevents images from queuing up in memory.
  * Avoid full state data transfer and object re-initialization for each job. Instead, use a pool initializer and exploit global variables.
    This important improvement also makes bytes input tolerable for parallel rendering.
  * Fixed parallel rendering with byte buffers on Linux by avoiding the process start method `fork`.
    (Upstream is aware of problems with `fork`. `spawn` will become the default everywhere with Python 3.14)
  * Implemented miscellaneous new options.
  * Added selective lightness inversion as post-processing feature.
- Improved setup code.

*Rationales*
- Removal of `PdfDocument.render()`:
  The parallel rendering API unfortunately was an inherent design mistake:
  Multiprocessing is not meant to transfer large amounts of pixel data from workers to the main process.
  Instead, each bitmap should be processed (e.g. saved) in the job which created it.
  Only a minimal, final result should be sent back to the main process (e.g. a file path).
  This means we cannot reasonably provide a generic parallel renderer, instead it should be implemented by callers.
  Apart from that, object re-construction is also better left in the control of callers.
  pypdfium2's rendering CLI cleanly re-implements parallel rendering to files (fixing further mistakes, see above).
  We are considering if this use case could eventually be turned into an API.
