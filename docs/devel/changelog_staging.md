<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfDocument.get_toc()` API changed. Bookmarks are now provided as wrapper objects with getter methods, rather than as namedtuples.
- Removed `mk_formconfig` parameter of `PdfDocument.render()`.
