<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

<!-- Currently, no API breaking changes are planned. -->

The following API breaking changes are being considered for the next major release:
- The content manager API of `PdfDocument` will be removed. It will not be possible to use documents in a `with`-block anymore.
- The textpage API will change
  * `count_chars()` will be removed in favour of the `n_chars` attribute.
  * `get_text()` will be renamed to `get_text_bounded()`.
