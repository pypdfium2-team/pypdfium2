#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Attempt to build PDFium from source. This may take very long.

import os
import sys
import shutil
import argparse
import importlib.util
from os.path import join


if __name__ == '__main__': sys.modules['platform_setup'] = importlib.util.module_from_spec( importlib.util.spec_from_file_location('platform_setup', os.path.join(os.path.dirname(os.path.abspath(__file__)), '__init__.py')) )

from platform_setup import check_deps
from platform_setup.packaging_base import (
    SB_Dir,
    Libnames,
    DataTree,
    PlatformNames,
    run_cmd,
    call_ctypesgen,
)


PatchDir       = join(SB_Dir,'patches')
DepotToolsDir  = join(SB_Dir,'depot_tools')
PDFiumDir      = join(SB_Dir,'pdfium')
PDFiumBuildDir = join(PDFiumDir,'out','Default')
OutputDir      = join(DataTree, PlatformNames.sourcebuild)
NB_BinaryDir   = join(PDFiumDir,'third_party','llvm-build','Release+Asserts','bin')

DepotTools_URL = "https://chromium.googlesource.com/chromium/tools/depot_tools.git"
PDFium_URL     = "https://pdfium.googlesource.com/pdfium.git"

DepotPatches = [
    (join(PatchDir,'depottools','gclient_scm.patch'), DepotToolsDir),
]
PdfiumMainPatches = [
    (join(PatchDir,'pdfium','public_headers.patch'), PDFiumDir),
    (join(PatchDir,'pdfium','shared_library.patch'), PDFiumDir),
]
PdfiumWinPatches = [
    (join(PatchDir,'pdfium','win','pdfium.patch'), PDFiumDir),
    (join(PatchDir,'pdfium','win','build.patch'), join(PDFiumDir,'build')),
]
PdfiumNativebuildPatches = [
    (join(PatchDir,'pdfium','nativebuild.patch'), join(PDFiumDir,'build')),
]

DefaultConfig = [
    'is_debug = false',
    'pdf_is_standalone = true',
    'pdf_enable_v8 = false',
    'pdf_enable_xfa = false',
    'pdf_use_skia = false',
    'treat_warnings_as_errors = false',
]

if sys.platform.startswith('linux'):
    DefaultConfig += [ 'use_custom_libcxx = true' ]
elif sys.platform.startswith('win32'):
    DefaultConfig += [ 'pdf_use_win32_gdi = true' ]
elif sys.platform.startswith('darwin'):
    DefaultConfig += [ 'mac_deployment_target = "10.11.0"' ]

NativeBuildConfig = DefaultConfig.copy()
NativeBuildConfig += [ 'clang_use_chrome_plugins = false' ]


def dl_depottools(do_sync):
    
    if not os.path.isdir(SB_Dir):
        os.makedirs(SB_Dir)
    
    is_update = True
    
    if os.path.isdir(DepotToolsDir):
        if do_sync:
            print("DepotTools: Revert and update ...")
            run_cmd('git reset --hard HEAD', cwd=DepotToolsDir)
            run_cmd('git pull "{}"'.format(DepotTools_URL), cwd=DepotToolsDir)
        else:
            print("DepotTools: Using existing repository as-is.")
            is_update = False
    else:
        print("DepotTools: Download ...")
        run_cmd(
            'git clone --depth 1 "{}" "{}"'.format(DepotTools_URL, DepotToolsDir),
            cwd = SB_Dir
        )
    
    sep = ';' if sys.platform.startswith('win32') else ':'
    os.environ['PATH'] += sep + DepotToolsDir
    
    return is_update


def dl_pdfium(do_sync, GClient):
    
    is_update = True
    
    if os.path.isdir(PDFiumDir):
        if do_sync:
            print("PDFium: Revert / Sync  ...")
            run_cmd('"{}" revert'.format(GClient), cwd=SB_Dir)
        else:
            print("PDFium: Using existing repository as-is.")
            is_update = False
    else:
        print("PDFium: Download ...")
        run_cmd('"{}" config --unmanaged "{}"'.format(GClient, PDFium_URL), cwd=SB_Dir)
        run_cmd('"{}" sync --no-history --shallow'.format(GClient), cwd=SB_Dir)
    
    return is_update


def _apply_patchset(patchset):
    for patch, cwd in patchset:
        run_cmd('git apply -v "{}"'.format(patch), cwd=cwd)


def patch_depottools():
    _apply_patchset(DepotPatches)


def _replace_binaries():
    
    binary_names = os.listdir(NB_BinaryDir)
    
    for name in binary_names:
        
        binary_path = join(NB_BinaryDir, name)
        replacement = shutil.which(name)
        
        if replacement is None:
            print("Warning: No system provided replacement available for '{}' - ".format(name) +
                  "will keep using the version shipped with the PDFium toolchain.",
                  file = sys.stderr,
            )
            continue
        
        os.remove(binary_path)
        os.symlink(replacement, binary_path)


def patch_pdfium():
    
    _apply_patchset(PdfiumMainPatches)
    
    if sys.platform.startswith('win32'):
        _apply_patchset(PdfiumWinPatches)
        shutil.copy(join(PatchDir,'pdfium','win','resources.rc'), join(PDFiumDir,'resources.rc'))


def patch_pdfium_nativebuild():
    _apply_patchset(PdfiumNativebuildPatches)
    _replace_binaries()


def configure(config, GN):
    
    if not os.path.exists(PDFiumBuildDir):
        os.makedirs(PDFiumBuildDir)
    
    with open(join(PDFiumBuildDir,'args.gn'), 'w') as args_handle:
        args_handle.write(config)
    
    run_cmd('"{}" gen "{}"'.format(GN, PDFiumBuildDir), cwd=PDFiumDir)


def build(Ninja):
    run_cmd('"{}" -C "{}" pdfium'.format(Ninja, PDFiumBuildDir), cwd=PDFiumDir)


def find_lib(srcname=None, directory=PDFiumBuildDir):
    
    if srcname is not None:
        path = join(PDFiumBuildDir, srcname)
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
        shutil.rmtree(OutputDir)
    os.makedirs(OutputDir)
    
    if destname is None:
        destname = os.path.basename(src_libpath)
    
    destpath = join(OutputDir, destname)
    shutil.copy(src_libpath, destpath)
    
    include_dir = join(OutputDir,'include')
    shutil.copytree(join(PDFiumDir,'public'), include_dir)
    
    call_ctypesgen(OutputDir, include_dir)
    shutil.rmtree(include_dir)


def _get_tool(tool, tool_desc, prefer_systools):
    
    exe = join(DepotToolsDir, tool)
    
    if prefer_systools:
        _sh_exe = shutil.which(tool)
        if _sh_exe:
            exe = _sh_exe
        else:
            print(
                "Warning: Host system does not provide {} ({}).".format(tool, tool_desc),
                file = sys.stderr,
            )
    
    return exe


def main(
        b_argfile = None,
        b_srcname = None,
        b_destname = None,
        b_update = False,
        b_checkdeps = False,
        b_nativebuild = False,
    ):
    
    # on Linux, rename the binary to `pdfium` to ensure it also works with older versions of ctypesgen
    if b_destname is None and sys.platform.startswith('linux'):
        b_destname = 'pdfium'
    
    if b_nativebuild:
        print("Using binaries provided by the system, if available.")
    else:
        print("Using binaries provided by the PDFium toolchain.")
    
    if b_checkdeps:
        check_deps.main(b_nativebuild)
    
    GClient = join(DepotToolsDir,'gclient')
    GN    = _get_tool('gn', 'generate-ninja', b_nativebuild)
    Ninja = _get_tool('ninja', 'ninja-build', b_nativebuild)
    
    if b_argfile is None:
        
        config_list = DefaultConfig
        if b_nativebuild:
            config_list = NativeBuildConfig
        
        config_str = ''
        sep = ''
        for entry in config_list:
            config_str += sep + entry
            sep = '\n'
        
    else:
        with open(os.path.abspath(b_argfile), 'r') as file_handle:
            config_str = file_handle.read()
    
    print("\nBuild configuration:\n{}\n".format(config_str))
    
    depot_dl_done = dl_depottools(b_update)
    if depot_dl_done:
        patch_depottools()
    
    pdfium_dl_done = dl_pdfium(b_update, GClient)
    
    if pdfium_dl_done:
        patch_pdfium()
    if b_nativebuild:
        patch_pdfium_nativebuild()
    
    configure(config_str, GN)
    build(Ninja)
    
    libpath = find_lib(b_srcname)
    pack(libpath, b_destname)


def parse_args(argv):
    
    parser = argparse.ArgumentParser(
        description = "A script to automate building PDFium from source and generating bindings " +
                      "with ctypesgen.",
    )
    
    parser.add_argument(
        '--argfile', '-a',
        help = "A text file containing custom PDFium build configuration, to be evaluated by " +
               "`gn gen`. Call `gn args --list sourcebuild/pdfium/out/Default` to obtain a "   +
               "list of possible options.",
    )
    parser.add_argument(
        '--srcname', '-s',
        help = "Name of the generated PDFium binary file. This script tries to automatically find "  +
               "the binary, which should usually work. If it does not, however, this option may be " +
               "used to explicitly provide the file name to look for.",
    )
    parser.add_argument(
        '--destname', '-d',
        help = "Rename the binary to a different filename.",
    )
    parser.add_argument(
        '--update', '-u',
        action = 'store_true',
        help = "Update existing PDFium/DepotTools repositories, removing local changes.",
    )
    parser.add_argument(
        '--check-deps', '-c',
        action = 'store_true',
        help = "Check that all required dependencies are installed. (Automatically installs " +
               "missing Python packages, complains about missing system dependencies.)",
    )
    parser.add_argument(
        '--nativebuild', '-n',
        action = 'store_true',
        help = "Try to use system-provided tools if available, rather than pre-built binaries "   +
               "from DepotTools. Warning: This may or may not work, and should only be used as "  +
               "a last resort if building with the official toolchain failed. Moreover, it will " +
               "likely not work on Windows.",
    )
    
    return parser.parse_args(argv)


def run_cli(argv=sys.argv[1:]):
    args = parse_args(argv)
    return main(
        b_argfile = args.argfile,
        b_srcname = args.srcname,
        b_destname = args.destname,
        b_update = args.update,
        b_checkdeps = args.check_deps,
        b_nativebuild = args.nativebuild,
    )
    

if __name__ == '__main__':
    run_cli()
