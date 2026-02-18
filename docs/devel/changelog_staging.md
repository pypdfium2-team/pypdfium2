<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Windows-only members are now included in bindings where applicable. Thanks to `NullYing` for an incentive to fix this.
  Callers who want to use this API, note: it is strongly recommended that you `ctypes.cast()` the HDC object created on your side to our internal `pypdfium2.raw.HDC` before passing it into `FPDF_RenderPage()` to ensure compatible types regardless of how the bindings were generated.
- `build_native.py`: The `--reset` option now does `git restore .` rather than `git reset --hard`. This may be significantly more efficient.
- `build_native.py`: If `--test` is given, honor the unittests' return code. Suppress a musl-specific failure. Fixed `pdfium_unittests` not running on musl with clang by applying a build patch.
