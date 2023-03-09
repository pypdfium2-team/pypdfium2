<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- API-breaking changes around forms code, necessary to fix conceptual issues.
  * `may_init_forms` parameter replaced with `init_forms()`, so that a custom form config can be provided.
    This is particularly required for V8 enabled PDFium.
  * `formtype` attribute replaced with `get_formtype()`.
    Previously, `formtype` would only be set correctly if `may_init_forms=True`,
    which caused confusion for documents that have forms but no initialized form env.
