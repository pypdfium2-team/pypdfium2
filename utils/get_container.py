# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys

_DEBIAN_CMD = "apt update && apt install --no-install-recommends -y python3 python3-pip python3-venv python3-pillow python3-numpy python3-pytest"
_ALPINE_CMD = "apk add python3 py3-pip py3-pillow py3-numpy py3-pytest"

DOCKER_CPU_MAP = {
    "x86_64": "amd64",
    "aarch64": "arm64v8",
    "armv7l": "arm32v7",
    "i686": "i386",
    "loongarch64": "loong64",
}  # ppc64le, riscv64, s390x equal

def _get_container(os_class, cpu):
    prefix = DOCKER_CPU_MAP.get(cpu, cpu)
    if cpu == "loongarch64":
        prefix = f"ghcr.io/{prefix}"
    if os_class == "manylinux":
        return f"{prefix}/debian:trixie-slim", _DEBIAN_CMD, "bash"
    elif os_class == "musllinux":
        return f"{prefix}/alpine:3", _ALPINE_CMD, "sh"
    else:
        assert False, os_class

os_class, cpu = sys.argv[1].split("_", maxsplit=1)
container, prepare_cmd, shell = _get_container(os_class, cpu)
print(f'export CONTAINER="{container}"')
print(f'export PREPARE_CMD="{prepare_cmd}"')
print(f'export INIT_SHELL="{shell}"')
