<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `build_native.py`: When GCC is used, we now declare a `custom_toolchain`, with environment passthrough.
   * First, this avoids inconsistency across different platforms in pdfium's build config, with some expecting just `gcc` and others an arch-prefixed variant. This makes `build_native.py` more likely to work out of the box, relieving callers from the necessity to create symlinks, including our internal cibuildwheel callers.
   * Second, this allows you to use a different version of GCC, or in fact any other compiler, including clang, by setting `CC`, `CXX` and `TOOLPREFIX`.
     This makes `--clang-as-gcc` more straightforward to implement.
   * Also, extra `CFLAGS`, `CPPFLAGS`, `CXXFLAGS` and `LDFLAGS` are now honored in this build mode.
