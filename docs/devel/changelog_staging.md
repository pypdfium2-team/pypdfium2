<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Disruption: `PdfPage.insert_text()` does not generate page content automatically anymore. The new `PdfPage.generate_content()` method now needs to be called to apply changes, to avoid generating content repeatedly.
- Disruption: In `PdfTextPage.get_text()`, the boundary values are now only set to defaults if they're `None`, not 0. This change was necessary because the underlying PDFium function requires PDF box values rather than normalised values.
- pypdfium2 finally implements automatic object finalisation. Calling the `close()` methods is not mandatory anymore. The context manager API of `PdfDocument` is retained for backwards compatibility, but exiting the context manager does not close the document anymore, since this would increase the risk of closing objects in wrong order.
- A new text extraction method `get_text_range()` was added. `get_text()` was renamed to `get_text_bounded()` but is still available as deprecated alias.
- Text pages now have an `n_chars` attribute. `count_chars()` is still available as deprecated alias.
- Added a helper class for transform matrices.
- Added support models to capture pages as XObjects, to get page objects for XObjects, to transform them with matrices, and to insert page objects into a page. This may be used to implement a custom N-up compositor, for instance.
- The document level renderer now uses a shortcut if processing just a single page.
- When rendering, pypdfium2 now checks if the document has forms before initialising/exiting a form environment.
- The Sphinx documentation now includes the Readme file.
