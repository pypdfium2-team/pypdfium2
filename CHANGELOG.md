<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

PyPDFium2 Changelog
===================

0.10.0 (unreleased)
-------------------

- Updated PDFium from `4835` to `xxxx`.
- Completely rearranged the internal structure of the support model.
  The public API should be mostly unaffected by these changes, however.
- Adapted documentation and tests to the support model changes.
- Modifications to exceptions:
    * `LoadPdfError` and `LoadPageError` were removed. The more general `PdfiumError` is now
      raised instead. This is because the exception handler may be used universally for more
      situations than just loading PDF documents or pages.
    * `PageIndexError` was replaced with `IndexError`. A custom exception seemed unnecessary
      for this case.
- New support models added:
    * Function `save_pdf()` to create a PDF file from an `FPDF_DOCUMENT` handle. This is
      demonstrated in the example [`merge_pdfs.py`](examples/merge_pdfs.py).
    * Methods `get_mediabox()` and `get_cropbox()` to retrieve PDF boxes of an `FPDF_PAGE`.
    * Made the utility functions `translate_viewmode()` and `translate_rotation()` public.
- Minor optimisations to the table of contents helper functions have been made "under the hood".
- Improved build scripts.
- Adapted the update script to upstream changes (thanks @bblanchon).
- Moved some scripts from the root directory into `utilities/` and changed the Makefile
  accordingly.
- Started backporting PyPDFium2 to older Python versions by removing all uses of f-strings,
  keywords-only enforcement, and `pathlib` across the package. The minimum required Python
  version is now 3.5. (It might be possible to further reduce the requirement by moving type
  hints from the actual code into docstrings.)

Tracking changes started with version 0.10.0, so there are no entries for older releases.
