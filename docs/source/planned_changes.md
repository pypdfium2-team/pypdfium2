<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

<!-- Currently, no API breaking changes are planned. -->

The following API breaking changes are being considered for the next major release:
- The textpage API will change
  * The `count_chars()` alias will be removed in favour of the `n_chars` attribute.
  * The `get_text()` alias will be removed in favour of `get_text_bounded()`.
- The `PdfDocument` context manager API will be removed. It will not be possible to use documents in a `with`-block anymore.
- `PdfDocument.add_font()` might be changed to take bytes rather than a file path.
