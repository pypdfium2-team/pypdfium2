# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

# Non-stdlib imports not allowed in this file, as it is imported prior to the getdeps call

import subprocess
from glob import glob
from os.path import (
    expanduser,
    dirname,
    abspath,
    join,
)

Libnames = [
    'libpdfium.dylib',
    'pdfium.dylib',
    'libpdfium.dll',
    'pdfium.dll',
    'libpdfium.so',
    'pdfium.so',
    'libpdfium',
    'pdfium',
]


HomeDir     = expanduser('~')
SourceTree  = dirname(dirname(abspath(__file__)))
DataTree    = join(SourceTree,'data')
SB_Dir      = join(SourceTree,'sourcebuild')
ModuleDir   = join(SourceTree,'src','pypdfium2')
VersionFile = join(ModuleDir,'_version.py')


class PlatformDirs:
    Darwin64     = join(DataTree,'darwin-x64')
    DarwinArm64  = join(DataTree,'darwin-arm64')
    Linux64      = join(DataTree,'linux-x64')
    LinuxArm64   = join(DataTree,'linux-arm64')
    LinuxArm32   = join(DataTree,'linux-arm32')
    Windows64    = join(DataTree,'windows-x64')
    Windows86    = join(DataTree,'windows-x86')
    WindowsArm64 = join(DataTree,'windows-arm64')
    SourceBuild  = join(DataTree,'sourcebuild')


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
    
    ctypesgen_cmd = 'ctypesgen --library pdfium --strip-build-path "{}" -L . {} -o "{}"'.format(
        platform_dir,
        headers_str,
        bindings_file,
    )
    #print(ctypesgen_cmd)
    subprocess.run(
        ctypesgen_cmd,
        stdout = subprocess.PIPE,
        cwd    = platform_dir,
        shell  = True,
    )
    
    with open(bindings_file, 'r') as file_reader:
        text = file_reader.read()
        #text = text.split('\n"""\n', maxsplit=1)[1]
        text = text.replace(platform_dir, '.')
        text = text.replace(HomeDir, '~')
    
    with open(bindings_file, 'w') as file_writer:
        file_writer.write(text)


def _get_ver_namespace():
    
    ver_namespace = {}
    with open(VersionFile) as fh:
        exec(fh.read(), ver_namespace)
    
    return ver_namespace


_ver_namespace = _get_ver_namespace()

def extract_version(variable_str):
    return _ver_namespace[variable_str]
