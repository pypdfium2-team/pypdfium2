<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Removed pypdfium2's own conda packaging following [thorough](https://github.com/mindee/doctr/discussions/2127) [consideration](https://github.com/mindee/doctr/issues/113#issuecomment-5340008535).
  * Key reasons include that it ended up covering far less platforms than our PyPI packages, did not integrate with our own build strategies, and seemed fraught with workarounds.
  In part, this has been a result of outsourcing the pdfium dependency (which however seemed like the only viable option prior to [CEP 20](https://github.com/conda/ceps/blob/main/cep-0020.md)), along with other limitations, like the conda ecosystem generally supporting less platforms, and tight storage limits at `anaconda.org` that push maintainers towards making tradeoffs between release frequency and platform inclusion vs. sustainability.
    There is no fallback setup, either, which even seems to be an intentional limitation of conda's.
  * To add to that, builds in a custom channel are inaccessible to dependents within the main anaconda/conda-forge ecosystems themselves, and generally a pain to manage, which resulted in negligible demand compared to PyPI. In short, the problems are manifold and technical debt is not far off.
  * This means conda is effectively a third-party package environment similar to nixpkgs or Linux distribution packaging, unlike PyPI, which is a first-party package index where upstream authors publish directly. Conda build tools did not feel like being conceived for in-project packaging, either (the contrast to PyPA build backends is quite stark).
    Overall, there has been an unjustifably high complexity and amount of workarounds in relation to the low or nonexistent benefit.
  * To be clear, any builds of pypdfium2 in conda-forge or anaconda/main are [unofficial (third-party)](https://github.com/pypdfium2-team/pypdfium2#unofficial-packages). We generally do not recommend using third-party distributions of pypdfium2, and their varying maintainership seems a potential concern. Anyway, we cannot support what we don't maintain.
  * Instead, we want to highlight that you can just install pypdfium2 from PyPI even in a conda env. There are no mandatory runtime dependencies, so the usual reasons against mixing in PyPI packages do not apply.
- Lowered iOS min version from 26_0 to 17_0 thanks to an upstream contribution. (We have not released any iOS wheels yet, but it is handled in setup.)
