<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfPage.get_objects()`: Don't register pageobjects as children, because they don't need to be closed by the caller when part of a page. This avoids excessive caching of weakrefs that are not cleaned up with the object they refer to.
- Fixed another dotted filepath blunder in the `extract-images` CLI. (The `PdfImage.extract()` API is not affected this time.)
- Fixed installation with reference bindings (`PDFIUM_BINDINGS=reference`) by adding a missing `mkdir` call. (In older versions, this can be worked around by unpacking the sdist and creating the missing directory manually before installation.)
- Updated test expectations: due to changes in pdfium, some numbers are now slightly different.
- Fixed conda packaging: It is now required to explicitly specify `-c defaults` with `--override-channels`, presumably due to an upstream change.
- Autorelease: Swapped default condition for minor/patch update, as pypdfium2 changes are likely more API-significant than pdfium updates. Added ability for manual override.
- Bumped workflows to Python 3.12.
- Updated docs on licensing.
- *This is expected to be the last release of the v4 series.*
