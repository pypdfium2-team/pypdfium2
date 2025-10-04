# SPDX-FileCopyrightText: 2025 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause

import re
import sys
import json
import shutil
import hashlib
from pathlib import Path
import urllib.request as url_request
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).parents[1]))
from pypdfium2_setup.base import *


MIN_PDFIUM_FOR_VERIFY = 7415
MIN_GH_FOR_VERIFY = "2.47.0"

def get_gh_avail():
    
    if not shutil.which("gh"):
        log("gh CLI is not installed")
        return False
    
    from packaging.version import Version
    gh_version = run_cmd(["gh", "--version"], cwd=None, capture=True)
    gh_version = Version( re.match(r"gh version ([\d.]+)", gh_version).group(1) )
    
    if gh_version >= Version(MIN_GH_FOR_VERIFY):
        return True
    else:
        log("gh CLI version is too old for verification")
        return False

def _get_gh_auth_state():
    return run_cmd(["gh", "auth", "status"], cwd=None, check=False).returncode == 0

def _gh_web_api(path):
    log(f"API Request {path}")
    with url_request.urlopen("https://api.github.com"+path) as h:
        return json.loads( h.read().decode() )

def _get_sha256sum(path):
    # https://stackoverflow.com/a/44873382/15547292
    if sys.version_info >= (3, 11):
        with open(path, "rb") as fh:
            return hashlib.file_digest(fh, "sha256").hexdigest()
    else:
        chunksize = 128 * 1024  # 128 KiB
        chunk = memoryview(bytearray(chunksize))
        hash = hashlib.sha256()
        
        with open(path, "rb", buffering=0) as fh:
            n = fh.readinto(chunk)
            while n:
                hash.update(chunk[:n])
                n = fh.readinto(chunk)
        
        return hash.hexdigest()


def do_verify(archives, pdfium_version, have_recent_gh, auto_enabled):
    
    # https://github.com/cli/cli/issues/11803#issuecomment-3334820737
    
    if not have_recent_gh:
        raise SystemExit(f"--verify requires gh CLI >= {MIN_GH_FOR_VERIFY}")
    if pdfium_version < MIN_PDFIUM_FOR_VERIFY:
        raise SystemExit(f"--verify was passed, but the requested pdfium version is too low: {MIN_PDFIUM_FOR_VERIFY}")
    
    artifact_paths = tuple(archives.values())
    one_artifact = artifact_paths[0]
    
    is_authed = _get_gh_auth_state()
    if is_authed:
        log("gh is authenticated, using default verification")
        extra_args = []
    else:
        log("gh is not authenticated, attempting tokenless verification (may fail due to rate limit)")
        attest_path = DataDir/f"pdfium-binaries-{pdfium_version}-attestation.json"
        if not attest_path.exists():
            file_sum = _get_sha256sum(one_artifact)
            try:
                attest_json = _gh_web_api(f"/repos/bblanchon/pdfium-binaries/attestations/sha256:{file_sum}")
            except HTTPError as e:
                if auto_enabled and "rate limit exceeded" in str(e):
                    log("Warning: Unable to auto-verify due to rate limit.")
                    return
                else:
                    raise e
            attest_json = attest_json["attestations"][0]["bundle"]
            with attest_path.open("w") as fh:
                json.dump(attest_json, fh)
        extra_args = ["-b", str(attest_path)]
    
    verify_result = run_cmd(
        ["gh", "attestation", "verify", "-R", "bblanchon/pdfium-binaries", str(one_artifact), *extra_args, "--format=json"],
        cwd=DataDir, check=True, capture=True
    )
    log(f"{one_artifact.name}: verified by gh")
    
    # short circuit if there are no more archives - the typical setup caller downloads only one archive at a time
    if not len(archives) > 1:
        return
    
    verify_result = json.loads(verify_result)
    attested_artifacts = verify_result[0]["verificationResult"]["statement"]["subject"]
    attested_artifacts = {d["name"]: d["digest"]["sha256"] for d in attested_artifacts}
    
    for artifact in artifact_paths:
        exp_checksum = attested_artifacts[artifact.name]
        actual_checksum = _get_sha256sum(artifact)
        if exp_checksum == actual_checksum:
            log(f"{artifact.name}: verified by result checksum: {exp_checksum}")
        else:
            raise SystemExit(f"{artifact.name}: checksum mismatch: expected {exp_checksum} != actual {actual_checksum}")
