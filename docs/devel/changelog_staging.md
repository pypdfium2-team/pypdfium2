<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Added new helpers `textpage.get_textobj()`, `PdfTextObj` and `PdfFont`.
  These helpers currently just cover font info and object-level text extraction, but may be extended in the future.
  `PdfPage.get_objects()` and the `PdfObject` constructor will now return `PdfTextObj` rather than just `PdfObject` instances.
  Thanks to Mykola Skrynnyk for the initial proposal.
  <!-- See #392, #391, #358, #325 -->
- Setup: Fixed inclusion of `BUILD_LICENSES/` sub-directories. This concerns sourcebuilds only. The wheels on PyPI are unaffected.
- Setup: Fixed Python 3.6/3.7 compatibility of `build_native.py` / fallback setup.
- GH Actions: Migrated from `macos-13` to `macos-15-intel`.
