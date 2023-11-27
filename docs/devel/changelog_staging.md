<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Improved issue templates, added pull request template.
- conda/workflows: Added ability to (re-)build pypdfium2_raw bindings for any given version of pdfium. Fixes {issue}`279`.
- conda: Improved installation docs and channel config.
- Made reference bindings more universal by including V8, XFA and Skia exclusive symbols. This is possible as the reference bindings have dynamic symbol guards.
- setup: Fixed blunder in headers cache logic that would always reuse existing headers and fail to update. *Note, this did not affect release workflows, only local re-installs.*
- Show path of linked binary in `pypdfium2 -v`.
