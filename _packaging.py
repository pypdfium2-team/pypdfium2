# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import subprocess
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
SourceTree  = dirname(abspath(__file__))
DataTree    = join(SourceTree,'data')
SB_Dir      = join(SourceTree,'sourcebuild')
ModuleDir   = join(SourceTree,'src','pypdfium2')
VersionFile = join(ModuleDir,'_version.py')


def run_cmd(command, cwd):
    print(command)
    subprocess.run(command, cwd=cwd, shell=True)


def postprocess_bindings(bindings_file, platform_dir):
    
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
