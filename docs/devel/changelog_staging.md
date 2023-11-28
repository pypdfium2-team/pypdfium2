<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Improved issue templates, added pull request template.
- conda/workflows: Added ability to (re-)build pypdfium2_raw bindings with any given version of pdfium. Fixes {issue}`279`.
- conda: Improved installation docs and channel config.
- Made reference bindings more universal by including V8, XFA and Skia symbols. This is possible due to the dynamic symbol guards.
- setup: Fixed blunder in headers cache logic that would cause existing headers to be always reused regardless of version. *Note, this did not affect release workflows, only local source re-installs.*
- Show path of linked binary in `pypdfium2 -v`.
