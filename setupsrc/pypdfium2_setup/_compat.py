# SPDX-FileCopyrightText: 2023 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

# Safe tar extraction preventing CVE-2007-4559
# Tries to use the most elegant strategy available in the caller's python version

__all__ = ["safe_unpack_tar"]

import sys

if sys.version_info >= (3, 11, 4):  # PEP 706
    import shutil
    def safe_unpack_tar(archive_path, dest_dir):
        shutil.unpack_archive(archive_path, dest_dir, format="tar", filter="data")

else:  # workaround
    
    if sys.version_info >= (3, 9):
        _is_within_dir = lambda path, dir: path.is_relative_to(dir)
    else:
        import os.path
        _is_within_dir = lambda path, dir: os.path.commonpath([dir, path]) == str(dir)
    
    import tarfile
    
    def safe_unpack_tar(archive_path, dest_dir):
        dest_dir = dest_dir.resolve()
        with tarfile.open(archive_path) as tar:
            for m in tar.getmembers():
                if not (m.isfile() or m.isdir()) or not _is_within_dir((dest_dir/m.name).resolve(), dest_dir):
                    raise RuntimeError("Path traversal, symlink or special member in tar archive (probably malicious).")
            tar.extractall(dest_dir)
