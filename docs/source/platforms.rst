.. SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

Platforms
=========

Platform support & build strategies (as of 06/2026)

.. csv-table::
   :file: ../../PLATFORMS.csv
   :header-rows: 1
   :class: fullwidth-table

Legend:

- Build strategies
  
  + **PBIN** = Repack external builds from ``bblanchon/pdfium-binaries``.
  + **SBLD** = Built at pypdfium2 via ``sbuild.yaml`` (``build_toolchained.py``).
  + **CIBW** = Built at pypdfium2 via ``cibw.yaml`` (``build_native.py`` + containers on Linux, ``build_toolchained.py`` on Windows and macOS).
 
- **MinVer**: Minimum required OS versions for present release.
  Other build strategies may result in different min versions, and older releases of pypdfium2 may have lower min versions.
  On Linux, low glibc requirements can be achieved by using upstream's sysroots.
  The CIBW strategy typically results in higher glibc requirements, since sysroots don't work in GCC build mode yet, and are not unavailable for some targets (e.g. ``loong64``, ``s390x``).
  
  + 🟢 Low/OK, 🟡 Medium/Acceptable, 🟠 Elevated, 🔴 High, ⚪ Uncertain / not tagged

- **Release** (status, version tracked, build strategy)
  
  + ✅ PyPI/GH, 🟩 GH only (platform not accepted by PyPI), 🟨 Setup only
  + 🔄 Latest version, 📌 Pinned version
