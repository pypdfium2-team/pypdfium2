.. SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
.. SPDX-License-Identifier: CC-BY-4.0

.. raw:: html

   <style>
   /* Let tables expand to the right freely instead of being limited to RTD's max width + horizontal scroll bar */
   .wy-table-responsive {
     overflow: visible !important;
   }
   
   /* Set a custom width for this table class */
   table.other-platforms-table {
     width: 830px !important;
   }
   /* Wrap text at newlines */
   /* https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/white-space */
   table.other-platforms-table td {
     white-space: pre-line !important;
   }
   </style>


Platforms
=========

Platform support & build strategies (as of 06/2026)

Covered platforms
-----------------

.. csv-table::
   :file: ../../PLATFORMS.csv
   :header-rows: 1

Legend
^^^^^^

- **MinVer**: Minimum required OS versions for present release.
  Other build strategies may result in different min versions, and older versions of pypdfium2 may have lower requirements.
  
  + 🟢 Low/OK, 🟡 Medium/Acceptable, 🟠 Elevated, 🔴 High, ⚪ Uncertain / not tagged

- **Release**: status, version tracked, build strategy
  
  + ✅ Wheels on PyPI/GH, 🟩 Wheels on GH only (platform rejected by PyPI), 🟦 Setup only
  + 🔄 Latest version, 📌 Pinned version

- **Tier**: Platform support level
  
  1. 🟢 Best / Core platform
  2. 🔵 Passable / Secondary platform
  3. 🟡 More complicated
  4. 🔴 Big known issues (e.g. endianness bugs)
  5. ⚪ Not classified

- Build strategies
  
  + **PBIN** = Repack external builds from ``bblanchon/pdfium-binaries``.
  + **SBLD** = Built at pypdfium2 via ``sbuild.yaml`` (``build_toolchained.py``).
  + **CIBW** = Built at pypdfium2 via ``cibw.yaml`` (``build_native.py`` + containers on Linux, ``build_toolchained.py`` on Windows and macOS).

- 🧪 Testing status
  
  + ✅ Tested on a native host
  + ☑️ Tested in an emulated container
  + 🟨 Tested when native compilation is used, untested otherwise.
  + ❌ Not automatically tested

- ✖️ Cross compilation status
  
  + ⬜ Native compilation
  + 🔳 Cross compilation
  + 🔲 Both is possible

- ⚙️ Compiler used (CIBW only, PBIN and SBLD always use clang)

- **NAT**: Can be built natively at end user level?
  
  + ✅ Yes
  + ☑️ Yes (tested in docker)
  + ❔ Unknown
  + 🚧 This used to work in the past, but is currently broken.

.. admonition:: Help wanted
   
   Reckon you can turn more ❌ into ✅ ? Please give it a try and open a PR.


Other platforms
---------------

.. list-table::
   :header-rows: 1
   :class: other-platforms-table
   
   * - Platform
     - Status
     - Comment
   * - FreeBSD
     - 🟦
     - Fallback installation with libreoffice-pdfium should work, and we occasionally test it on CI.
       Note, however, that libreoffice-pdfium tends to be a bit incomplete.
       Building from source might work with a feasible amount of patching.
       It *may* be possible to provide prebuilds for x86_64 in the future.
       There is also upstream work in progress to have PDFium added to the ports collection.
   * - OpenBSD / \*BSD
     - ❓
     - Libreoffice is not built with PDFium on OpenBSD.
       However, if building on FreeBSD is possible, it may be doable on other BSDs, too.
   * - Illumos
     - ❌
     - No known prebuilds available. PDFium has not been ported to this platform.
   * - Haiku
     - ❌
     - No known prebuilds available. PDFium has not been ported to this platform.
   * - SerenityOS
     - ❌
     - No known prebuilds available. PDFium has not been ported to this platform.
   * - AIX
     - ❓
     - No known prebuilds available. Proprietary OS.
       Chromium build infrastructure appears to have some degree of support for AIX but the exact status is unknown.
   * - z/OS
     - ❌
     - No known prebuilds available. PDFium has not been ported to this platform. Proprietary OS.
