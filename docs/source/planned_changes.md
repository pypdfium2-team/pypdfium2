<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Planned Changes

<!-- Currently, no API breaking changes are planned. -->

The following API breaking changes are being considered for the next major release:
- The textpage API will change
  * The `count_chars()` alias will be removed in favour of the `n_chars` attribute.
  * The `get_text()` alias will be removed in favour of `get_text_bounded()`.
- The `PdfDocument` class will be cleaned up:
  * The context manager API will be removed. It will not be possible to use documents in a `with`-block anymore.
  * The `update_rendering_input()` method will be removed.
    Callers are expected to save and re-open the document on their if they wish that changes take effect with the multi-page renderer.
  * The multipage renderer will not implicitly read byte buffers into memory anymore.
    Callers are expected to take an explicit decision by providing a different input in the first place.
