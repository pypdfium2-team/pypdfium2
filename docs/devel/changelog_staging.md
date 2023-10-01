<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfTextPage.get_text_range()`: Correct the allocation in case of excluded/inserted chars, modify scope to prevent pdfium from reading beyond `range(index, index+count)` (which otherwise it does with leading excluded chars). Update docs to note the two different representations. Thanks to Nikita Rybak for the discovery ({issue}`261`).
- ctypesgen fork: replaced the old library loader with a new, lean version
- Setup changes (partly ported from the devel branch)
   Merged `$PDFIUM_VERSION` and `$PDFIUM_USE_V8` into the existing `$PDFIUM_PLATFORM` specifier (see Readme for updated description). The setup API breakage was considered tolerable; the core library API is not affected.
  * Removed the `build` package from pyproject buildsystem requires, where it was unnecessary. Thanks to Anaconda Team.
  * Split in two separate modules: pypdfium2 for helpers (pure-python), pypdfium2_raw for the core bindings (data files).
- Switched PyPI upload to "trusted publishing" (OIDC), which is considered safer. Further, the core maintainers have set up 2FA as requested by PyPI.
