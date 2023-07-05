<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Some API breaking changes, without a major increment due to the comparatively low overall impact.
  - `PdfDocument.get_toc()` API changed. Bookmarks are now provided as wrapper objects with getter methods, rather than as namedtuples.
  - Removed `mk_formconfig` parameter of `PdfDocument.render()`.
- Added support for new input types `bytearray`, `memoryview`, and `mmap`. See the docs for `PdfDocument(input)`.
- CLI/renderer: added option to configure prefix of output images
