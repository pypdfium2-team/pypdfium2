<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Added new helpers `textpage.get_textobj()`, `PdfTextObj` and `PdfFont`.
  These helpers currently just cover font info and object-level text extraction, but may be extended in the future.
  For objects of type `FPDF_PAGEOBJ_TEXT`, `PdfPage.get_objects()` and the `PdfObject` constructor will now return `PdfTextObj` rather than just `PdfObject` instances.
  Thanks to Mykola Skrynnyk for the initial proposal.
  <!-- See #392, #391, #358, #325 -->
- Setup: Fixed inclusion of `BUILD_LICENSES/` sub-directories. This concerns sourcebuilds only. The wheels on PyPI are unaffected.
- Setup: Fixed Python 3.6/3.7 compatibility of `build_native.py` / fallback setup.
- CI: Migrated from `macos-13` to `macos-15-intel`.
- CI: Added i686 (manylinux and musllinux) to cibuildwheel workflow.
  Use an arm64 host (GHA `ubuntu-24.04-arm`) for armv7l builds, which is much faster than with an `x86_64` host. Added armv7l manylinux target (previously just musllinux).
  This does not impact releases yet, but it may in the future.
