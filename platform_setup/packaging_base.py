# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

# Non-stdlib imports not allowed in this file, as it is imported prior to the check_deps call

import subprocess
from glob import glob
from os.path import (
    expanduser,
    dirname,
    abspath,
    join,
)

Libnames = (
    'pdfium',
    'pdfium.dylib',
    'pdfium.dll',
    'libpdfium.so',
    'pdfium.so',
    'libpdfium',
    'libpdfium.dylib',
    'libpdfium.dll',
)


HomeDir     = expanduser('~')
SourceTree  = dirname(dirname(abspath(__file__)))
DataTree    = join(SourceTree,'data')
SB_Dir      = join(SourceTree,'sourcebuild')
ModuleDir   = join(SourceTree,'src','pypdfium2')
VersionFile = join(ModuleDir,'_version.py')


class PlatformNames:
    darwin_x64    = 'darwin_x64'
    darwin_arm64  = 'darwin_arm64'
    linux_x64     = 'linux_x64'
    linux_x86     = 'linux_x86'
    linux_arm64   = 'linux_arm64'
    linux_arm32   = 'linux_arm32'
    windows_x64   = 'windows_x64'
    windows_x86   = 'windows_x86'
    windows_arm64 = 'windows_arm64'
    sourcebuild   = 'sourcebuild'


def run_cmd(command, cwd):
    print(command)
    subprocess.run(command, cwd=cwd, shell=True)


def call_ctypesgen(platform_dir, include_dir):
    
    headers_str = ''
    sep = ''
    
    for file in sorted(glob( join(include_dir,'*.h') )):
        headers_str += sep + '"{}"'.format(file)
        sep = ' '
    
    bindings_file = join(platform_dir,'_pypdfium.py')
    
    ctypesgen_cmd = 'ctypesgen --library pdfium --strip-build-path "{}" -L . {} -o "{}"'.format(platform_dir, headers_str, bindings_file)
    subprocess.run(
        ctypesgen_cmd,
        stdout = subprocess.PIPE,
        cwd    = platform_dir,
        shell  = True,
    )
    
    with open(bindings_file, 'r') as file_reader:
        text = file_reader.read()
        text = text.replace(platform_dir, '.')
        text = text.replace(HomeDir, '~')
    
    with open(bindings_file, 'w') as file_writer:
        file_writer.write(text)


def _get_ver_namespace():
    
    ver_namespace = {}
    with open(VersionFile, 'r') as fh:
        exec(fh.read(), ver_namespace)
    
    return ver_namespace


_ver_namespace = _get_ver_namespace()

def extract_version(variable_str):
    return _ver_namespace[variable_str]
