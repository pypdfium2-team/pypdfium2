#!/bin/bash
# SPDX-FileCopyrightText: 2025 Matthieu Darbois
# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileComment: From scikit-build/ninja-python-distributions. License assumed from project license.

# Stop at any error, show all commands
set -exuo pipefail

STAGING_DIR="/tmp"
SCRIPT_MODE=""

while getopts "d:m:" OPTION
do
  case $OPTION in
    d)
		STAGING_DIR="$OPTARG"
		echo "download dir: $STAGING_DIR";;
	m)
		SCRIPT_MODE="$OPTARG"
		echo "mode: $SCRIPT_MODE";;
    *)
      echo "Invalid flag -$OPTION"
      exit 1
  esac
done


# Download static-clang
DEFAULT_ARCH="$(uname -m)"
if [ "${STATIC_CLANG_ARCH:-}" == "" ]; then
	STATIC_CLANG_ARCH="${RUNNER_ARCH:-${DEFAULT_ARCH}}"
fi
case "${STATIC_CLANG_ARCH}" in
	ARM64|aarch64|arm64|arm64/*) GO_ARCH=arm64;;
	ARM|armv7l|armv8l|arm|arm/v7) GO_ARCH=arm;;  # assume arm/v7 for arm
	X64|x86_64|amd64|amd64/*) GO_ARCH=amd64;;
	X86|i686|386) GO_ARCH=386;;
	loongarch64) GO_ARCH=loong64;;
	ppc64le) GO_ARCH=ppc64le;;
	riscv64) GO_ARCH=riscv64;;
	s390x) GO_ARCH=s390x;;
	*) echo "No static-clang toolchain for ${CLANG_ARCH}">2; exit 1;;
esac

STATIC_CLANG_VERSION=latest  # or pin 22.1.8.0
if [ "${STATIC_CLANG_VERSION}" == "latest" ]; then
	STATIC_CLANG_BASEURL="https://github.com/mayeut/static-clang-images/releases/latest/download"
else
	STATIC_CLANG_BASEURL="https://github.com/mayeut/static-clang-images/releases/download/v${STATIC_CLANG_VERSION}"
fi

STATIC_CLANG_FILENAME="static-clang-linux-${GO_ARCH}.tar.xz"
STATIC_CLANG_URL="${STATIC_CLANG_BASEURL}/${STATIC_CLANG_FILENAME}"
SHASUMS_URL="${STATIC_CLANG_BASEURL}/sha256sums.txt"
SHASUMS_PATH="${STAGING_DIR}/${STATIC_CLANG_FILENAME}.sha256"
ATTEST_URL="${STATIC_CLANG_BASEURL}/attestation-bundle.json"
ATTEST_PATH="${STAGING_DIR}/attestation-bundle.json"

mkdir -p "$STAGING_DIR"
pushd "$STAGING_DIR"

if [[ "$SCRIPT_MODE" == "skip-download" ]]; then
	echo "skip-download mode"
else
    curl -fsSLO "$STATIC_CLANG_URL"
    curl -fsSL "$SHASUMS_URL" | grep "$STATIC_CLANG_FILENAME" > "$SHASUMS_PATH"
    sha256sum -c "$SHASUMS_PATH"
    curl -fsSLO "$ATTEST_URL"
    gh attestation verify "$STATIC_CLANG_FILENAME" -R "mayeut/static-clang-images" -b "$ATTEST_PATH"
    # or: sigstore verify github "$STATIC_CLANG_FILENAME" --repository "mayeut/static-clang-images" --bundle "$ATTEST_PATH"
fi

if [[ "$SCRIPT_MODE" == "download-only" ]]; then
echo "download-only mode"
rm "$ATTEST_PATH" "$SHASUMS_PATH"
exit 0
fi

TOOLCHAIN_PATH="/opt/clang"
tar -C /opt -xf "$STATIC_CLANG_FILENAME"
ln -s "${TOOLCHAIN_PATH}/bin/readelf" "${TOOLCHAIN_PATH}/bin/llvm-readelf"
popd

if [[ "$SCRIPT_MODE" == "install-only" ]]; then
echo "install-only mode"
exit 0
fi

# configure target triple
case "${AUDITWHEEL_POLICY}-${AUDITWHEEL_ARCH}" in
	manylinux*-armv7l) TARGET_TRIPLE=armv7-unknown-linux-gnueabihf;;
	musllinux*-armv7l) TARGET_TRIPLE=armv7-alpine-linux-musleabihf;;
	manylinux*-ppc64le) TARGET_TRIPLE=powerpc64le-unknown-linux-gnu;;
	musllinux*-ppc64le) TARGET_TRIPLE=powerpc64le-alpine-linux-musl;;
	manylinux*-*) TARGET_TRIPLE=${AUDITWHEEL_ARCH}-unknown-linux-gnu;;
	musllinux*-*) TARGET_TRIPLE=${AUDITWHEEL_ARCH}-alpine-linux-musl;;
esac
case "${AUDITWHEEL_POLICY}-${AUDITWHEEL_ARCH}" in
	*-riscv64) M_ARCH="-march=rv64gc";;
	*-x86_64) M_ARCH="-march=x86-64";;
	*-armv7l) M_ARCH="-march=armv7a";;
	manylinux*-i686) M_ARCH="-march=k8 -mtune=generic";;  # same as gcc manylinux2014 / manylinux_2_28
	musllinux*-i686) M_ARCH="-march=pentium-m -mtune=generic";;  # same as gcc musllinux_1_2
esac
GCC_TRIPLE=$(gcc -dumpmachine)

cat<<EOF >"${TOOLCHAIN_PATH}/bin/${AUDITWHEEL_PLAT}.cfg"
	-target ${TARGET_TRIPLE}
	${M_ARCH:-}
	--gcc-toolchain=${DEVTOOLSET_ROOTPATH:-}/usr
	--gcc-triple=${GCC_TRIPLE}
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang++.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

cat<<EOF >"${TOOLCHAIN_PATH}/bin/clang-cpp.cfg"
	@${AUDITWHEEL_PLAT}.cfg
EOF

# override entrypoint to add the toolchain to PATH
mv /usr/local/bin/manylinux-entrypoint /usr/local/bin/manylinux-entrypoint-org
cat<<EOF >/usr/local/bin/manylinux-entrypoint
#!/bin/bash

set -eu

export PATH="${TOOLCHAIN_PATH}/bin:\${PATH}"
exec /usr/local/bin/manylinux-entrypoint-org "\$@"
EOF

chmod +x /usr/local/bin/manylinux-entrypoint
