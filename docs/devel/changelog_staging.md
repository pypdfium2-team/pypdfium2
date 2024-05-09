<!-- SPDX-FileCopyrightText: 2024 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
*Backported bug fixes / corrections from current development branch to preferably leave v4 in a clean state.*
- Fixed blunder in `PdfImage.extract()` producing an incorrect output path for prefixes containing a dot. In the `extract-images` CLI, this caused all output images of a type to be written to the same path for a document containing a non-extension dot in the filename.
- XFA / rendering CLI: Fixed incorrect recognition of document length. `pdf.init_forms()` must be called before `len(pdf)`.
- Made `get_text_range()` allocation adapt to pdfium version, as `FPDFText_GetText()` has been reverted to UCS-2. (See v4.28 changelog for background.)
- Updated workflows to include both `macos-13` and `macos-14` in test matrices because v13 is Intel and v14 ARM64 on GH actions. Removed python 3.7 testing because not supported anymore on `macos-14` runners.
