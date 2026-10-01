"""Assert both user-requested patches are on by default in the built bundle."""
import re
import subprocess
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from java import java_executable

root = Path(__file__).resolve().parents[1]
version = next(line.split('=', 1)[1].strip() for line in (root / 'gradle.properties').read_text().splitlines() if line.startswith('version'))
output = subprocess.check_output([java_executable(), '-jar', str(root / '.build-tools/morphe-desktop-1.18.0-all.jar'), 'list-patches', '--patches=' + str(root / f'patches/build/libs/patches-{version}.mpp'), '-pv'], text=True, stderr=subprocess.STDOUT)
for name in ('Hide Free Edition reminder events', 'Enable local premium features'):
    match = re.search(r'Name: ' + re.escape(name) + r'\n.*?Enabled: (true|false)', output, re.S)
    assert match and match.group(1) == 'true', name + ' is not enabled by default'
print('PASS: both Hide and Premium are registered and enabled by default')
