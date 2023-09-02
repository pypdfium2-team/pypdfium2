<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

This release backports some key fixes/improvements from the development branch:
- [V8/XFA] Fixed XFA init. This issue was caused by a typo in a struct field. Thanks to Benoît Blanchon.
- [V8/XFA] Expose V8/XFA exclusive members in the bindings file by passing ctypesgen the pre-processor defines in question.
- Fixed sourcebuild with system libraries.
- Attempt to fix automatic GH pages rebuild on release.
