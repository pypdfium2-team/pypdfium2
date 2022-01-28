<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# PyPDFium2 Changelog

## 0.11.0 (unreleased)

- Overhauled the command-line interface to group different tasks in subcommands.
  It should be a lot cleaner now; easier to use and extend. These modifications make the
  command-line API incompatible with previous releases, though.
  In the course of this restructuring, the following functional changes were applied:
  * Made rendering output formats customisable by providing control over the file extension to use,
    from which the `Pillow` library will be able to automatically determine the corresponding encoder.
  * Changed the rendering parser to accept multiple files at once.
  * Positional arguments are now used for file input.
  * Added CLI commands for merging PDFs and performing page tiling (N-up).
  * Temporarily removed support for working with encrypted PDFs while we are looking for a
    suitable way to take passwords for multiple files.
- Adapted documentation to the CLI changes.

## 0.10.0 (2022-01-24)

- Updated PDFium from `4835` to `4849`.
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
- Removed the in-library logging setup as it could cause issues for downstream users who wish
  to configure the pypdfium2 logger.
- Started backporting PyPDFium2 to older Python versions by removing all uses of f-strings,
  keywords-only enforcement, and `pathlib` across the package. The minimum required Python
  version is now 3.5. (It might be possible to further reduce the requirement by moving type
  hints from the actual code into docstrings.)
- We no longer implicitly read the data of files with non-ascii paths to bytes on Windows in
  `render_pdf()`, mainly because `str.isascii()` requires at least Python 3.7. Callers may
  implement the workaround if desired.
- Minor optimisations to the table of contents helper functions have been made "under the hood".
- Improved build scripts.
- Adapted the update script to upstream changes (thanks @bblanchon).
- Moved some scripts from the root directory into `utilities/` and changed the Makefile
  accordingly.
- Added a list of future [tasks](TASKS.md) to keep in mind.

Tracking changes started with version 0.10.0, so there are no entries for older releases.
