<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `PdfDocument`: When encoding input filepath to `UTF-8`, use the `surrogateescape` error handler (except on Windows).
  This fixes loading some garbled filenames, where a default `.encode("utf-8")` call would raise `UnicodeEncodeError`. Thanks to Filipe Litaiff for the report.
- The CLI has moved from `pypdfium2._cli` to `pypdfium2_cli`, i.e. an own submodule.
  `pypdfium2.__main__` and `python3 -m pypdfium2` are deprecated. Use `pypdfium2_cli.__main__` and `python3 -m pypdfium2_cli` or the `pypdfium2` entrypoint instead.
  This has been necessary since a module's `__main__.py` implies its `__init__.py`, which gives us no chance to prepare before library init if `__main__.py` lives in the `pypdfium2` module itself.
- Added new helper `PdfSysfontBase`. Wraps `FPDF_SYSFONTINFO` and related APIs.
  Callers can subclass from `PdfSysfontBase` to inspect or alter the way PDFium uses system fonts. This is a first step towards implementing a warning mechanism for missing system fonts or substitution. Thanks to `scyyh11` for related proposals, and especially a hint on passing the right pointer in callbacks.
- Added `PdfiumWarning` (subclass of `Warning`). A `PdfiumWarning` is now issued on XFA forms load failure, with programmatic error code info, rather than just a log message.
- Added new subomdule stub `pypdfium2_cfg`, which can be imported before `pypdfium2` for init-time configuration. The `DEBUG_AUTOCLOSE` setting has been moved to this module. In the future, `pypdfium2_cfg` may be extended to give callers control over how pypdfium2 initializes PDFium (e.g. custom font paths).
- Split off `pypdfium2_raw/version.py` from `pypdfium2/version.py`, so that `PDFIUM_INFO` is now available from within `pypdfium2_raw`. This has been necessary to implement a target-specific workaround (see below).
- `build_native.py`: When GCC is used, we now declare a `custom_toolchain`, with environment passthrough.
   * First, this avoids inconsistency across different platforms in pdfium's build config, with some expecting just `gcc` and others an arch-prefixed variant. This makes `build_native.py` more likely to work out of the box, relieving callers from the necessity to create symlinks, including our internal cibuildwheel callers.
   * Second, this allows you to use a different version of GCC, or in fact any other compatible compiler, including clang, by setting `CC`, `CXX` and `TOOLPREFIX`.
     This makes `--clang-as-gcc` more straightforward to implement.
   * Also, extra `CFLAGS`, `CPPFLAGS`, `CXXFLAGS` and `LDFLAGS` are now honored in this build mode.
- Basic FreeBSD CI added (powered by `cross-platform-actions`), testing installation with libreoffice-pdfium.
  - On (Free)BSD with libreoffice-pdfium, pre-load implicit dependency libraries with `mode=RTLD_GLOBAL` to fix library load.
