<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Update build scripts from PDFium `8146` to `8149`. This release is again made with the `prefer-sbuild` strategy.
- Fixed a blunder in the autoclose machinery. We mustn't ever iterate over object trackers directly as they can change any time, because GC might run a finalizer removing an item from the tracker. We hope that first making a shallow copy should prevent this condition. The issue had been introduced in v5.8.0 but went unreported and unnoticed by the author until this day. Many thanks to `@vuongphamxd05` for this outstanding catch.
