# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from base import ProjectDir, log  # local

_DEBIAN_CMD = "apt update && apt install --no-install-recommends -y python3 python3-pip python3-venv python3-pillow python3-numpy python3-pytest"
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


def _get_container(os_class, cpu):
    docker_cpu = DOCKER_CPU_MAP.get(cpu, cpu)
    platform_cpu = PLATFORM_CPU_MAP.get(cpu, cpu)
    docker_flags = ("--platform", f"linux/{platform_cpu}")
    if docker_cpu == "loong64":
        prefix = f"ghcr.io/"
    else:
        prefix = ""
    if os_class == "manylinux":
        which_debian = "bookworm" if docker_cpu == "mips64le" else "trixie"
        return f"{prefix}{docker_cpu}/debian:{which_debian}-slim", docker_flags, _DEBIAN_CMD, "bash"
    elif os_class == "musllinux":
        return f"{prefix}{docker_cpu}/alpine:3", docker_flags, _ALPINE_CMD, "sh"
    else:
        assert False, os_class

def run_process(argv, **kwargs):
    log(argv)
    return subprocess.run(argv, **kwargs)

def parse_args():
    parser = argparse.ArgumentParser(
        description = "Install and test pypdfium2 in docker container",
    )
    parser.add_argument("target")
    parser.add_argument(
        "-w", "--wheelfile",
        type = lambda p: Path(p).expanduser().resolve(),
    )
    return parser.parse_args(sys.argv[1:])

def main():
    
    args = parse_args()
    os_class, cpu = args.target.split("_", maxsplit=1)
    cpu = {"loongarch64": "loong64"}.get(cpu, cpu)
    
    container, docker_flags, prepare_cmd, shell = _get_container(os_class, cpu)
    log(f"{container}, {docker_flags}, {prepare_cmd}, {shell}")
    
    env = os.environ.copy()
    env["PREPARE_CMD"] = prepare_cmd
    container_wheel = str(Path("/pypdfium2") / args.wheelfile.relative_to(ProjectDir))
    run_process(["docker", "run", "--security-opt", "label=disable", "-e", "PREPARE_CMD", "-i", "--rm", "-v", f"{ProjectDir}:/pypdfium2", *docker_flags, container, shell, "/pypdfium2/utils/test_in_docker.sh", container_wheel], cwd=ProjectDir, env=env, check=True)

if __name__ == "__main__":
    main()
