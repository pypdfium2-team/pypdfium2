<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

This release backports some key fixes/improvements from the development branch:
- [V8/XFA] Fixed XFA init. This issue was caused by a typo in a struct field. Thanks to Benoît Blanchon.
- [V8/XFA] Expose V8/XFA exclusive members in the bindings file by passing ctypesgen the pre-processor defines in question.
- Fixed some major non-API implementation issues with multipage rendering:
  * Avoid full state data transfer and object re-initialization for each job. Instead, use a pool initializer and exploit global variables. This also makes bytes input tolerable for parallel rendering.
  * In the CLI, use a custom converter to save directly in workers instead of serializing bitmaps to the main process.
- Set pdfium version fields to unknown for `PDFIUM_PLATFORM=none` (sdist). This prevents encoding a potentially incorrect version. Also improve CLI version print.
- Fixed sourcebuild with system libraries.
- Fixed RTD build (`system_packages` option removal).
- Attempt to fix automatic GH pages rebuild on release.
