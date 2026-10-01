from pathlib import Path
import zipfile
root = Path(__file__).resolve().parents[1]
version = next(line.split('=', 1)[1].strip() for line in (root / 'gradle.properties').read_text().splitlines() if line.startswith('version'))
with zipfile.ZipFile(root / f'patches/build/libs/patches-{version}.mpp') as bundle:
    assert bundle.testzip() is None
    assert 'app/yuna/patches/calendar/CalendarPatchesKt.class' in bundle.namelist()
    assert bundle.read('classes.dex')[:4] == b'dex\n'
    assert f'Version: {version}' in bundle.read('META-INF/MANIFEST.MF').decode()
print('PASS: JVM patch class, Android DEX and version metadata present')
