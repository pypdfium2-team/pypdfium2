<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfTextPage.get_text_range()`: Correct the allocation in case of excluded/inserted chars, modify scope to prevent pdfium from reading beyond `range(index, index+count)` (which otherwise it does with leading excluded chars). Update docs to note the two different representations. Thanks to Nikita Rybak for the discovery ({issue}`261`).
- Ported setup changes from the devel branch.
  * Replaced the env vars `$PDFIUM_PLATFORM`, `$PDFIUM_VERSION` and `$PDFIUM_USE_V8` by the compound `$PDFIUM_BINARY` specifier (see the Readme for description). The setup API breakage was considered tolerable; the core library API is not affected.
  * Removed the `build` package from pyproject buildsystem requires, where it was unnecessary. Thanks to Anaconda Team.
- Switched PyPI upload to "trusted publishing" (OIDC), which is considered safer. Further, the core maintainers have set up 2FA as requested by PyPI.
