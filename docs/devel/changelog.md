<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- MyST Syntax -->


# Changelog


## 4.2.0 (2023-03-14)

- Updated PDFium from `5633` to `5648` (autorelease).
- API-breaking changes around forms code, necessary to fix conceptual issues. Closes {issue}`182`.
  * `may_init_forms` parameter replaced with `init_forms()`, so that a custom form config can be provided.
    This is particularly required for V8 enabled PDFium.
  * `formtype` attribute replaced with `get_formtype()`.
    Previously, `formtype` would only be set correctly if `may_init_forms=True`,
    which caused confusion for documents that have forms but no initialized form env.
- `PdfPage.get_*box()` functions now provide an option to disable fallbacks. Closes {issue}`187`.
- Some formerly hidden utilities are now exposed in the new namespace `pypdfium2.internal`.


## 4.1.0 (2023-03-07)

- Updated PDFium from `5619` to `5633` (autorelease).


## 4.0.0 (2023-02-28)

- Updated PDFium from `5579` to `5619` (autorelease).
- Full support model rewrite. Many existing features changed and new helpers added. Numerous bugs fixed on the way.
  Read the updated documentation to migrate your code.
- The raw API is now isolated in a separate namespace (`pypdfium2.raw`).
  Moreover, the raw API bindings do not implicitly encode strings anymore (pypdfium2 is now built with a patched version of ctypesgen by default).
- Helper objects now automatically resolve to the underlying raw object if used as ctypes function parameter.
- Overhauled the code base to use `pathlib` and f-strings.
- Updated wheel tags.
- Improved command-line interface, setup code, and documentation.


## 4.0.0b2 (2023-02-23)

- First working beta release for v4.


## 4.0.0b1 (2023-02-22)

- Attempted first beta release for v4. PyPI upload failed due to {issue}`177`.


## History

pypdfium2 is on PyPI since Dec 3, 2021. New versions have been released on a regular basis ever since.

There have been the following version ranges: `0.1 - 0.15`, `1.0 - 1.11`, `2.0 - 2.11`, `3.0 - 3.21.1`.

Entries for releases below version 4 have been removed from the changelog because they were too inconsistent.
