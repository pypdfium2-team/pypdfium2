<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Removed pypdfium2's conda packaging following [thorough](https://github.com/mindee/doctr/discussions/2127) [consideration](https://github.com/mindee/doctr/issues/113#issuecomment-5340008535).
  Key reasons include that it was over-complex and not agnostic of our own build strategies, as a result of outsourcing the pdfium dependency (which was the only viable option prior to [CEP 20](https://github.com/conda/ceps/blob/main/cep-0020.md) – our implementation predated this change).
  Along with tight storage limits at `anaconda.org`, pypdfium2's conda packages ended up covering far less platforms than we do with PyPI wheels.
  To add to that, builds in a custom channel are not accessible to dependents within the main anaconda/conda-forge ecosystems themselves, which resulted in negligible demand compared to PyPI.
- Lowered iOS min version from `26_0` to `17_0` thanks to an upstream contribution.
  (We have not released any iOS wheels yet, but it is handled in setup.)
