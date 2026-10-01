"""Check the manifest consumed by Morphe's JsonPatchBundle."""
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / 'patches-bundle.json').read_text())
assert re.fullmatch(r'\d+\.\d+\.\d+', manifest['version']), 'Missing valid release version'
assert manifest['description'].strip(), 'Missing source description'
# MorpheAsset uses kotlinx.datetime.LocalDateTime (UTC, without a Z suffix).
created = manifest['created_at']
assert 'T' in created and not created.endswith('Z') and '+' not in created
assert datetime.datetime.fromisoformat(created).tzinfo is None
url = urlparse(manifest['download_url'])
assert url.scheme == 'https' and url.netloc == 'github.com'
assert url.path == f'/YunaAUbot/yuna-calendar-patches/releases/download/v{manifest["version"]}/patches-{manifest["version"]}.mpp'
assert manifest.get('signature_download_url') is None, 'Do not advertise a nonexistent signature'
print('PASS: nonempty, versioned Morphe source manifest with correct UTC LocalDateTime and public bundle URL')
