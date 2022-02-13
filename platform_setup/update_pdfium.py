#! /usr/bin/env python3
# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Download the PDFium binaries and generate ctypes bindings

import os
import sys
import shutil
import tarfile
import zipfile
import argparse
import traceback
import subprocess
from os.path import (
    join,
    dirname,
    basename,
)
from urllib import request
from concurrent.futures import ThreadPoolExecutor

from platform_setup.packaging_base import (
    PlatformDirs,
    VersionFile,
    extract_version,
    call_ctypesgen,
)


ReleaseURL = "https://github.com/bblanchon/pdfium-binaries/releases/download/chromium%2F"
ReleaseExtension = "tgz"
ReleaseFiles = {
    PlatformDirs.Darwin64     : 'pdfium-mac-x64',
    PlatformDirs.DarwinArm64  : 'pdfium-mac-arm64',
    PlatformDirs.Linux64      : 'pdfium-linux-x64',
    PlatformDirs.LinuxArm64   : 'pdfium-linux-arm64',
    PlatformDirs.LinuxArm32   : 'pdfium-linux-arm',
    PlatformDirs.Windows64    : 'pdfium-win-x64',
    PlatformDirs.Windows86    : 'pdfium-win-x86',
    PlatformDirs.WindowsArm64 : 'pdfium-win-arm64',
}

def _set_versions(*versions_list):
    
    with open(VersionFile, 'r') as fh:
        content = fh.read()
    
    for variable, current_ver, new_ver in versions_list:
        
        template = "{} = {}"
        previous = template.format(variable, current_ver)
        updated = template.format(variable, new_ver)
        
        print( "'{}' -> '{}'".format(previous, updated) )
        content = content.replace(previous, updated, 1)
    
    with open(VersionFile, 'w') as fh:
        fh.write(content)


def get_latest_version():
    
    git_ls = subprocess.run(
        "git ls-remote https://github.com/bblanchon/pdfium-binaries.git",
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT,
        shell  = True,
    )
    
    git_ls = git_ls.stdout.decode('UTF-8')
    tag = git_ls.split('\t')[-1].replace('\n', '')
    version = int(tag.split('/')[-1])
    
    return version


def handle_versions(latest_version):
    
    v_minor = extract_version("V_MINOR")
    v_libpdfium = extract_version("V_LIBPDFIUM")
    
    if v_libpdfium < latest_version:
        print("New PDFium build")
        _set_versions(
            ("V_MINOR", v_minor, v_minor+1),
            ("V_LIBPDFIUM", v_libpdfium, latest_version),
        )
        
    else:
        print("No new PDFium build - will re-create bindings without incrementing version")


def clear_data():
    for dirpath in ReleaseFiles:
        if os.path.isdir(dirpath):
            shutil.rmtree(dirpath)


def _get_package(args):
    
    dirpath, file_url, file_path = args
    print("Downloading {} -> {}".format(file_url, file_path))
    
    try:
        request.urlretrieve(file_url, file_path)
    except Exception:
        traceback.print_exc()
        return None
    
    return dirpath, file_path


def download_releases(latest_version, download_files):
    
    base_url = "{}{}/".format(ReleaseURL, latest_version)
    args = []
    
    for dirpath, arcname in download_files.items():
        
        filename = "{}.{}".format(arcname, ReleaseExtension)
        file_url = base_url + filename
        
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        
        file_path = join(dirpath, filename)
        args.append( (dirpath, file_url, file_path) )
    
    archives = {}
    
    with ThreadPoolExecutor() as pool:
        
        for output in pool.map(_get_package, args):
            
            if output is not None:
                dirpath, file_path = output
                archives[dirpath] = file_path
    
    return archives


def unpack_archives(archives):
    
    for file in archives.values():
        
        extraction_path = join(dirname(file), 'build_tar')
        
        if ReleaseExtension == 'tgz':
            arc_opener = tarfile.open
        elif ReleaseExtension == 'zip':
            arc_opener = zipfile.ZipFile
        else:
            raise ValueError("Unknown archive extension {}".format(ReleaseExtension))
        
        with arc_opener(file) as archive:
            archive.extractall(extraction_path)
        
        os.remove(file)


def generate_bindings(archives): 
    
    for platform_dir in archives.keys():
        
        build_dir = join(platform_dir,'build_tar')
        bin_dir = join(build_dir,'lib')
        dirname = basename(platform_dir)
        
        if dirname.startswith('windows'):
            target_name = 'pdfium.dll'
            bin_dir = join(build_dir,'bin')
        elif dirname.startswith('darwin'):
            target_name = 'pdfium.dylib'
        elif dirname.startswith('linux'):
            target_name = 'pdfium'
        else:
            raise ValueError("Unknown platform directory name '{}'".format(dirname))
        
        current_name = os.listdir(bin_dir)[0]
        shutil.move(join(bin_dir, current_name), join(platform_dir, target_name))
        
        call_ctypesgen(platform_dir, join(build_dir,'include'))
        shutil.rmtree(build_dir)


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description = "Download pre-built PDFium packages and generate the bindings,",
    )
    parser.add_argument(
        '--platforms', '-p',
        metavar = 'P',
        nargs = '*',
    )
    return parser.parse_args(argv)


def get_download_files(args):
    
    platforms = args.platforms
    if platforms is None:
        return ReleaseFiles
    
    short_platforms = {}
    for key in ReleaseFiles.keys():
        short_platforms[basename(key)] = key
    
    download_files = {}
    
    for short_name in args.platforms:
        
        if short_name in short_platforms:
            long_name = short_platforms[short_name]
            download_files[long_name] = ReleaseFiles[long_name]
        else:
            available_keys = [k for k in short_platforms.keys()]
            raise ValueError(
                "Unknown platform name '{}'. Available keys are {}.".format(short_name, available_keys)
            )
    
    return download_files


def main(argv=sys.argv[1:]):
    
    args = parse_args(argv)
    download_files = get_download_files(args)
    
    latest_version = get_latest_version()
    handle_versions(latest_version)
    clear_data()
    
    archives = download_releases(latest_version, download_files)
    unpack_archives(archives)
    generate_bindings(archives)


if __name__ == '__main__':
    main()
