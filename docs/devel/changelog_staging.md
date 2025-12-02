<!-- SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com> -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<!-- List character: dash (-) -->

# Changelog for next release
- Added new builds `android_{armv8a,armv7a}` and `{many,musl}linux_{ppc64le,riscv64,loongarch64}`, and `musllinux_armv7l` to the release process. This greatly improves platform support. Loongarch is only uploaded to GH, as PyPI doesn't accept it yet. Replaced `musllinux_{x86_64,aarch64,i686}` with our own builds, as they are a bit smaller than the pdfium-binaries.
- `build_native.py`: Added full dependency library vendoring abilities. This is now the default behavior on fallback setup. Integrated ninja/gn bootstrapping helpers.
- CIBW workflow: Use vendored libraries for most Linux targets. Build `ppc64le, riscv64, loongarch64` (and theoretically `s390x`) using static clang that runs on the host architecture (even though from within an emulated container), while being pre-configured for cross-compilation to the target architecture. This is much faster than building with an emulated compiler. Many thanks to Matthieu Darbois (mayeut) of pypa/manylinux for coming up with this approach.
- Greatly simplified verification of pdfium-binaries attestation in pypdfium2's setup. Thanks to Benoît Blanchon for attaching the attestation as artifact.
- Enabled immutability for pypdfium2's GitHub releases, and added build provenance attestations, like pdfium-binaries did.
