<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `build_native.py`: Restore compatibility with git versions prior to `2.49`.
- Handle new pdfium-binaries for `musllinux_armv7l` in setup. (However, we still prefer CIBW for musllinux release builds.)
- Include tests in sdist, and capture release ctypesgen version in `autorelease/record.json`, to provide a better basis for packaging. Thanks to Ihar Hrachyshka for bringing this up.
- Updated `BUILD_LICENSES` to include newer third-party dependencies of PDFium.
- Aggregate release info (`matrix.txt`, `strategy.json`) in a zip file.
