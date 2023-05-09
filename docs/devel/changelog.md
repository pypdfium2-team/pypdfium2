<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- MyST Syntax -->


# Changelog


## 4.10.0 (2023-05-09)

- Updated PDFium from `5744` to `5758`.


## 4.9.0 (2023-05-02)

- Updated PDFium from `5731` to `5744`.


## 4.8.0 (2023-04-25)

- Updated PDFium from `5715` to `5731`.
- `PdfTextPage.get_rect()`: Added missing return code check and updated docs regarding dependence on `count_rects()`.
  Fixed related test code that was broken but disabled by accident (missing asserts). Thanks to Guy Rosin for reporting {issue}`207`.
- Added `PdfImage.get_size()` wrapping the new pdfium function `FPDFImageObj_GetImagePixelSize()`, which is faster than getting image size through the metadata.
- `build_pdfium.py --use-syslibs`: Changed `sysroot="/"` (invalid) to `use_sysroot=false` (valid). This allows us to remove a botched patch.


## 4.7.0 (2023-04-18)

- Updated PDFium from `5705` to `5715`.
- Fixed `PdfPage.remove_obj()` wrongly retaining the page as parent in the finalizer hierarchy.


## 4.6.0 (2023-04-11)

- Updated PDFium from `5692` to `5705`.


## 4.5.0 (2023-04-04)

- Updated PDFium from `5677` to `5692`.
- In pdfium-binaries, forms init for V8/XFA enabled builds was fixed by correctly setting up XFA on library init
  (see [pdfium-binaries#105](https://github.com/bblanchon/pdfium-binaries/issues/105)).
  Updated pypdfium2's support model accordingly.


## 4.4.0 (2023-03-28)

- Updated PDFium from `5664` to `5677`.


## 4.3.0 (2023-03-21)

- Updated PDFium from `5648` to `5664`.
- Fixed forms rendering in the multi-page renderer by initializing a formenv in worker jobs if the triggering document has one.


## 4.2.0 (2023-03-14)

- Updated PDFium from `5633` to `5648`.
- API-breaking changes around forms code, necessary to fix conceptual issues. Closes {issue}`182`.
  * `may_init_forms` parameter replaced with `init_forms()`, so that a custom form config can be provided.
  * `formtype` attribute replaced with `get_formtype()`.
    Previously, `formtype` would only be set correctly on formenv init, which caused confusion
    for documents that have forms but no formenv was initialized.
- `PdfPage.get_*box()` functions now provide an option to disable fallbacks. Closes {issue}`187`.
- Some formerly hidden utilities are now exposed in the new namespace `pypdfium2.internal`.


## 4.1.0 (2023-03-07)

- Updated PDFium from `5619` to `5633`.
- The `PdfDocument` parameter `may_init_forms` is now False by default.


## 4.0.0 (2023-02-28)

- Updated PDFium from `5579` to `5619`.
- Full support model rewrite. Many existing features changed and new helpers added. Numerous bugs fixed on the way.
  Read the updated documentation to migrate your code.
- The raw API is now isolated in a separate namespace (`pypdfium2.raw`).
  Moreover, the raw API bindings do not implicitly encode strings anymore (pypdfium2 is now built with a patched version of ctypesgen by default).
- Helper objects now automatically resolve to the underlying raw object if used as ctypes function parameter.
- Overhauled the code base to use `pathlib` and f-strings.
- Updated wheel tags.
- Improved command-line interface, setup code, and documentation.


## 4.0.0b2 (2023-02-23)

- First successful beta release for v4.


## 4.0.0b1 (2023-02-22)

- Attempted beta release for v4. PyPI upload failed due to {issue}`177`.


## History

pypdfium2 is on PyPI since Dec 3, 2021. New versions have been released on a regular basis ever since.

There have been the following version ranges: `0.1 - 0.15`, `1.0 - 1.11`, `2.0 - 2.11`, `3.0 - 3.21.1`.

Entries for releases below version 4 have been removed from the changelog because they were too inconsistent.
