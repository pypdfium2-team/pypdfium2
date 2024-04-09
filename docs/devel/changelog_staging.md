<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*API-breaking changes*
- Rendering / Bitmap
  * Removed `PdfDocument.render()` (see deprecation rationale in v4.25 changelog). Instead, use `PdfPage.render()` with a loop or process pool.
  * Removed `PdfBitmap.get_info()` and `PdfBitmapInfo`, which existed only on behalf of data transfer with `PdfDocument.render()`.
  * `PdfBitmap.from_pil()`: Removed `recopy` param.
  * Removed pdfium color scheme param from rendering, as it's not really useful: one can only set colors for certain object types, which are then forced on all instances of that type. This may flatten different colors into one, leading to a loss of visual information. To achieve a "dark them" for light PDFs, we suggest to instead post-process rendered images with selective lightness inversion.
- Pageobjects
  * Renamed `PdfObject.get_pos()` to `.get_bounds()`.
  * Renamed `PdfImage.get_size()` to `.get_px_size()`.
  * `PdfImage.extract()`: Removed `fb_render` param because it does not fit in this API. If the image's rendered bitmap is desired, use `.get_bitmap(render=True)` in the first place.
- `PdfDocument.get_toc()`: Replaced `PdfOutlineItem` namedtuple with method-oriented wrapper classes `PdfBookmark` and `PdfDest`, so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects. Provides signed count as-is rather than splitting in `n_kids` and `is_closed`. Also distinguishes between `dest == None` and an empty dest.
- Removed legacy version flags.

*Improvements and new features*
- Added `PdfPosConv` helper and `PdfBitmap.get_posconv(page)` for bidirectional translation between page and bitmap coordinates.
- Added `PdfObject.get_quad_points()` to get the corner points of an image or text object.
- Added `PdfPage.flatten()` (previously non-public helper), after having found out how to correctly use it. Added an assertion to make sure requirements are met, and updated docs accordingly.
- Added context manager support to `PdfDocument`, so it can be used in a `with`-statement, because opening from a file path binds a file descriptor, which should be released safely and as soon as possible, given OS limits on the number of open FDs.
- Corrected some null pointer checks: we have to use `bool(ptr)` rather than `ptr is None`.
- Simplified version impl (no API change expected).

*Project*
- Merged `tests_old/` back into `tests/`.

<!-- TODO
See https://github.com/pypdfium2-team/pypdfium2/blob/devel_old/docs/devel/changelog_staging.md
for how to proceed. Note that some things have already been backported, and some rejected.
-->
