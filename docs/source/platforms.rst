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

Notes

1. MIPS platforms are not officially part of the manylinux standard, so the wheel tags we use are actually rejected by ``pip``, as they are not in its internal whitelist.
   This can be remedied by re-tagging with ``wheel`` locally to match the host's ``sysconfig.get_platform()`` value.
   ``pip`` maintainers have been informed of this situation.
2. The ``mipsle`` target is untested, for lack of a container and binfmt handler.
3. iOS is untested, and has `special requirements concerning the management of binary extension modules <https://docs.python.org/3/using/ios.html#binary-extension-modules>`_.
   You should be prepared to patch the library search path in ``pypdfium2_raw/bindings.py``.
   Pull requests to pypdfium2 and/or ctypesgen welcome.

Legend
^^^^^^

- **MinVer**: Minimum required OS versions for present release.
  Other build strategies may result in different min versions, and older versions of pypdfium2 may have lower requirements.
  
  + 🟢 Low/Good, 🔵 Reasonable, 🟡 Medium, 🟠 Elevated, 🔴 High, ⚪ Not tagged

- **Release**: status, version tracked, build strategy
  
  + ✅ Wheels on PyPI/GH, 🟩 Wheels on GH only [1]_, 🟦 Setup only
  + 🔄 Latest version, 📌 Pinned version

- **Tier**: Platform support level
  
  + 🟢 1 Core, 🔵 2 Secondary, 🟡 3 Complicated, 🔴 4 Major issues, ⚪ Not classified

- Build strategies
  
  + **PBIN** = Repack external builds from ``bblanchon/pdfium-binaries``.
  + **SBLD** = Built at pypdfium2 via ``sbuild.yaml`` (``build_toolchained.py``).
  + **CIBW** = Built at pypdfium2 via ``cibw.yaml`` (``build_native.py`` + containers on Linux, ``build_toolchained.py`` on Windows and macOS).
  + ✅ Platform supported, ❌ Not supported with that strategy, ⏳Coming soon

- 🐍 Conda *(PBIN only)*
  
  + ✅ Released to conda
  + ⏸️ Built, but conda upload is paused due to storage limits. Get in touch with ``pdfium-binaries`` if you would like this to be reinstated.
  + ❓ Built, but unclear if there were any point releasing this to conda (not a priority)
  + ❌ Not built at pdfium-binaries

- 🧪 Testing status
  
  + ✅ Tested on host
  + ☑️ Tested under emulation (QEMU/Rosetta)
  + 🟨 Only tested when native compilation is used, but it is not the default
  + ❌ Not automatically tested

- 🛠️ Cross compilation indicator
  
  + ⬜ Native compilation
  + 🔳 Cross compilation
  + 🔲 Both is possible / applies

- ⚙️ Compiler used *(CIBW only – PBIN and SBLD always use clang)*

- **NAT**: Can be built natively on-device?
  
  + ✅ Yes (tested on GHA)
  + ☑️ Yes (tested in Docker)
  + 🅿️ Probably (might need minor tweaks)
  + 🚧 This used to work in the past, but is currently broken.

- NA: Not applicable / Unknown (placeholder)

.. [1] Some platforms (LoongArch, MIPS) are rejected by PyPI, as they are not whitelisted in its backend (warehouse).

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
