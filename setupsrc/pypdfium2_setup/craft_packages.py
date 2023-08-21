# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import os
import sys
import shutil
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))
# CONSIDER glob import or dotted access
from pypdfium2_setup.packaging_base import (
    run_cmd,
    clean_platfiles,
    get_latest_version,
    Host,
    ModuleDir,
    BindingsFileName,
    LibnameForSystem,
    SourceTree,
    BinarySpec_EnvVar,
    BinarySpec_V8Indicator,
    BinarySpec_VersionSep,
    PlatformTarget_None,
    ReleaseNames,
    VerNamespace,
    CondaNames,
    CondaDir,
    CondaOutDir,
)


class ArtifactStash:
    
    # Preserve in-tree aftefacts from editable install
    
    def __init__(self):
        
        self.tmpdir = None
        
        # FIXME some degree of duplication with base::get_platfiles()
        file_names = [BindingsFileName, LibnameForSystem[Host.system]]
        self.files = [fp for fp in [ModuleDir / fn for fn in file_names] if fp.exists()]
        if len(self.files) == 0:
            return
        elif len(self.files) != 2:
            print(f"Warning: Expected exactly 2 platform files, but found {len(self.files)}.", file=sys.stderr)
        
        self.tmpdir = tempfile.TemporaryDirectory(prefix="pypdfium2_artifact_stash_")
        self.tmpdir_path = Path(self.tmpdir.name)
        for fp in self.files:
            shutil.move(fp, self.tmpdir_path)
    
    def pop(self):
        if self.tmpdir is None:
            return
        for fp in self.files:
            shutil.move(self.tmpdir_path / fp.name, ModuleDir)
        self.tmpdir.cleanup()


def run_pypi_build(args):
    run_cmd([sys.executable, "-m", "build", "--skip-dependency-check", "--no-isolation"] + args, cwd=SourceTree, env=os.environ)


def run_conda_build(binary):
    os.environ[BinarySpec_EnvVar] = binary
    run_cmd(["conda", "build", CondaDir, "--output-folder", CondaOutDir, "--variants", "{python: [3.8, 3.9, 3.10, 3.11]}"], cwd=SourceTree, env=os.environ)


def main():
    
    parser = argparse.ArgumentParser(
        description = "Craft PyPI or conda packages for pypdfium2.",
    )
    parser.add_argument(
        "--conda",
        dest = "pypi",
        action = "store_false",
        help = "If given, build for conda instead of PyPI."
    )
    parser.add_argument(
        "--use-v8",
        action = "store_true",
    )
    parser.add_argument(
        "--version",
        type = int,
        default = None,
    )
    args = parser.parse_args()
    if not args.version:
        args.version = get_latest_version()
    
    stash = ArtifactStash()
    suffix = (BinarySpec_V8Indicator if args.use_v8 else "") + BinarySpec_VersionSep + str(args.version)
    
    if args.pypi:
        
        os.environ[BinarySpec_EnvVar] = PlatformTarget_None
        run_pypi_build(["--sdist"])
        clean_platfiles()
        
        for plat in ReleaseNames.keys():
            os.environ[BinarySpec_EnvVar] = plat + suffix
            run_pypi_build(["--wheel"])
            clean_platfiles()
        
    else:
        
        version = VerNamespace["V_PYPDFIUM2"]
        os.environ["VERSION"] = version
        
        platforms = CondaNames.copy()
        conda_host = platforms.pop(Host.platform)
        host_files = None
        
        for plat, conda_plat in platforms.items():
            
            run_conda_build(plat + suffix)
            
            if host_files is None:
                host_files = list((CondaOutDir / conda_host).glob(f"pypdfium2-{version}-*.tar.bz2"))
            for hf in host_files:
                run_cmd(["conda", "convert", hf, "-p", conda_plat, "-o", CondaOutDir], cwd=SourceTree, env=os.environ)
                hf.unlink()
        
        run_conda_build(Host.platform + suffix)
    
    stash.pop()


if __name__ == '__main__':
    main()
