<!-- SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

Adding a new platform
=====================

This document is intended to outline the steps required to support a new platform in `pypdfium2` that was added to the builds from `pdfium-binaries`.

For a sample implementation, see [Pull Request #92](https://github.com/pypdfium2-team/pypdfium2/pull/92), which added support for `linux_x86`.

* Add a new attribute to the class `PlatformNames` in `platform_setup/packaging_base.py`, following the existing naming patterns.
* Insert a corresponding entry into the `ReleaseNames` dictionary in `platform_setup/update_pdfium.py`. The key is the `PlatformNames` attribute, while the value is the name of the file to download (without extension).
* Add the new wheel tag to the `_get_tag()` function of `platform_setup/setup_base.py`. Usually, these platform tags match or are derived from the return of `sysconfig.get_platform()` on a device of the platform in question. While Windows generally matches `sysconfig.get_platform()`, there are the `manylinux` and `musllinux` standards for Linux. Sometimes you may even have to use multiple tags (e. g. `macos_10_xx_{arch}.macos_11_xx_{arch}`). Please see related Python documentation, look at the release files of other projects on PyPI that support this platform, or ask at `discuss.python.org` if you cannot determine the tag. To the author's knowledge, there is no comprehensive list of all possible wheel tags, unfortunately.
* In `setup.py`, modify `install_handler()`: Add a check to recognise the new host platform and call `_setup()` with the corresponding `PlatformName` attribute as argument.
* In `utilities/setup_all.sh`, insert the new platform identifier into the `whl_targets` array.
* Test your changes:
  * Run something like this:
    ```bash
    # define the setup target (replace `platform_name` with the name of the new platform)
    export PYP_TARGET_PLATFORM="platform_name"
    # download the binary package and call ctypesgen
    python3 platform_setup/update_pdfium.py -p "$PYP_TARGET_PLATFORM"
    # craft the wheel, according to the target platform environment variable
    # (-n: no isolation, -x: skip dependency check)
    python3 -m build -n -x --wheel
    ```
  * If all went well, a wheel for the new platform should have been written to `dist/`. Inspect it with an archiver tool to ensure the `pypdfium2` directory contains all stuff from `src/pypdfium2/`, the bindings file `_pypdfium.py`, and the PDFium binary (one-of `pdfium`, `pdfium.dylib`, `pdfium.dll`).
  * Run `make release`. When done, confirm that there were no errors, the new platform wheel is present in `dist/`, and all sanity checks passed (`twine check` and `check-wheel-contents`).
  * Finally, create an entry for the next release in `docs/markdown/changelog.md` and note that you added support for a new platform.
  * Make a new branch, add and commit your changes. Example:
    ```bash
    # replace `new_platform` with any name of your liking
    # (if you are the maintainer yourself and intend to push the changes directly into main,
    # feel free to skip this step and the pull request)
    git branch new_platform; git checkout new_platform
    # show changed files
    git status
    # stage the changes
    git add file_1 file_2 ...  # or `git add *`
    # create a commit
    git commit -m "Added support for new platform xyz" -m "(longer description, if necessary)"
    ```
    (It may be more convenient to use a GUI such as `git-cola`, `qgit`, or `GitAhead`)
  * Submit a Pull Request:
    ```bash
    # using the interactive GitHub CLI
    gh pr create
    ```
  * At best, install the created wheel on the target platform, run the test suite (`python3 -m pytest tests/`) and report success or failure.
