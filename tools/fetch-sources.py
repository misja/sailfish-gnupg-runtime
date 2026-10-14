#!/usr/bin/env python3
"""Fetch pinned public release sources inside the SDK container only."""
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.request

root = Path(__file__).resolve().parents[1]
if str(root) != '/home/ubuntu/gnupg-runtime':
    raise SystemExit('Run only from /home/ubuntu/gnupg-runtime in the SDK container')
lock = json.loads((root / 'sources.lock.json').read_text())
sources = root / 'sources'
sources.mkdir(exist_ok=True)
(root / 'evidence').mkdir(exist_ok=True)
home = root / 'verify-home'
home.mkdir(mode=0o700, exist_ok=True)
def download(url, dest):
    with urllib.request.urlopen(url, timeout=60) as response:
        dest.write_bytes(response.read())
keys = sources / 'signature_key.asc'
download('https://gnupg.org/signature_key.asc', keys)
gpg = ['gpg', '--no-options', '--homedir', str(home), '--batch']
subprocess.run(gpg + ['--import', str(keys)], check=True, capture_output=True)
records = []
for item in lock['sources']:
    filename = f"{item['name']}-{item['version']}.tar.bz2"
    url = f"https://gnupg.org/ftp/gcrypt/{item['name']}/{filename}"
    archive = sources / filename
    if not archive.exists():
        download(url, archive)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != item['sha256']:
        raise SystemExit(f'Checksum mismatch: {filename}')
    signature = sources / (filename + '.sig')
    download(url + '.sig', signature)
    verified = subprocess.run(gpg + ['--status-fd', '1', '--verify', str(signature), str(archive)], capture_output=True, text=True)
    (root / 'evidence' / (filename + '.verification.txt')).write_text(verified.stdout + verified.stderr)
    valid = [line.split()[2:] for line in verified.stdout.splitlines() if line.startswith('[GNUPG:] VALIDSIG ')]
    if verified.returncode or not valid or any(fields[-1] not in lock['allowed_primary_fingerprints'] for fields in valid):
        raise SystemExit(f'Signature not accepted: {filename}')
    records.append(dict(item, url=url, signature_sha256=hashlib.sha256(signature.read_bytes()).hexdigest(), signers=[fields[-1] for fields in valid]))
    print(f'Authenticated {filename}', flush=True)
(root / 'evidence' / 'source-verification.json').write_text(json.dumps(records, indent=2) + '\n')
