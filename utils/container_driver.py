# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import re
import sys
import argparse
import subprocess
from pathlib import Path
from collections import namedtuple

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from shared_base import ProjectDir, log, get_cool_date  # local

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

ImageCmdMap = {
    "debian": ("bash", "apt-get update && apt-get install --no-install-recommends -y python3 python3-pip python3-venv python3-pillow python3-numpy python3-pytest"),
    "manylinux2014": ("bash", "yum install -y python3 && yum install -y python3-pillow python3-numpy python3-pytest || true"),
    "alpine": ("sh", "apk add python3 py3-pip py3-pillow py3-numpy py3-pytest"),
}
ValidImagesMap = {"manylinux": ("debian", "manylinux2014"), "musllinux": ("alpine", )}
MountPoint = "/projects/pypdfium2"
ImageInfo = namedtuple("ImageInfo", ("name", "version"))
ScriptFields = namedtuple("ScriptFields", ("sys_install", "pip_install", "lib_install"))


def infer_target(target, artifact):
    if not artifact or artifact.endswith(".tar.gz"):
        assert target, "With source installation, a --target must be given, e.g. manylinux_x86_64"
    elif artifact.endswith(".whl"):
        inferred = "%s_%s" % re.search(r"(\w+linux)_[\d_]+_(\w+)\.", artifact).groups()
        if target:
            assert target == inferred, f"Given vs. inferred target mismatch: {target!r} != {inferred!r}"
        else:
            log(f"Inferred target {inferred!r}")
            target = inferred
    else:
        assert False, f"Invalid artifact (neither sdist nor wheel): {artifact!r}"
    return target


def get_image(image, cibw_os, docker_cpu):
    
    if not image:
        image = {"manylinux": "debian", "musllinux": "alpine"}[cibw_os]
    image, *version = image.split(":", maxsplit=1)
    assert image in ValidImagesMap[cibw_os]
    
    if not version:
        version = {
            "debian": ("bookworm-slim" if docker_cpu == "mips64le" else "trixie-slim"),
            "manylinux2014": None,
            "alpine": '3',
        }[image]
    else:
        version, = version
    
    return ImageInfo(image, version)


# IMPORTANT: The container's venv *must not* be managed in the mounted directory, since it should never end up on the host. In particular, don't use the usual //.venv, as that would conflict with the host's venv.
SCRIPT_TEMPLATE = f"""\
set -exuo pipefail

%(sys_install)s
VENV_DIR="/projects/testenv"
python3 -m venv "$VENV_DIR" --system-site-packages
export PATH="$VENV_DIR/bin:$PATH"
which python3; python3 --version
cd {MountPoint}
python3 utils/update_pip.py
export PIP_UPLOADED_PRIOR_TO="{get_cool_date(7)}"
%(pip_install)s
%(lib_install)s
pypdfium2 --version
python3 -m pytest tests/
"""

def write_script(args, cibw_cpu, sys_install, image):
    pip_packages = []
    if args.update_with_pip:
        pip_packages.extend(args.update_with_pip)
    
    if args.artifact:
        if cibw_cpu.startswith("mips") and args.artifact.endswith(".whl"):
            pip_packages.append("wheel")
            lib_install = './utils/misc/enforce_install.sh "$1"'
        else:
            # TODO for sdist: add an option to set PDFIUM_BINDINGS=reference
            lib_install = 'pip install -v "$1"'
    else:
        pip_packages += ("setuptools", "packaging", "wheel", "build")
        lib_install = 'pip install --no-build-isolation -v .'
    
    pip_install = ('pip install -U ' + " ".join(pip_packages)) if pip_packages else ""
    return SCRIPT_TEMPLATE % ScriptFields(sys_install, pip_install, lib_install)._asdict()


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Install and test pypdfium2 in a docker container",
    )
    parser.add_argument(
        "-a", "--artifact",
        help = "The artifact (wheel or sdist) to install. Optional. If not given, pypdfium2 will be installed from the mounted repository directly, rather than from a packaged distribution."
    )
    parser.add_argument(
        "-t", "--target",
        help = "The target platform, in CIBW/wheeltag-like notation. Required if installing from source. Optional if a wheel artifact is given, where the target will be inferred from the wheel filename, with this option just used for validation."
    )
    parser.add_argument(
        "-i", "--image",
        help = "The container image to use. Supported images are: (manylinux) debian, manylinux2014. (musllinux) alpine. Optionally, a colon-separated version specifier can be added, e.g. debian:bookworm-slim or alpine:3. If not given, a default version will be used."
    )
    parser.add_argument(
        "-u", "--update-with-pip",
        nargs="+",
        help = "Packages to install/update with pip. E.g. with manylinux2014 or debian:bullseye, getting pytest from PyPI is recommended, as these containers' system packages of pytest are known to be incompatible with pypdfium2. With x86_64 or aarch64, it is also possible (and sometimes necessary) to install pillow and numpy from PyPI."
    )
    args = parser.parse_args(sys.argv[1:])
    args.target = infer_target(args.target, args.artifact)
    return args


def main():
    
    args = parse_args()
    cibw_os, cibw_cpu = args.target.split("_", maxsplit=1)
    cibw_cpu = {"loongarch64": "loong64"}.get(cibw_cpu, cibw_cpu)
    docker_cpu = DOCKER_CPU_MAP.get(cibw_cpu, cibw_cpu)
    platform_cpu = PLATFORM_CPU_MAP.get(cibw_cpu, cibw_cpu)
    
    image = get_image(args.image, cibw_os, docker_cpu)
    shell, sys_install = ImageCmdMap[image.name]
    if image.name == "manylinux2014":
        image_prefix = "quay.io/pypa/"
        container = f"{image_prefix}{image.name}_{cibw_cpu}"
    else:
        image_prefix = "ghcr.io/" if docker_cpu == "loong64" else ""
        container = f"{image_prefix}{docker_cpu}/{image.name}:{image.version}"
    script = write_script(args, cibw_cpu, sys_install, image)
    
    docker_flags = ("--platform", f"linux/{platform_cpu}")
    docker_cmd = ["docker", "run", "-i", "--rm", "--volume", f"{ProjectDir}:{MountPoint}", "--security-opt", "label=disable", *docker_flags, container, shell, "-s"]
    if args.artifact:
        assert Path(args.artifact).exists(), "Given artifact path does not actually exist"
        wheel_path = str(Path(MountPoint)/args.artifact)
        docker_cmd += ["--", wheel_path]
    
    log(docker_cmd)
    log(script)
    subprocess.run(docker_cmd, input=script.encode(), cwd=ProjectDir, check=True)


if __name__ == "__main__":
    main()
