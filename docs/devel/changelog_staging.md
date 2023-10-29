<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Fixed faulty version repr (avoid trailing `+` if desc is empty).
- Merged conda packaging code. The packages build, but there is no CI integration yet.
- Updated setup code, mainly to support conda.
  * Independent bindings cache. Download headers from pdfium. Extract archive members explicitly.
  * Cleaned up version integration of sourcebuild.
  * Changed `system` platform to generate files according to given version, instead of expecting given files.
  * Added `provided!` prefix to platform spec, allowing to install with given files.
  * Added `PDFIUM_BINDINGS=reference` to use pre-built bindings when installing from source.
- Updated Readme.
