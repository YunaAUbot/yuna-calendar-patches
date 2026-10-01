#!/usr/bin/env python3
"""Publish only our patch bundle to Forgejo, using the ephemeral job token."""
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = next(line.split('=', 1)[1].strip() for line in (root / 'gradle.properties').read_text().splitlines() if line.startswith('version'))
tag = os.environ['RELEASE_TAG']
assert tag == 'v' + version, 'Tag and source version disagree'
repository = os.environ['RELEASE_REPOSITORY']
assert repository == 'ai-collective/yuna-calendar-patches'
api = 'https://forgejo.horotw.dev/api/v1/repos/' + repository
headers = {'Authorization': 'token ' + os.environ['RELEASE_TOKEN']}
artifact = root / f'patches/build/libs/patches-{version}.mpp'
data = artifact.read_bytes()
sha = hashlib.sha256(data).hexdigest()

def request(path, body=None, content_type=None, method=None):
    h = dict(headers)
    if content_type:
        h['Content-Type'] = content_type
    req = urllib.request.Request(api + path, data=body, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

try:
    release = request('/releases/tags/' + urllib.parse.quote(tag))
except urllib.error.HTTPError as e:
    if e.code != 404:
        raise
    payload = {'tag_name': tag, 'target_commitish': 'main', 'name': 'Yuna Calendar Patches ' + version,
        'body': 'Morphe patch bundle for Your Calendar Widget 1.71.3.\n\n'
                '- Hide Free Edition reminder events: enabled by default.\n'
                '- Enable local premium features: optional, disabled by default.\n\n'
                'Import this .mpp in Morphe Manager and patch your own APK. No third-party APK is distributed.\n\n'
                'Premium only changes the local Pro checks; Google/Microsoft integration and purchases are not guaranteed.\n\n'
                'SHA256: `' + sha + '`',
        'draft': False, 'prerelease': False}
    release = request('/releases', json.dumps(payload).encode(), 'application/json')
assets = request(f'/releases/{release["id"]}/assets')
existing = next((a for a in assets if a['name'] == artifact.name), None)
if existing:
    with urllib.request.urlopen(urllib.request.Request(existing['browser_download_url'], headers=headers), timeout=30) as r:
        assert hashlib.sha256(r.read()).hexdigest() == sha, 'Existing release differs; refusing overwrite'
    asset = existing
else:
    boundary = 'YunaPatchBundleBoundary'
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="attachment"; filename="{artifact.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
            + data + f'\r\n--{boundary}--\r\n'.encode())
    asset = request(f'/releases/{release["id"]}/assets?name={urllib.parse.quote(artifact.name)}', body,
                    'multipart/form-data; boundary=' + boundary)
with urllib.request.urlopen(urllib.request.Request(asset['browser_download_url'], headers=headers), timeout=30) as r:
    assert hashlib.sha256(r.read()).hexdigest() == sha, 'Release download hash mismatch'
verified = request('/releases/tags/' + urllib.parse.quote(tag))
assert not verified['draft'] and not verified['prerelease']
print('VERIFIED RELEASE', verified['html_url'])
print('VERIFIED ASSET', asset['browser_download_url'])
print('SHA256', sha)
