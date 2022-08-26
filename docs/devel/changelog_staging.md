<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- pypdfium2 now provides PDFium with an external buffer for rendering. This has numerous advantages, most notably that callers don't need to free resources anymore. The `BitmapDataHolder` class has been removed. *`PdfPage.render_base()` was semi-public, so technically this is an API-breaking change.*
- Rewrote the project's `README.md`. Added more support model examples and an extensive guide regarding the raw PDFium/ctypes API.
- Improved support model code style while writing the raw API guide.
- When doing an automatic release, repository changes are now only pushed after successful wheel building, to avoid leaving the repository in an invalid state in case some earlier step fails.
- PDFium's commit log is now shown with GitHub releases.
- Tweaked dependency pinning.
