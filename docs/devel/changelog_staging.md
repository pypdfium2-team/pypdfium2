<!-- SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Experimental PyEmscripten wasm32 (Pyodide) build support added. However, the resulting builds are known to be flaky at runtime and susceptible to various types of seemingly random crashes. Freezes at shutdown have also been observed.
  Given that, PyEmscripten wheels will not be uploaded to PyPI at this time; however, they are included in the release process and can be downloaded from GitHub for experimentation.
  If you can help track down and fix these issues, please reach out.
  Note: Our PyEmscripten wheels are bigger than usual, since they are built with debug symbols. A non-debug build would be smaller but is not considered useful at this time.
- Fixed compatibility with Python 3.6 and 3.7.
  * Runtime support was inadvertently broken due to a faulty cached property backport which held only one cache per class, not per instance as should have been.
    The accidental loss of caches broke key assumptions of our autoclose logic, which relies on `cached_property` since 5.8.0. (Earlier versions that did not make extensive use of cached properties should work in essentials, but have not been explicitly tested.)
  * This release replaces both `functools.cached_property` and the faulty `functools.lru_cache()` based backport with our own, backward compatible `cached_property` implementation along with thorough documentation.
  * Also, fixed setup (i.e. source installation) with Python 3.6 and its max available setup dependency versions (that is, `setuptools` 59).
    - This had probably been broken for a long time. (A few non-breaking issues remain, e.g. for some reason we end up with a `purelib` directory, but it should be `platlib`.)
    - Note that ctypesgen continues to require Python `>=3.8` at this time (with 3.6 compatibility not being a priority here), but you can install with `--no-build-isolation` and let the reference bindings be used, or try adding ctypesgen's `src/` to `PYTHONPATH` to bypass setup, and see how it goes.
  * Python 3.6 was a very decent version of Python – the first to have f-strings and insertion order preserving dictionaries –, and has been supported by stable distributions like SUSE, RHEL and Ubuntu for a long time, so it is still considered worth restoring support.
  * However, to be clear, **we do not plan to (and practically cannot) keep up compatibility with outdated Python versions indefinitely**. In fact, it is anticipated that setup compatibility may be given up some time soon in favor of contemporary Python packaging concepts, like migrating as much as possible to `pyproject.toml`. That said, we are happy to restore compatibility at this point, and fix any *unintentional* breakage.
- `gn-dist` improvements: Made setup Python 3.6 compatible (wheels should have worked before now). Changed versioning and release process so that CI no longer needs to push to the repository (may eventually become a blueprint for pypdfium2 itself). More documentation added, including `manylinux2014` POC.
- With `container_driver.py`, added ability to test source installation, and to select another container image. This can be used to test pypdfium2 in a manylinux2014 container with Python 3.6.
- TODO document CI changes (package installation cooldowns), MANIFEST.in fix, PEP 735 dependency groups etc., Lockfiles, i686 containers
