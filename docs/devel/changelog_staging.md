<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- The pdfium update fixes a regression in `FPDFText_GetLooseCharBox()` / `PdfTextPage.get_charbox(i, loose=True)` results introduced in the previous release.
  (Since conda pdfium-binaries are updated only once a month, this release downgrades to pdfium `7713` on conda)
- Fixed an oversight in the CLI that caused `pypdfium2.__init__` to run before preparation after all. This had regressed shortly before the previous release.
 `DEBUG_AUTOCLOSE=1 pypdfium2 -h` should now show `Initialize PDFium` at first.
- Changed output string handling once more, as even slicing the buffer directly still implies a copy – so let's use `memoryview` and `codecs.decode()` instead.
  Also, we now create buffers of the expected type directly to avoid casts, and convert number of bytes to units via ceil division where needed.
  Updated the Readme's raw API examples accordingly.
- `PdfTextPage.get_text_bounded()` no longer unconditionally calls `page.get_bbox()` each time. Instead, call it only if needed, when at least one of the boundary values is None.
  If all bounds are given, skip the call. This eliminates extra overhead when `get_text_bounded()` is called many times on given rectangles, like from `PdfTextPage.get_rect()`. Though the API probably is not meant to be used this way.
  Consider `PdfPage.get_objects(filter=(FPDF_PAGEOBJ_TEXT,))` and `textobj.extract()` as a possible alternative.
- Added `PdfFont.is_embedded` property.
