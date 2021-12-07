#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0

# Attempt to build PDFium from source. This may take very long.

import os
import sys
import shutil
import subprocess
from os.path import (
    join,
    abspath,
    dirname,
    basename,
)


HomeDir       = os.path.expanduser('~')
SourceTree    = dirname(abspath(__file__))
WorkDir       = join(SourceTree,'sourcebuild')
PatchDir      = join(WorkDir,'patches')
DepotToolsDir = join(WorkDir,'depot_tools')
PDFiumDir     = join(WorkDir,'pdfium')
BuildDir      = join(PDFiumDir,'out')
TargetDir     = join(SourceTree,'data','sourcebuild')

DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium.git"

GClient = join(DepotToolsDir,'gclient')
GN      = join(DepotToolsDir,'gn')
Ninja   = join(DepotToolsDir,'ninja')

Configuration = """\
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


def dl_depottools():
    
    if not os.path.isdir(WorkDir):
        os.mkdir(WorkDir)
    
    cmd = f"git clone --depth 1 {DepotTools_URL}"
    print(cmd)
    subprocess.run(cmd, shell=True, cwd=WorkDir)
    
    if sys.platform.startswith('win32'):
        os.environ['PATH'] += f";{DepotToolsDir}"
    else:
        os.environ['PATH'] += f":{DepotToolsDir}"


def dl_pdfium():
    
    config_cmd = f"{GClient} config --unmanaged {PDFium_URL}"
    print(config_cmd)
    subprocess.run(config_cmd, shell=True, cwd=WorkDir)
    
    sync_cmd = f"{GClient} sync --no-history --shallow"
    print(sync_cmd)
    subprocess.run(sync_cmd, shell=True, cwd=WorkDir)


def _apply_patchset(patchset, cwd):
    for patch in patchset:
        cmd = f"git apply -v {patch}"
        print(cmd)
        subprocess.run(cmd, shell=True, cwd=cwd)

def patch_depottools():
    _apply_patchset(DepotPatches, DepotToolsDir)

def patch_pdfium():
    _apply_patchset(PdfiumPatches, PDFiumDir)
    shutil.copy(join(PatchDir,'resources.rc'), join(PDFiumDir,'resources.rc'))


def configure():
    
    if not os.path.exists(BuildDir):
        os.mkdir(BuildDir)
    
    with open(join(BuildDir,'args.gn'), 'w') as args_handle:
        args_handle.write(Configuration)
    
    gen_cmd = f"{GN} gen {BuildDir}"
    print(gen_cmd)
    subprocess.run(gen_cmd, shell=True, cwd=PDFiumDir)


def build():
    build_cmd = f"{Ninja} -C {BuildDir} pdfium"
    print(build_cmd)
    subprocess.run(build_cmd, shell=True, cwd=PDFiumDir)


def find_lib():
    
    lib = None
    
    for lname in Libnames:
        path = join(BuildDir,lname)
        if os.path.isfile(path):
            lib = path
    
    if lib is None:
        raise RuntimeError("Build artifact not found.")
    
    return lib


def pack(src_libpath):
    
    if not os.path.isdir(TargetDir):
        os.mkdir(TargetDir)
    
    # assumption: filename is ctypesgen-recognisable
    # we could also rename according to the host platform ...
    target_libpath = join(TargetDir, basename(src_libpath))
    shutil.copy(src_libpath, target_libpath)
    
    src_headers = join(PDFiumDir,'public')
    target_headers = join(TargetDir,'include')
    shutil.copytree(src_headers, target_headers)
    
    header_files = join(TargetDir,'include','*.h')
    bindings_file = join(TargetDir,'_pypdfium.py')
    
    ctypesgen_cmd = f"ctypesgen --library pdfium --strip-build-path {TargetDir} -L . {header_files} -o {bindings_file}"
    subprocess.run(
        ctypesgen_cmd,
        stdout = subprocess.PIPE,
        cwd    = TargetDir,
        shell  = True,
    )


def main():
    
    dl_depottools()
    patch_depottools()
    dl_pdfium()
    patch_pdfium()
    
    configure()
    build()
    
    libpath = find_lib()
    pack(libpath)
    
    return basename(libpath)


if __name__ == '__main__':
    main()
