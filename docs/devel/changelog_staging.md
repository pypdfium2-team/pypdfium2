<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- pypdfium2 was changed to provide PDFium with an external buffer for rendering. This has numerous advantages, most notably that callers don't need to free resources anymore. `PdfPage.render_base()` now directly returns a ctypes ubyte array; `BitmapDataHolder` has been removed.
- When doing an automatic release, repository changes are now only pushed after successful wheel building, to avoid leaving the repository in an invalid state in case some earlier step fails.
- Rewrote the project's `README.md`. Added more support model examples and an extensive guide regarding the raw PDFium/ctypes API.
- Improved support model code style while writing the raw API guide.
- Polished `setup.py` code to be much cleaner and easier to understand.
- Restructured some setup-related sources.
- Tweaked dependency pinning.
- PDFium's commit log is now shown with GitHub releases.
