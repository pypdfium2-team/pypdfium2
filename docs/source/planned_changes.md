<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

The following API breaking changes are being considered for the next major release:
* If the target page of a bookmark cannot be identified, `PdfDocument.get_toc()` will assign `None` rather than `-1` in the future, to avoid accidental reverse list indexing and to enforce that callers properly handle this case.
* Removal of the public function `raise_error()`, given that it is only usable for document loading APIs which are sufficiently managed by support models anyway.
* Rendering parameters might change, especially the anti-aliasing options.
