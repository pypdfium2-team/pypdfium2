<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

*API-breaking changes*
- `PdfDocument.get_toc()`: Replaced `PdfOutlineItem` namedtuple with method-oriented wrapper classes `PdfBookmark` and `PdfDest`, so callers may retrieve only the properties they actually need. This is closer to pdfium's original API and exposes the underlying raw objects. Provides signed count as-is rather than splitting in `n_kids` and `is_closed`. Also, distinguish between `dest == None` and an empty dest.
- Removed `PdfDocument.render()` (see deprecation rationale in v4.25 changelog).
- Removed `PdfBitmap.get_info()` and `PdfBitmapInfo`, which existed only on behalf of data transfer with `PdfDocument.render()`.

*Improvements and new features*
- Added context manager support to `PdfDocument`, so it can be used in a `with`-statement, because opening from a file path binds a file descriptor, which should be released safely and as soon as possible, given OS limits on the number of open FDs.

<!-- TODO
See https://github.com/pypdfium2-team/pypdfium2/blob/devel_old/docs/devel/changelog_staging.md
for how to proceed. Note that some things have already been backported, and some rejected.
-->
