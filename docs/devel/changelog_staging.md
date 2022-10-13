<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Disruption: Two components of `PdfDocument` have been removed to clean up the code (without a major release, due to their insignificance):
  - Removal of `update_rendering_input()`. Callers are expected to save and re-open the document on their if they wish that changes take effect with the multi-page renderer.
  - The multipage renderer does not implicitly read byte buffers into memory anymore. Callers are expected to take an explicit decision by providing a different input in the first place.
- Added a new support model `PdfImageObject` (which inherits from `PdfPageObject`). This can be used to insert a JPEG image into a page, get metadata, etc.
- Docs: The changelog page now selectively includes an entry for the next release that may be shown on `latest` builds.
