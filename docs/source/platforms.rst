.. SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

.. raw:: html

   <style>
   .wy-table-responsive {  /* :has(.fullwidth-table) */
     width: 100% !important;
     max-width: 100% !important;
     flex-grow: 1 !important;
     overflow: visible !important;
   }
   
   .wy-table-responsive .fullwidth-table {
     width: 100% !important;
   }
   </style>


Platforms
=========

Platform support & build strategies (as of 06/2026)

.. csv-table::
   :file: ../../PLATFORMS.csv
   :header-rows: 1
   :class: fullwidth-table


Legend
------

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
  
  + ✅ Wheels on PyPI/GH, 🟩 Wheels on GH only (platform rejected by PyPI), 🟨 Setup only
  + 🔄 Latest version, 📌 Pinned version

.. admonition:: Help wanted
   
   Reckon you can turn more ❌ into ✅ ? Please give it a try & open a PR.


Other platforms
---------------

.. csv-table::
   :header-rows: 1
   
   Platform,Status,Comment
   FreeBSD,⬜,1
   OpenBSD / \*BSD,❌,2
   Illumos,❌,2
   Haiku,❌,2
   SerenityOS,❌,2
   AIX,❌,2
   z/OS,❌,2

1) Fallback installation with libreoffice-pdfium should work and is occasionally tested on our CI.
   Note, however, that libreoffice-pdfium is a bit incomplete.
   Building from source might work with a feasible amount of patching.
   It *may* be possible to provide prebuilds for x86_64 in the future.
   There is also upstream work in progress to have PDFium added to the ports collection.
2) No known PDFium prebuilds available for this platform.
