# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import os.path

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


HomeDir = os.path.expanduser('~')

def postprocess_bindings(bindings_file, platform_dir):
    
    with open(bindings_file, 'r') as file_reader:
        text = file_reader.read()
        #text = text.split('\n"""\n', maxsplit=1)[1]
        text = text.replace(platform_dir, '.')
        text = text.replace(HomeDir, '~')
    
    with open(bindings_file, 'w') as file_writer:
        file_writer.write(text)
