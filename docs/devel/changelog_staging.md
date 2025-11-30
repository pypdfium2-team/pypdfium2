<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- `build_native.py`: added ability to build with vendored libc++.
- CIBW workflow: Build extra architectures `ppc64le, riscv64, loongarch64` (and theoretically `s390x`) using static clang that runs on the host architecture (even though from within an emulated container), while being pre-configured for cross-compilation to the target architecture. This is much faster than building with an emulated compiler. Many thanks to Matthieu Darbois (mayeut) of pypa/manylinux for coming up with this approach.
