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

Platform support & build strategies (as of 07/2026)

Covered platforms
-----------------

.. csv-table::
   :file: ../../PLATFORMS.csv
   :header-rows: 1

.. [1] Since v5.12.0, build strategies used and platforms included may vary between releases. pypdfium2's GitHub releases contain the authoritative strategy info, while this table currently reflects our ``default`` release profile.
.. [2] MIPS platforms are not officially part of the manylinux standard, so the wheel tags we use are actually rejected by ``pip``, as they are not in its internal whitelist.
   This can be remedied by re-tagging with ``wheel`` locally to match the host's ``sysconfig.get_platform()`` value.
   ``pip`` maintainers have been informed of this situation.
.. [3] Untested, for lack of a container and binfmt handler.
.. [4] Native compilation on Android (Termux) once worked in the past, with a rather early version of ``build_native.py`` and a pre-PEP738 interpreter, but this broke at some point, and it was eventually decided to remove the code passages. See `here <https://github.com/pypdfium2-team/pypdfium2/blob/35ea0c1687d92f5828d5f84316fddfa311975b03/README.md?plain=1#L224-L279>`_ for historical instructions.
.. [5] iOS is untested, and has special considerations regarding the `management of binary extension modules <https://docs.python.org/3/using/ios.html#binary-extension-modules>`_.
   You should be prepared to patch the library search path in ``pypdfium2_raw/bindings.py``.
   Pull requests to pypdfium2 and/or ctypesgen welcome.
.. [6] Though the ``pdfium-binaries`` project does provide WASM builds, they are actually incompatible with Pyodide/ctypes, which require a ``.so`` shared library side module, not a ``.wasm`` blob.
.. [7] While there is experimental Pyodide build support, the resulting builds are known to be flaky at runtime. Use with caution and not in a production environment! If you can help fix these issues, please reach out :)

.. TODO consider publishing macOS universal & android x86_64/x86 wheels to GH ?

Legend
^^^^^^

- **MinVer**: Minimum required OS versions for present release.
  Other build strategies may result in different min versions, and older versions of pypdfium2/pdfium may have lower requirements.
  
  + 🟢 Low/Good, 🔵 Reasonable, 🟡 Medium, 🟠 Elevated, 🔴 High, ⚪ Not tagged

- **Release**:
  
  + Status:
    
    * ✅ Wheels on PyPI & GH
    * 🟩 GH only - Rejected by PyPI (not whitelisted in backend)
    * ❎ GH only - Intentionally not uploaded to PyPI
    * 🟦 Setup only
    * 🟨 Setup only (unresolved issues / untested)
  
  + Version tracked: 🔄 Latest / 📌 Pinned
  + Strategy: see below

- **Tier**: Platform support level
  
  + 🟢 1 Core, 🔵 2 Secondary, 🟡 3 Complicated, 🔴 4 Major issues, ⚪ Not classified

- Strategies
  
  + **PBIN** = Repack external builds from ``bblanchon/pdfium-binaries``.
  + **SBLD** = Built at pypdfium2 via ``sbuild.yaml`` (``build_toolchained.py``).
  + **CIBW** = Built at pypdfium2 via ``cibw.yaml`` (``build_native.py`` + containers on Linux, ``build_toolchained.py`` on Windows and macOS).
  + ✅ Platform supported, ❌ Not supported with that strategy, ⏳In planning

- 🐍 Conda *(PBIN only)*
  
  + ✅ Released to conda
  + ⏸️ Built, but conda upload is paused due to storage limits. Get in touch with ``pdfium-binaries`` if you would like this to be reinstated.
  + ❓ Built, but unclear if there were any point releasing this to conda (not a priority)
  + ❌ Not built at pdfium-binaries

- 🧪 Testing status
  
  + ✅ Tested on host
  + ☑️ Tested under emulation
  + ❌ Not automatically tested

- 🛠️ Cross compilation indicator
  
  + ⬜ Native compilation
  + 🔳 Cross compilation
  + 🔲 Both is possible / applies

- ⚙️ Compiler used *(CIBW only – PBIN and SBLD always use clang)*

- **DEV**: Can be built from source natively on-device?
  
  + ✅ Yes (tested with GHA)
  + ☑️ Yes (tested with Docker)
  + 🅿️ Probably (might need minor tweaks)

- **N**: Notes

- Common identifiers
  
  + ``NA`` Not applicable / unknown (placeholder)
  + 👷 Work in progress
  + 🚧 This used to work in the past, but is currently broken

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
