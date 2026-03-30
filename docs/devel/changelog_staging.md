<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- CLI: `pypdfium2._cli` has moved to `pypdfium2_cli`, i.e. an own submodule.
  `pypdfium2.__main__` and `python3 -m pypdfium2` are deprecated. Use `pypdfium2_cli.__main__` and `python3 -m pypdfium2_cli` or the `pypdfium2` entrypoint instead.
  This has been necessary because a module's `__main__.py` implies the respective `__init__.py`, which gives us no chance to prepare before library init if `__main__.py` lives in the `pypdfium2` module itself.
- TODO: pypdfium2_cfg, sysfontinfo
- `PdfDocument`: When encoding input filepath to `UTF-8`, use the `surrogateescape` error handler (except on Windows). This fixes loading some garbled filenames, where a default `.encode("utf-8")` call would raise `UnicodeEncodeError`. Thanks to Filipe Litaiff for the report.
- `build_native.py`: When GCC is used, we now declare a `custom_toolchain`, with environment passthrough.
   * First, this avoids inconsistency across different platforms in pdfium's build config, with some expecting just `gcc` and others an arch-prefixed variant. This makes `build_native.py` more likely to work out of the box, relieving callers from the necessity to create symlinks, including our internal cibuildwheel callers.
   * Second, this allows you to use a different version of GCC, or in fact any other compatible compiler, including clang, by setting `CC`, `CXX` and `TOOLPREFIX`.
     This makes `--clang-as-gcc` more straightforward to implement.
   * Also, extra `CFLAGS`, `CPPFLAGS`, `CXXFLAGS` and `LDFLAGS` are now honored in this build mode.
- Basic FreeBSD CI added, powered by `cross-platform-actions`.
- On (Free)BSD with libreoffice-pdfium, pre-load implicit dependency libraries with `mode=RTLD_GLOBAL` to fix library loading.
- Split off `pypdfium2_raw/version.py` from `pypdfium2/version.py`, so that `PDFIUM_INFO` is now available from within `pypdfium2_raw`. This was a pre-requisite to implement the above FreeBSD workaround.
