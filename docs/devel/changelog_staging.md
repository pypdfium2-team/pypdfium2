<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Experimental ``pyemscripten_2026_0_wasm32`` (Pyodide) build support added. *However, the resulting builds are flaky at runtime and subject to various types of seemingly random crashes. Freezes on shutdown have also been observed.*<br>
  While these issues persist, PyEmscripten wheels will not be uploaded to PyPI, but they are included in the release process and can be downloaded from GitHub on an experimental basis.
  If you can help track down and fix these issues, please reach out.<br>
  Note: Our PyEmscripten wheels are bigger than usual, as they are built with debug symbols (a non-debug build is not considered useful at this stage).
- Fixed compatibility with Python 3.6 and 3.7.
  * Runtime support was inadvertently broken due to a faulty cached property backport which held only one cache per class, not per instance as should have been.
    The accidental loss of caches broke key assumptions of our autoclose logic, which relies on `cached_property` since 5.8.0. (Earlier versions that did not make extensive use of cached properties might work but have not been explicitly tested.)
  * This release replaces both `functools.cached_property` and the faulty `functools.lru_cache()` based backport with our own, backward compatible `cached_property` implementation along with thorough documentation.
  * Also, fixed setup (i.e. source installation) with Python 3.6 and its max available setup dependency versions (that is, `setuptools` 59).
    - This had probably been broken for a long time. (A few non-breaking issues remain, e.g. for some reason we end up with a `purelib` directory, but it should be `platlib`.)
    - Note that ctypesgen continues to require Python `>=3.8` at this time (with 3.6 compatibility not being a priority in this case), but you can install with `--no-build-isolation` and let the reference bindings be used, or try adding ctypesgen's `src/` to `PYTHONPATH` to bypass setup, and see how it goes.
  * Maintainer's note: Python 3.6 was a very decent version of Python – the first to have f-strings and insertion order preserving dictionaries –, and has been supported by stable distributions like SUSE, RHEL and Ubuntu for a long time, so it is still considered worth restoring support.
  * However, to be clear, **we do not plan to (and practically cannot) keep up compatibility with outdated Python versions indefinitely**. In fact, it is anticipated that setup compatibility may soon be given up in favor of contemporary Python packaging concepts, like migrating as much as possible to `pyproject.toml`. That said, we are happy to restore compatibility at this point, and fix any *unintentional* breakage.
- Fixed `MANIFEST.in` missing Windows spoof headers, which resulted in subtly incorrect bindings when installing from an sdist on Windows, as seen in test failures. (Release wheels have been unaffected and passed the test suite, so this issue went unnoticed for a while.)
- Bumped `gn-dist` from `2407.1` to `2407.3`. Made its setup python 3.6 compatible likewise (wheels should have worked before now). Changed versioning and release process so that CI no longer needs to push to the repository (may eventually become a blueprint for pypdfium2 itself). More documentation added, including `manylinux2014` POC.
- Internal improvements (non-exhaustive):
  * Properly clean up `*.egg-info/` and `build/` before packaging, to avoid mad file inclusion bugs (ran into this while working on setup include rules).
  * Migrated from requirements files to PEP 735 dependency groups (`pyproject.toml`).
    Recent enough `pip` should be available to Python >= 3.9. For compatibility with older versions, feel free to use `./utils/misc/install_dep_group.py -f`.
  * Applied dependency cooldowns to internal callers of `pip install`. Always use virtual environments. Use lockfiles in sensitive areas (e.g. publish jobs).
  * Rearranged & improved utilities. Cleaner distinction between `setupsrc/` and `utils/`.
  * Fixed persistent i686 container network issues by downgrading host runner to `24.04`.
