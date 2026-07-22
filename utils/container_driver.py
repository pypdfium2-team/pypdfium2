# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
import subprocess
from pathlib import Path
from collections import namedtuple

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import ProjectDir, log  # local

_RHEL_CMD   = "yum install -y python3 python3-pillow python3-numpy"  # python3-pytest
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


def _get_container(image, cibw_os, cibw_cpu, docker_cpu):
    prefix = f"ghcr.io/" if docker_cpu == "loong64" else ""
    if image == "debian":
        assert cibw_os == "manylinux"
        which_debian = "bookworm" if docker_cpu == "mips64le" else "trixie"
        return f"{prefix}{docker_cpu}/debian:{which_debian}-slim", "bash", _DEBIAN_CMD
    elif image == "manylinux2014":
        # manylinux2014 is useful to test both python 3.6 and glibc 2.17 compatibility in one go
        assert cibw_os == "manylinux"
        return f"quay.io/pypa/manylinux2014_{cibw_cpu}", "bash", _RHEL_CMD
    elif image == "alpine":
        assert cibw_os == "musllinux"
        return f"{prefix}{docker_cpu}/alpine:3", "sh", _ALPINE_CMD
    else:
        assert False, cibw_os


MountPoint = "/projects/pypdfium2"
ScriptFields = namedtuple("ScriptFields", ("sys_install", "pip_install", "lib_install"))

SCRIPT_TEMPLATE = """\
set -exuo pipefail

%(sys_install)s
VENV_DIR="/projects/testenv"
python3 -m venv "$VENV_DIR" --system-site-packages
export PATH="$VENV_DIR/bin:$PATH"
which python3; python3 --version
python3 -m pip install -U pip
%(pip_install)s
cd /projects/pypdfium2
%(lib_install)s
pypdfium2
python3 -m pytest tests/
"""

def write_script(args, cibw_cpu, sys_install):
    pip_packages = []
    if args.wheel_path:
        if cibw_cpu.startswith("mips"):
            pip_packages.append("wheel")
            lib_install = f'bash "{MountPoint}/utils/enforce_install.sh" "$1"'
        else:
            lib_install = 'pip install "$1"'
        if args.image == "manylinux2014":
            pip_packages.append("pytest")
    else:
        pip_packages += ("setuptools", "packaging", "wheel", "build", "pytest")
        lib_install = 'pip install --no-build-isolation -v .'
    
    pip_install = ('pip install ' + " ".join(pip_packages)) if pip_packages else ""
    return SCRIPT_TEMPLATE % ScriptFields(sys_install, pip_install, lib_install)._asdict()


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Install and test pypdfium2 in docker container",
    )
    parser.add_argument("target")
    parser.add_argument("--image")
    parser.add_argument("-w", "--wheel-path")
    args = parser.parse_args(sys.argv[1:])
    return args


def main():
    
    args = parse_args()
    if args.target == "manylinux_i686" and bool(os.getenv("GITHUB_ACTIONS")):
        print("Debian i686 container has network problems on GHA. Skipping.", file=sys.stderr)
        return
    
    cibw_os, cibw_cpu = args.target.split("_", maxsplit=1)
    cibw_cpu = {"loongarch64": "loong64"}.get(cibw_cpu, cibw_cpu)
    if not args.image:
        args.image = {"manylinux": "debian", "musllinux": "alpine"}[cibw_os]
    
    docker_cpu = DOCKER_CPU_MAP.get(cibw_cpu, cibw_cpu)
    platform_cpu = PLATFORM_CPU_MAP.get(cibw_cpu, cibw_cpu)
    
    container, shell, sys_install = _get_container(args.image, cibw_os, cibw_cpu, docker_cpu)
    script = write_script(args, cibw_cpu, sys_install)
    
    docker_flags = ("--platform", f"linux/{platform_cpu}")
    docker_cmd = ["docker", "run", "-i", "--rm", "--volume", f"{ProjectDir}:{MountPoint}", "--security-opt", "label=disable", *docker_flags, container, shell, "-s"]
    if args.wheel_path:
        wheel_path = str(Path(MountPoint)/args.wheel_path)
        docker_cmd += ["--", wheel_path]
    
    log(docker_cmd)
    log(script)
    subprocess.run(docker_cmd, input=script.encode(), cwd=ProjectDir, check=True)


if __name__ == "__main__":
    main()
