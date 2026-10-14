#!/usr/bin/env python3
"""Extract only locked archives; fetch-sources.py authenticates signatures first."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / 'sources.lock.json').read_text())
evidence = json.loads((root / 'evidence/source-verification.json').read_text())
assert len(evidence) == len(lock['sources'])
destination = root / 'inspect'
destination.mkdir(exist_ok=True)
for item in lock['sources']:
    filename = f"{item['name']}-{item['version']}.tar.bz2"
    archive = root / 'sources' / filename
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == item['sha256'], filename
    matching = [entry for entry in evidence if entry['name'] == item['name'] and entry['version'] == item['version'] and entry['sha256'] == item['sha256']]
    assert len(matching) == 1 and matching[0]['signers'], filename
    assert all(signer in lock['allowed_primary_fingerprints'] for signer in matching[0]['signers']), filename
    component = destination / f"{item['name']}-{item['version']}"
    if component.exists():
        # Only disposable extracted source trees under this project are replaced.
        shutil.rmtree(component)
    with tarfile.open(archive) as stream:
        assert all(member.name.split('/')[0] == component.name for member in stream.getmembers()), filename
        stream.extractall(destination, filter='data')
    print('Prepared ' + filename)
