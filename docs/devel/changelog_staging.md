<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Removed pypdfium2's own conda packaging following [thorough](https://github.com/mindee/doctr/discussions/2127) [consideration](https://github.com/mindee/doctr/issues/113#issuecomment-5340008535).
  * Key reasons include that it was over-complex and not agnostic of our own build strategies, as a result of outsourcing the pdfium dependency, which was the only viable option prior to [CEP 20](https://github.com/conda/ceps/blob/main/cep-0020.md) (our conda packaging layout predates that change).
  * Along with tight storage limits at `anaconda.org`, pypdfium2's conda packages ended up covering far less platforms than we do with PyPI wheels.
  * To add to that, builds in a custom channel are not accessible to dependents within the main anaconda/conda-forge ecosystems themselves, and generally a pain to manage, which resulted in negligible demand compared to PyPI.
  * This means conda is effectively a *third-party* package environment similar to nixpkgs or Linux distribution packaging, unlike PyPI, which is a *first-party* package index where upstream authors publish directly. Conda build tools did not feel like being conceived for in-project packaging, either (the contrast to PyPA build backends is quite stark).
  * Any builds of pypdfium2 in `conda-forge` or `anaconda/main` are [unofficial (third-party)](https://github.com/pypdfium2-team/pypdfium2#unofficial-packages). We generally do not recommend using third-party distributions of pypdfium2, and their varying maintainership seems a potential safety concern. In any case, we cannot support what we don't maintain.
  * Instead, we want to highlight that you can just install pypdfium2 from PyPI even in a conda env. There are no mandatory runtime dependencies, so the usual reasons against mixing in PyPI packages do not apply. Also, there is the novel `conda-pypi` bridge which should finally provide better integration with the PyPI world.
- Lowered iOS min version from `26_0` to `17_0` thanks to an upstream contribution.
  (We have not released any iOS wheels yet, but it is handled in setup.)
