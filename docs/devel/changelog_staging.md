<!-- SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release

- Changed `PDFIUM_PLATFORM=none` to strictly exclude all data files. Added new target `system` consuming bindings and version files supplied by the caller. Again, the setup API implications were accepted. Packagers that used `none` to bind to system pdfium will have to update.
- Enhanced integration of separate modules. This blazes the trail for conda packaging. We had to move metadata back to `setup.cfg` since we need a dynamic project name, which `pyproject.toml` does not support.
- Major improvements to version integration.
  * Ship version info as JSON files, separately for each submodule. Expose as immutable classes. Legacy members have been retained for backwards compatibility.
  * Autorelease uses dedicated JSON files for state tracking and control.
  * Read version info from `git describe`, providing definite identification.
  * If a local git repo is not available or `git describe` failed (e.g. sdist or shallow checkout), fall back to a supplied version file or the autorelease record. However, you are strongly encouraged to provide a setup that works with `git describe` where possible.
- Added musllinux aarch64 wheel. Thanks to `@jerbob92`.
