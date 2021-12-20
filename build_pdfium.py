#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Attempt to build PDFium from source. This may take very long.
# Last confirmed to work on 2021-12-13

import os
import sys
import shutil
import argparse
import subprocess
from os.path import (
    join,
    abspath,
    dirname,
    basename,
)
from update import postprocess_bindings


HomeDir       = os.path.expanduser('~')
SourceTree    = dirname(abspath(__file__))
WorkDir       = join(SourceTree,'sourcebuild')
PatchDir      = join(WorkDir,'patches')
DepotToolsDir = join(WorkDir,'depot_tools')
PDFiumDir     = join(WorkDir,'pdfium')
BuildDir      = join(PDFiumDir,'out')
OutputDir     = join(SourceTree,'data','sourcebuild')

DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium.git"

DefaultConfig = """\
is_debug = false
pdf_is_standalone = true
pdf_enable_v8 = false
pdf_enable_xfa = false
use_custom_libcxx = true\
"""

Libnames = [
    'pdfium.so',
    'libpdfium.so',
    'pdfium.dylib',
    'libpdfium.dylib',
    'pdfium.dll',
    'libpdfium.dll',
    'libpdfium',
    'pdfium',
]

PdfiumPatches = [
    join(PatchDir,'public_headers.patch'),
    join(PatchDir,'rc_compiler.patch'),
    join(PatchDir,'shared_library.patch'),
    join(PatchDir,'widestring.patch'),
]

DepotPatches = [
    join(PatchDir,'gclient_scm.patch'),
]


GClient = join(DepotToolsDir,'gclient')
GN      = join(DepotToolsDir,'gn')
Ninja   = join(DepotToolsDir,'ninja')


# prefer system-provided build tools if available, because depot-tools
# do not ship binaries for non-standard architectures

_sh_gn = shutil.which('gn')
_sh_ninja = shutil.which('ninja')

if _sh_gn:
    GN = _sh_gn
if _sh_ninja:
    Ninja = _sh_ninja


def run_cmd(command, cwd):
    print(command)
    subprocess.run(command, cwd=cwd, shell=True)


def dl_depottools(do_sync):
    
    if not os.path.isdir(WorkDir):
        os.mkdir(WorkDir)
    
    is_update = True
    
    if os.path.isdir(DepotToolsDir):
        if do_sync:
            print("DepotTools: Revert and update ...")
            run_cmd(f"git reset --hard HEAD", cwd=DepotToolsDir)
            run_cmd(f"git pull {DepotTools_URL}", cwd=DepotToolsDir)
        else:
            print("DepotTools: Using existing repository as-is.")
            is_update = False
    else:
        print("DepotTools: Download ...")
        run_cmd(f"git clone --depth 1 {DepotTools_URL} {DepotToolsDir}", cwd=WorkDir)
    
    if sys.platform.startswith('win32'):
        os.environ['PATH'] += f";{DepotToolsDir}"
    else:
        os.environ['PATH'] += f":{DepotToolsDir}"
    
    return is_update


def dl_pdfium(do_sync):
    
    is_update = True
    
    if os.path.isdir(PDFiumDir):
        if do_sync:
            print("PDFium: Revert / Sync  ...")
            run_cmd(f"{GClient} revert", cwd=WorkDir)
        else:
            print("PDFium: Using existing repository as-is.")
            is_update = False
    else:
        print("PDFium: Download ...")
        run_cmd(f"{GClient} config --unmanaged {PDFium_URL}", cwd=WorkDir)
        run_cmd(f"{GClient} sync --no-history --shallow", cwd=WorkDir)
    
    return is_update
    

def _apply_patchset(patchset, cwd):
    for patch in patchset:
        run_cmd(f"git apply -v {patch}", cwd=cwd)

def patch_depottools():
    _apply_patchset(DepotPatches, DepotToolsDir)

def patch_pdfium():
    _apply_patchset(PdfiumPatches, PDFiumDir)
    shutil.copy(join(PatchDir,'resources.rc'), join(PDFiumDir,'resources.rc'))


def configure(config):
    
    if not os.path.exists(BuildDir):
        os.mkdir(BuildDir)
    
    with open(join(BuildDir,'args.gn'), 'w') as args_handle:
        args_handle.write(config)
    
    run_cmd(f"{GN} gen {BuildDir}", cwd=PDFiumDir)


def build():
    run_cmd(f"{Ninja} -C {BuildDir} pdfium", cwd=PDFiumDir)


def find_lib(srcname=None, directory=BuildDir):
    
    if srcname is not None:
        path = join(BuildDir, srcname)
        if os.path.isfile(path):
            return path
        else:
            print("Warning: The file of given srcname does not exist.", file=sys.stderr)
    
    libpath = None
    
    for lname in Libnames:
        path = join(directory, lname)
        if os.path.isfile(path):
            libpath = path
    
    if libpath is None:
        raise RuntimeError("Build artifact not found.")
    
    return libpath


def pack(src_libpath, destname=None):
    
    if os.path.isdir(OutputDir):
        if len(os.listdir(OutputDir)) > 0:
            shutil.rmtree(OutputDir)
            os.mkdir(OutputDir)
    else:
        os.mkdir(OutputDir)
    
    if destname is None:
        destname = basename(src_libpath)
    
    destpath = join(OutputDir, destname)
    shutil.copy(src_libpath, destpath)
    
    src_headers = join(PDFiumDir,'public')
    target_headers = join(OutputDir,'include')
    
    shutil.copytree(src_headers, target_headers)
    
    include_dir = join(OutputDir,'include')
    header_files = join(include_dir,'*.h')
    bindings_file = join(OutputDir,'_pypdfium.py')
    
    ctypesgen_cmd = f"ctypesgen --library pdfium --strip-build-path {OutputDir} -L . {header_files} -o {bindings_file}"
    subprocess.run(
        ctypesgen_cmd,
        stdout = subprocess.PIPE,
        cwd    = OutputDir,
        shell  = True,
    )
    
    postprocess_bindings(bindings_file, OutputDir)
    shutil.rmtree(include_dir)


def parse_args():
    parser = argparse.ArgumentParser(
        description = "A script to automate building PDFium from source and generating ctypesgen bindings."
    )
    parser.add_argument(
        '--argfile', '-a',
        help = "A file containing custom PDFium build configuration, to be evaluated by `gn gen`.",
    )
    parser.add_argument(
        '--srcname', '-s',
        help = "File name of the generated PDFium binary.",
    )
    parser.add_argument(
        '--destname', '-d',
        help = "Rename the binary to a different file name.",
    )
    parser.add_argument(
        '--update', '-u',
        action = 'store_true',
        help = "Update existing repositories, removing local changes.",
    )
    return parser.parse_args()


def main(args):
    
    if args.argfile is None:
        config = DefaultConfig
    else:
        with open(abspath(args.argfile), 'r') as file_handle:
            config = file_handle.read()
    
    depot_dl_done = dl_depottools(args.update)
    if depot_dl_done:
        patch_depottools()
    
    pdfium_dl_done = dl_pdfium(args.update)
    if pdfium_dl_done:
        patch_pdfium()
    
    configure(config)
    build()
    
    libpath = find_lib(args.srcname)
    pack(libpath, args.destname)


if __name__ == '__main__':
    main(parse_args())
