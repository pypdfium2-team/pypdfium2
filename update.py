#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Download the PDFium binaries and generate ctypes bindings
# Last confirmed to work on 2021-12-24

import os
from os.path import (
    join,
    dirname,
    basename,
    realpath,
)
import shutil
import tarfile
import zipfile
import argparse
import traceback
import subprocess
from urllib import request
from concurrent.futures import ThreadPoolExecutor
from setup_base import (
    Darwin64,
    DarwinArm64,
    Linux64,
    LinuxArm64,
    LinuxArm32,
    Windows64,
    Windows86,
    WindowsArm64,
)


HomeDir      = os.path.expanduser('~')
SourceTree   = dirname(realpath(__file__))
VersionFile  = join(SourceTree,'src','pypdfium2','_version.py')
DataTree     = join(SourceTree,'data')
ReleaseURL   = 'https://github.com/bblanchon/pdfium-binaries/releases/download/chromium%2F'
ReleaseExtension = 'tgz'
ReleaseFiles = {
    Darwin64     : 'pdfium-mac-x64',
    DarwinArm64  : 'pdfium-mac-arm64',
    Linux64      : 'pdfium-linux-x64',
    LinuxArm64   : 'pdfium-linux-arm64',
    LinuxArm32   : 'pdfium-linux-arm',
    Windows64    : 'pdfium-win-x64',
    Windows86    : 'pdfium-win-x86',
    WindowsArm64 : 'pdfium-win-arm64',
}


def _version_pos(version_content, variable):
    expression = variable + ' = '
    pos_var = version_content.index(expression) + len(expression)
    pos_lineend = len(version_content[:pos_var]) + version_content[pos_var:].index('\n')
    return pos_var, pos_lineend

def _get_version(version_content, variable):
    pos_var, pos_lineend = _version_pos(version_content, variable)
    value = version_content[pos_var:pos_lineend]
    version = int(value)
    return version

def _set_version(version_content, variable, new_version):
    pos_var, pos_lineend = _version_pos(version_content, variable)
    new_vc = version_content[:pos_var] + str(new_version) + version_content[pos_lineend:]
    return new_vc


def get_latest_version():
    
    git_ls = subprocess.run(
        f'git ls-remote https://github.com/bblanchon/pdfium-binaries.git',
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        shell  = True,
    )
    
    git_ls = git_ls.stdout.decode('UTF-8')
    tag = git_ls.split('\t')[-1].replace('\n', '')
    version = int(tag.split('/')[-1])
    
    return version


def handle_versions(latest_version):
    
    with open(VersionFile, 'r') as file:
        version_content = file.read()
        v_minor = _get_version(version_content, "V_MINOR")
        v_libpdfium = _get_version(version_content, "V_LIBPDFIUM")
    
    if v_libpdfium < latest_version:
        print("New PDFium build")
        new_content = _set_version(version_content, "V_MINOR", v_minor+1)
        new_content = _set_version(new_content, "V_LIBPDFIUM", latest_version)
        with open(VersionFile, 'w') as file:
            file.write(new_content)
    else:
        print("No new PDFium build - will re-create bindings without incrementing version")


def clear_data():
    
    for dirname in ReleaseFiles:
        
        dirpath = join(DataTree, dirname)
        
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)


def _get_package(args):
    
    dirname, file_url, file_path = args
    print(f"Downloading {file_url} -> {file_path}")
    
    try:
        request.urlretrieve(file_url, file_path)
    except Exception:
        traceback.print_exc()
        return None
    
    return dirname, file_path


def download_releases(latest_version, download_files):
    
    base_url = f"{ReleaseURL}{latest_version}/"
    args = []
    
    for dirname, arcname in download_files.items():
        
        filename = f"{arcname}.{ReleaseExtension}"
        file_url = base_url + filename
        
        dest_dir = join(DataTree, dirname)
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        
        file_path = join(dest_dir, filename)
        args.append( (dirname, file_url, file_path) )
    
    archives = {}
    
    with ThreadPoolExecutor() as pool:
        
        for output in pool.map(_get_package, args):
            
            if output is not None:
                dirname, file_path = output
                archives[dirname] = file_path
    
    return archives


def unpack_archives(archives):
    
    for file in archives.values():
        
        extraction_path = join(dirname(file), 'build_tar')
        
        if ReleaseExtension == 'tgz':
            arc_opener = tarfile.open
        elif ReleaseExtension == 'zip':
            arc_opener = zipfile.ZipFile
        else:
            raise ValueError(f"Unknown archive extension {ReleaseExtension}")
        
        with arc_opener(file) as archive:
            archive.extractall(extraction_path)
        
        os.remove(file)


def postprocess_bindings(bindings_file, platform_dir):
    
    with open(bindings_file, 'r') as file_reader:
        text = file_reader.read()
        #text = text.split('\n"""\n', maxsplit=1)[1]
        text = text.replace(platform_dir, '.')
        text = text.replace(HomeDir, '~')
    
    with open(bindings_file, 'w') as file_writer:
        file_writer.write(text)


def generate_bindings(archives): 
    
    for platform_dir in archives.keys():
        
        dirname = basename(platform_dir)
        build_dir = join(platform_dir, 'build_tar')
        
        if dirname.startswith('windows'):
            
            bin_name = 'pdfium.dll'
            
            if dirname.endswith('x64'):
                bin_dir = join(build_dir,'x64','bin')
            elif dirname.endswith('x86'):
                bin_dir = join(build_dir,'x86','bin')
            elif dirname.endswith('arm64'):
                bin_dir = join(build_dir,'arm64','bin')
            else:
                raise ValueError("Binary directory could not be recognised.")
            
        elif dirname.startswith('darwin'):
            
            bin_name = 'pdfium.dylib'
            bin_dir = join(build_dir,'lib')
            
        elif dirname.startswith('linux'):
            
            bin_name = 'pdfium'
            bin_dir = join(build_dir,'lib')
        
        current_bin_name = os.listdir(bin_dir)[0]
        bindings_file = join(platform_dir,'_pypdfium.py')
        header_files = join(build_dir,'include','*.h')
        
        current_binpath = join(bin_dir, current_bin_name)
        new_binpath = join(bin_dir, bin_name)
        os.rename(current_binpath, new_binpath)
        dest_binpath = join(platform_dir, bin_name)
        
        shutil.move(new_binpath, dest_binpath)
        
        ctypesgen_cmd = f"ctypesgen --library pdfium --strip-build-path {platform_dir} -L . {header_files} -o {bindings_file}"
        subprocess.run(
            ctypesgen_cmd,
            stdout = subprocess.PIPE,
            cwd    = platform_dir,
            shell  = True,
        )
        
        postprocess_bindings(bindings_file, platform_dir)
        shutil.rmtree(build_dir)


def parse_args():
    parser = argparse.ArgumentParser(
        description = "Download pre-built PDFium packages and generate the bindings,",
    )
    parser.add_argument(
        '--platforms', '-p',
        metavar = 'P',
        nargs = '*',
    )
    return parser.parse_args()


def get_download_files(args):
    
    platforms = args.platforms
    if platforms is None:
        return ReleaseFiles
    
    download_files = {}
    for plat_name in platforms:
        if plat_name in ReleaseFiles:
            download_files[plat_name] = ReleaseFiles[plat_name]
        else:
            available_keys = [k for k in ReleaseFiles.keys()]
            raise ValueError(f"Unknown platform name '{plat_name}'. Available keys are {available_keys}.")
    
    return download_files


def main():
    
    args = parse_args()
    download_files = get_download_files(args)
    
    latest_version = get_latest_version()
    handle_versions(latest_version)
    clear_data()
    
    archives = download_releases(latest_version, download_files)
    unpack_archives(archives)
    generate_bindings(archives)


if __name__ == '__main__':
    main()
