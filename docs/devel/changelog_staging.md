<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- In `PdfDocument.render()`, fixed a bad `bitmap.close()` call that would lead to a downstream use after free when using the combination of foreign bitmap and no-copy conversion. Using foreign bitmaps was not the default and expressly not recommended.
