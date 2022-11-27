<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Full support model rewrite. Many existing features changed and new helpers added. Numerous bugs fixed on the way.
  Read the updated documentation to migrate your code.
- The raw API is now isolated in a separate namespace (`pypdfium2.raw`).
  Moreover, the raw API bindings do not implicitly encode strings anymore (pypdfium2 is now built with a patched version of ctypesgen by default).
- Improved command-line interface.
- Documentation improvements.
