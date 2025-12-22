<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Fixed inclusion of `loongarch64` build in GH attestation. This was an oversight in the workflow.
- `ppc64le (glibc)` is now built at pdfium-binaries using upstream's tooling.
  This means pypdfium2's conda builds now also support this platform.
  Updated pypdfium2's setup/workflow accordingly to use the pdfium-binaries.
