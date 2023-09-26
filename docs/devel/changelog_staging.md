<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfTextPage.get_text_range()`: Correct the allocation in case of excluded/inserted chars, modify scope to prevent pdfium from reading beyond `range(index, index+count)` (which otherwise it does with leading excluded chars). Update docs to note the two different representations. Thanks to Nikita Rybak for the discovery.
- Picked setup changes from the devel branch. This replaces the env vars `$PDFIUM_PLATFORM`, `$PDFIUM_VERSION` and `$PDFIUM_USE_V8` with the compound `$PDFIUM_BINARY` specifier (see the Readme for description). The setup API breakage was considered tolerable; the core library's API is not affected.
- Switched PyPI upload to "trusted publishing", which is considered safer.
