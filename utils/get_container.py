# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import sys

_UBUNTU_INST = "apt install -y python3 python3-pillow python3-numpy"
_RHEL_INST   = "dnf in -y python3 python3-pillow python3-numpy"
_ALPINE_INST = "pkg add --update python3 py3-pip py3-pillow py3-numpy"

def _get_container(os_class, cpu):
    if os_class == "manylinux":
        # https://github.com/pypa/manylinux
        if cpu == "riscv64":
            return "quay.io/pypa/manylinux_2_39", _UBUNTU_INST
        elif cpu == "armv7l":
            return "quay.io/pypa/manylinux_2_35", _UBUNTU_INST
        elif cpu == "loongarch64":
            return "ghcr.io/loong64/manylinux_2_38", _RHEL_INST
        else:
            return "quay.io/pypa/manylinux_2_34", _RHEL_INST
    elif os_class == "musllinux":
        if cpu == "loongarch64":
            return "ghcr.io/loong64/musllinux_1_2", _ALPINE_INST
        else:
            return "quay.io/pypa/musllinux_1_2", _ALPINE_INST
    else:
        assert False, os_class

os_class, cpu = sys.argv[1].split("_", maxsplit=1)
container_prefix, deps = _get_container(os_class, cpu)
container = f"{container_prefix}_{cpu}"
print(f'export CONTAINER={container!r}')
print(f'export INSTALL_DEPS={deps!r}')
