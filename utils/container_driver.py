# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import ProjectDir, log  # local

_RHEL_CMD   = "yum install -y python3 python3-virtualenv python3-pillow python3-numpy"  # python3-pytest
_DEBIAN_CMD = "apt-get update && apt-get install --no-install-recommends -y python3 python3-pip python3-venv python3-pillow python3-numpy python3-pytest"
_ALPINE_CMD = "apk add python3 py3-pip py3-pillow py3-numpy py3-pytest"

# Map uname-style machine name to docker container arch name
# Check the respective docker hub pages for a list of platforms (e.g. https://hub.docker.com/_/debian#quick-reference-cont)
DOCKER_CPU_MAP = {
    "x86_64":  "amd64",
    "i686":    "i386",
    "aarch64": "arm64v8",
    "armv7l":  "arm32v7",
}

# Map uname-style machine name to binfmt handler name.
# Check tonistiigi/binfmt for a canonical list (also seen in setup-qemu-action output).
PLATFORM_CPU_MAP = {
    "x86_64":  "amd64",
    "i686":    "386",
    "aarch64": "arm64",
    "armv7l":  "arm/v7",
}

# The following platform names match across conventions, so they do not need to be explicitly handled above:
# loong64, mips64le, ppc64le, riscv64, s390x


def _get_container(image, os_class, cibw_cpu):
    docker_cpu = DOCKER_CPU_MAP.get(cibw_cpu, cibw_cpu)
    prefix = f"ghcr.io/" if docker_cpu == "loong64" else ""
    if image == "debian":
        assert os_class == "manylinux"
        which_debian = "bookworm" if docker_cpu == "mips64le" else "trixie"
        return f"{prefix}{docker_cpu}/debian:{which_debian}-slim", _DEBIAN_CMD, "bash"
    elif image == "manylinux2014":
        assert os_class == "manylinux"
        return f"quay.io/pypa/manylinux2014_{cibw_cpu}", _RHEL_CMD, "bash"
    elif image == "alpine":
        assert os_class == "musllinux"
        return f"{prefix}{docker_cpu}/alpine:3", _ALPINE_CMD, "sh"
    else:
        assert False, os_class


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Install and test pypdfium2 in docker container",
    )
    parser.add_argument("target")
    parser.add_argument("--image")
    parser.add_argument(
        "-w", "--wheel-path",
        type = lambda p: Path("/pypdfium2") / p,
    )
    args = parser.parse_args(sys.argv[1:])
    return args


SCRIPT_TEMPLATE = """\
set -exuo pipefail

%(install_pkgs)s
VENV_DIR="/testenv"
python3 -m venv "$VENV_DIR" --system-site-packages
export PATH="$VENV_DIR/bin:$PATH"
which python3; python3 --version
python3 -m pip install -U pip
cd /pypdfium2
%(install_lib)s
pypdfium2
python3 -m pytest tests/
"""

INSTALL_WHEEL = """
python3 -m pip install "$1"
"""
INSTALL_WHEEL_BYFORCE = """
python3 -m pip install -U wheel
bash "/pypdfium2/utils/enforce_install.sh" "$1"
"""
INSTALL_FROM_SRC = """
python3 -m pip install -U setuptools packaging wheel build pytest
python3 -m pip install --no-build-isolation -v .
"""

def main():
    
    args = parse_args()
    if args.target == "manylinux_i686" and bool(os.getenv("GITHUB_ACTIONS")):
        print("Debian i686 container has network problems on GHA. Skipping.", file=sys.stderr)
        return
    
    os_class, cibw_cpu = args.target.split("_", maxsplit=1)
    cibw_cpu = {"loongarch64": "loong64"}.get(cibw_cpu, cibw_cpu)
    platform_cpu = PLATFORM_CPU_MAP.get(cibw_cpu, cibw_cpu)
    docker_flags = ("--platform", f"linux/{platform_cpu}")
    if not args.image:
        args.image = {"manylinux": "debian", "musllinux": "alpine"}[os_class]
    
    container, install_pkgs, shell = _get_container(args.image, os_class, cibw_cpu)
    if args.wheel_path:
        # https://github.com/pypa/pip/issues/14095
        install_lib = INSTALL_WHEEL if not cibw_cpu.startswith("mips") else INSTALL_WHEEL_BYFORCE
    else:
        install_lib = INSTALL_FROM_SRC
    
    script = SCRIPT_TEMPLATE % dict(install_pkgs=install_pkgs, install_lib=install_lib.strip())
    docker_cmd = ["docker", "run", "--security-opt", "label=disable", "-i", "--rm", "-v", f"{ProjectDir}:/pypdfium2", *docker_flags, container, shell]
    if args.wheel_path:
        docker_cmd += ["--", args.wheel_path]
    
    log(docker_cmd)
    log(script)
    subprocess.run(docker_cmd, input=script.encode(), cwd=ProjectDir, check=True)


if __name__ == "__main__":
    main()
