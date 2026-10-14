#!/usr/bin/env python3
"""SDK package/file fingerprints only; never reads a personal GnuPG home."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

packages = ['gnupg2', 'gpgme', 'libgcrypt', 'libgpg-error', 'libksba', 'pth']
def query(args):
    return subprocess.check_output(['rpm'] + args, text=True)
record = {'versions': query(['-q'] + packages), 'files': {}, 'verification': {}}
for package in packages:
    record['verification'][package] = subprocess.run(['rpm', '-V', package], text=True, capture_output=True).stdout
    for item in query(['-ql', package]).splitlines():
        path = Path(item)
        # Restrict to distributed binaries/libraries/docs, not user files.
        assert item.startswith(('/usr/', '/bin/', '/lib/', '/lib64/', '/etc/')) or path.is_dir(), item
        if path.is_symlink():
            record['files'][item] = {'symlink': str(path.readlink())}
        elif path.is_file():
            record['files'][item] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
Path(f'/home/ubuntu/gnupg-runtime/evidence/stock-{sys.argv[1]}.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'Snapshot {sys.argv[1]}: {len(record["files"])} stock files')
