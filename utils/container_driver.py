# SPDX-FileCopyrightText: 2026 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import argparse
import subprocess
from pathlib import Path
from collections import namedtuple

sys.path.insert(0, str(Path(__file__).parents[1]/"setupsrc"))
from simplebase import ProjectDir, log, get_cool_date  # local

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

# Note: With manylinux2014 or debian bullseye, you should pass --update-with-pip pytest.
# manylinux2014's pytest causes a lot of erroneous test failures because it lacks APIs etc., whereas debian bullseye's pytest fails right on startup at parsing our pyproject.toml.
ImageCmdMap = {
    "debian": ("bash", "apt-get update && apt-get install --no-install-recommends -y python3 python3-pip python3-venv python3-pillow python3-numpy python3-pytest"),
    "manylinux2014": ("bash", "yum install -y python3 && yum install -y python3-pillow python3-numpy python3-pytest || true"),
    "alpine": ("sh", "apk add python3 py3-pip py3-pillow py3-numpy py3-pytest"),
}
ValidImagesMap = {"manylinux": ("debian", "manylinux2014"), "musllinux": ("alpine", )}
MountPoint = "/projects/pypdfium2"
ImageInfo = namedtuple("ImageInfo", ("name", "version"))
ScriptFields = namedtuple("ScriptFields", ("sys_install", "pip_install", "lib_install"))


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
python3 utils/update_pip_cool.py
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
    
    if args.wheel_path:
        if cibw_cpu.startswith("mips"):
            pip_packages.append("wheel")
            lib_install = f'bash "{MountPoint}/utils/enforce_install.sh" "$1"'
        else:
            lib_install = 'pip install "$1"'
    else:
        pip_packages += ("setuptools", "packaging", "wheel", "build")
        lib_install = 'pip install --no-build-isolation -v .'
    
    if image.name == "debian" and image.version in ("buster", "buster-slim"):
        sys_install = """\
sed -i.bak "s|deb.debian.org|archive.debian.org|g" /etc/apt/sources.list
""" + sys_install
    
    pip_install = ('pip install -U ' + " ".join(pip_packages)) if pip_packages else ""
    return SCRIPT_TEMPLATE % ScriptFields(sys_install, pip_install, lib_install)._asdict()


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Install and test pypdfium2 in docker container",
    )
    parser.add_argument("target")
    parser.add_argument("--image")
    parser.add_argument("-w", "--wheel-path")
    parser.add_argument("-u", "--update-with-pip", nargs="+")
    args = parser.parse_args(sys.argv[1:])
    return args


def main():
    
    args = parse_args()
    if args.target == "manylinux_i686" and bool(os.getenv("GITHUB_ACTIONS")):
        print("Debian i686 container has network problems on GHA. Skipping.", file=sys.stderr)
        return
    
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
    if args.wheel_path:
        wheel_path = str(Path(MountPoint)/args.wheel_path)
        docker_cmd += ["--", wheel_path]
    
    log(docker_cmd)
    log(script)
    subprocess.run(docker_cmd, input=script.encode(), cwd=ProjectDir, check=True)


if __name__ == "__main__":
    main()
