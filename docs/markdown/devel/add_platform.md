<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Adding a new platform
=====================

This document is intended to outline the steps required to support a new platform in
`pypdfium2` that was added to the builds from `pdfium-binaries`.

* Add a new attribute to the class `PlatformDirs` in `platform_setup/packaging_base.py`
  that represents the path to a platform directory in `data/`, following the existing
  naming patterns.
* Insert a corresponding entry into the `ReleaseFiles` dictionary in `platform_setup/update_pdfium.py`.
  The key is the `PlatformDirs` attribute, while the value is the name of the file to download (without extension).
* Add the new wheel tag to the `_get_tag()` function of `platform_setup/setup_base.py`.
  Usually, these platform tags match or are derived from the return of `sysconfig.get_platform()`
  on a device of the platform in question. While Windows generally matches `sysconfig.get_platform()`,
  there are the `manylinux` and `musllinux` standards for Linux. Sometimes you may even have to use
  multiple tags (e. g. `macos_10_xx_{arch}.macos_11_xx_{arch}`).
  Please see related Python documentation, look at the release files of other projects on PyPI that
  support this platform, or ask at `discuss.python.org` if you cannot determine the tag.
  To the author's knowledge, there is no comprehensive list of all possible wheel tags, unfortunately.
* Modify `setup.py`:
    * In `packaging_handler()`, add a case for the corresponding `mkwheel()` call.
      The target string should be the same as the name of the platform directory.
    * In `install_handler()`, add a function to `PlatformManager` to recognise host systems
      of the platform in question, then add the check to the `if/elif` tree.
* In `utilities/setup_all.sh`, insert the new platform identifier into the `whl_targets` array.
* Test your changes:
  * Run something like this:
    ```bash
    # define the setup target (replace `platform_name` with the name of the new platform)
    export PYP_TARGET_PLATFORM="platform_name"
    # download the binary package and call ctypesgen
    python3 platform_setup/update_pdfium.py -p $PYP_TARGET_PLATFORM
    # craft the wheel (-n: no isolation, -x: skip dependency check)
    python3 -m build -n -x --wheel
    ```
  * If all went well, a wheel for the new platform should have been written to `dist/`.
    Inspect it with an archiver tool to ensure the `pypdfium2` directory contains all stuff from
    `src/pypdfium2/`, the bindings file `_pypdfium.py`, and the PDFium binary (one-of `pdfium`,
    `pdfium.dylib`, `pdfium.dll`).
  * Finally, run `make release`. When done, confirm that the new platform wheel is present in
    `dist/`, and that all sanity checks passed (`twine check` and `check-wheel-contents`).
