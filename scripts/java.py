#!/usr/bin/env python3
"""Use Java 21 or provision a project-local, publisher-checksummed Temurin JRE.
Never change the shared worker's global Java selection.
"""
import hashlib
import re
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

URL = 'https://github.com/adoptium/temurin21-binaries/releases/download/jdk-21.0.12.1%2B1/OpenJDK21U-jre_x64_linux_hotspot_21.0.12.1_1.tar.gz'
SHA256 = '2413149700df0f7d440500a84a8f764c535f21e5a5e87d38328b64eec2c5b500'
ROOT = Path(__file__).resolve().parents[1]


def java_executable():
    current = shutil.which('java')
    if current:
        result = subprocess.run([current, '-version'], capture_output=True, text=True)
        if re.search(r'version "21\.', result.stdout + result.stderr):
            return current
    cache = ROOT / '.build-tools'
    cache.mkdir(exist_ok=True)
    executable = cache / 'jdk-21.0.12.1+1-jre/bin/java'
    if executable.exists():
        return str(executable)
    archive = cache / 'temurin21-jre.tar.gz'
    if not archive.exists():
        with urllib.request.urlopen(URL, timeout=90) as response:
            archive.write_bytes(response.read())
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == SHA256, 'Temurin checksum mismatch'
    with tarfile.open(archive) as bundle:
        bundle.extractall(cache, filter='data')
    assert executable.exists(), 'Missing Java executable in verified archive'
    return str(executable)


if __name__ == '__main__':
    print(java_executable())
