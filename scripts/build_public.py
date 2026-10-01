#!/usr/bin/env python3
"""Credential-free Morphe bundle build for the shared Forgejo worker.

Uses the official Desktop distribution as compile-only Patcher API, public
Kotlin compiler artifacts and Google's public D8 artifact. No APK is involved.
"""
import hashlib
import json
import os
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.build-tools'
CACHE.mkdir(exist_ok=True)
LOCK = ROOT / 'toolchain-lock.json'


def fetch(name, url):
    target = CACHE / name
    if not target.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            data = response.read()
        target.write_bytes(data)
    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    pins = json.loads(LOCK.read_text()) if LOCK.exists() else {}
    if name in pins:
        assert pins[name] == {'url': url, 'sha256': sha}, 'Toolchain hash mismatch: ' + name
    elif os.environ.get('BOOTSTRAP_TOOLCHAIN_LOCK') == '1':
        pins[name] = {'url': url, 'sha256': sha}
        LOCK.write_text(json.dumps(pins, indent=2) + '\n')
    else:
        raise RuntimeError('Unpinned toolchain artifact: ' + name)
    return target


def maven(group, artifact, version):
    name = f'{artifact}-{version}.jar'
    return fetch(name, f'https://repo.maven.apache.org/maven2/{group.replace(".", "/")}/{artifact}/{version}/{name}')


compiler = [maven('org.jetbrains.kotlin', a, '2.4.10') for a in (
    'kotlin-compiler-embeddable', 'kotlin-build-tools-api', 'kotlin-stdlib',
    'kotlin-script-runtime', 'kotlin-daemon-embeddable')]
compiler += [maven('org.jetbrains.kotlin', 'kotlin-reflect', '1.6.10'),
             maven('org.jetbrains.kotlinx', 'kotlinx-coroutines-core-jvm', '1.8.0'),
             maven('org.jetbrains', 'annotations', '26.0.2')]
desktop = fetch('morphe-desktop-1.18.0-all.jar',
    'https://github.com/MorpheApp/morphe-desktop/releases/download/v1.18.0/morphe-desktop-1.18.0-all.jar')
d8 = fetch('r8-9.4.28.jar', 'https://dl.google.com/dl/android/maven2/com/android/tools/r8/9.4.28/r8-9.4.28.jar')
version = next(line.split('=', 1)[1].strip() for line in (ROOT / 'gradle.properties').read_text().splitlines() if line.startswith('version'))
build = ROOT / 'build/public'
build.mkdir(parents=True, exist_ok=True)
classes = build / 'classes.jar'
sources = sorted((ROOT / 'patches/src/main/kotlin/app/yuna').rglob('*.kt'))
assert sources, 'No patch sources'
subprocess.run(['java', '-cp', os.pathsep.join(map(str, compiler)),
    'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect',
    '-classpath', os.pathsep.join(map(str, [desktop, compiler[2], compiler[-1]])),
    '-jvm-target', '17', '-d', str(classes), *map(str, sources)], check=True)
dex = build / 'dex'
dex.mkdir(exist_ok=True)
subprocess.run(['java', '-cp', str(d8), 'com.android.tools.r8.D8', '--release',
                '--min-api', '26', '--classpath', str(desktop),
                '--output', str(dex), str(classes)], check=True)
output = ROOT / f'patches/build/libs/patches-{version}.mpp'
output.parent.mkdir(parents=True, exist_ok=True)
manifest = ('Manifest-Version: 1.0\r\nName: Yuna Calendar Patches\r\n'
    'Description: Targeted Your Calendar Widget patches for Morphe\r\n'
    f'Version: {version}\r\nTimestamp: 0\r\n'
    'Source: https://forgejo.horotw.dev/ai-collective/yuna-calendar-patches\r\n'
    'Author: Yuna\r\nLicense: GPLv3\r\nPatcher-Version: 1.14.1\r\n\r\n')
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
    def add(name, data):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        bundle.writestr(info, data)
    add('META-INF/MANIFEST.MF', manifest.encode())
    with zipfile.ZipFile(classes) as compiled:
        for name in sorted(compiled.namelist()):
            if not name.endswith('/') and name != 'META-INF/MANIFEST.MF':
                add(name, compiled.read(name))
    for path in sorted(dex.glob('classes*.dex')):
        add(path.name, path.read_bytes())
print('BUILT', output)
print('SHA256', hashlib.sha256(output.read_bytes()).hexdigest())
