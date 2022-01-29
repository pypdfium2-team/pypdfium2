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
    'pdfium.so',
    'libpdfium.so',
    'pdfium.dylib',
    'libpdfium.dylib',
    'pdfium.dll',
    'libpdfium.dll',
    'libpdfium',
    'pdfium',
]


HomeDir    = expanduser('~')
SourceTree = dirname(abspath(__file__))
DataTree   = join(SourceTree,'data')
SB_Dir     = join(SourceTree,'sourcebuild')


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


def get_version_namespace():
    
    ver_path = join(SourceTree,'src','pypdfium2','_version.py')
    
    ver_namespace = {}
    with open(ver_path) as ver_file:
        exec(ver_file.read(), ver_namespace)
    
    return ver_namespace
