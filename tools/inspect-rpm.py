#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path
import re
import tempfile
import stat
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Inspect current candidate; never install RPMs')
parser.add_argument('--artifact', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
spec = (root / 'rpm/sailfish-gnupg-private.spec').read_text()
version = re.search(r'^Version: (\S+)$', spec, re.M)[1]
release = re.search(r'^Release: (\S+)$', spec, re.M)[1]
identity = f'{version}-{release}'
artifact = args.artifact or root / f'RPMS/sailfish-gnupg-private-{identity}.aarch64.rpm'
output = args.output or root / f'evidence/rpm-inspection-{identity}.json'
if output.exists():
    raise SystemExit(f'Refusing to overwrite inspection evidence: {output}')
def query(option):
    return subprocess.check_output(['rpm', '-qp', option, str(artifact)], text=True)
record = {name: query(option) for name, option in [('provides','--provides'), ('requires','--requires'), ('payload','--list'), ('scripts','--scripts')]}
assert set(record['provides'].splitlines()) == {f'sailfish-gnupg-private = {identity}', f'sailfish-gnupg-private(aarch-64) = {identity}'}
assert 'libc.so.6(GLIBC_2.38)(64bit)' in record['requires']
assert 'libz.so.1()(64bit)' in record['requires']
assert not re.search(r'^lib(?:gcrypt|gpg-error|assuan|ksba|npth)\.so', record['requires'], re.M)
assert not record['scripts'].strip(), 'Unexpected installation script'
for binary in ['gpg','gpg-agent','gpgconf','pinentry-tty']:
    assert f'/usr/libexec/sailfish-gnupg/bin/{binary}\n' in record['payload'], binary
for notice in ['LICENSE', 'LICENSING.md']:
    assert f'/usr/libexec/sailfish-gnupg/licenses/project/{notice}\n' in record['payload'], notice
for name in ['libgpg-error-1.61','libgcrypt-1.12.4','libassuan-3.0.2','npth-1.8','libksba-1.8.1','pinentry-1.3.3','gnupg-2.5.24']:
    assert f'/usr/libexec/sailfish-gnupg/licenses/{name}/COPYING' in record['payload'], name
for item in record['payload'].splitlines():
    assert item in ('/usr/bin/sailfish-gpg', '/usr/bin/sailfish-gpg-agent') or item == '/usr/libexec/sailfish-gnupg' or item.startswith('/usr/libexec/sailfish-gnupg/'), item
    assert '/include/' not in item and not item.endswith(('.la','.a','.pc')), item
# Parse newc payload without extracting or executing packaged files.
raw = subprocess.check_output(['rpm2cpio', str(artifact)])
offset, entries = 0, {}
while True:
    assert offset + 110 <= len(raw), 'Truncated newc header'
    assert raw[offset:offset + 6] in (b'070701', b'070702')
    fields = [int(raw[offset + 6 + i * 8:offset + 14 + i * 8], 16) for i in range(13)]
    size, namesize = fields[6], fields[11]
    offset += 110
    assert namesize > 1 and offset + namesize <= len(raw) and raw[offset + namesize - 1] == 0 and b'\0' not in raw[offset:offset + namesize - 1], 'Invalid newc name'
    name = raw[offset:offset + namesize - 1].decode().removeprefix('./')
    offset = (offset + namesize + 3) & ~3
    assert offset + size <= len(raw), 'Truncated newc data'
    data = raw[offset:offset + size]
    offset = (offset + size + 3) & ~3
    if name == 'TRAILER!!!': break
    assert name not in entries, 'Duplicate normalized payload entry'
    entries[name] = (fields[1], data)
for name, source, mode in [
    ('usr/bin/sailfish-gpg', 'sailfish-gpg', 0o755),
    ('usr/bin/sailfish-gpg-agent', 'sailfish-gpg-agent', 0o755),
    ('usr/libexec/sailfish-gnupg/libexec/runtime-policy.sh', 'runtime-policy.sh', 0o644),
]:
    actual_mode, data = entries[name]
    assert data == (root / 'runtime' / source).read_bytes(), name
    assert stat.S_ISREG(actual_mode), name
    assert actual_mode & 0o7777 == mode, name
for requirement in ['/usr/bin/busybox', '/usr/bin/env', '/usr/bin/getent', '/usr/bin/id']:
    assert requirement in record['requires'].splitlines(), requirement
assert '(/bin/stat or /usr/bin/stat)' in record['requires'].splitlines()
elf_records = []
with tempfile.TemporaryDirectory(prefix='synthetic-rpm-elf-') as temporary:
    for name, (mode, data) in sorted(entries.items()):
        if not data.startswith(b'\x7fELF'): continue
        assert stat.S_ISREG(mode), name
        object_path = Path(temporary) / 'object'
        object_path.write_bytes(data)
        header = subprocess.check_output(['readelf', '-h', str(object_path)], text=True)
        dynamic = subprocess.check_output(['readelf', '-d', str(object_path)], text=True)
        assert 'AArch64' in header, name
        paths = re.findall(r'\((?:RUNPATH|RPATH)\).*\[(.*?)\]', dynamic)
        assert paths == ['/usr/libexec/sailfish-gnupg/lib'], (name, paths)
        if name.startswith(('usr/libexec/sailfish-gnupg/bin/', 'usr/libexec/sailfish-gnupg/libexec/')):
            program = subprocess.check_output(['readelf', '-l', str(object_path)], text=True)
            assert '[Requesting program interpreter: /lib/ld-linux-aarch64.so.1]' in program, name
        elf_records.append({'path': name, 'runpath': paths,
                            'needed': re.findall(r'\(NEEDED\).*\[(.*?)\]', dynamic)})
assert elf_records, 'No ELF objects found'
record['elf_static'] = elf_records
record.update(artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
              identity=identity, scope='RPM metadata and exact policy payload only; no native acceptance')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2) + '\n')
print('PASS private RPM payload/provides, retained platform requirements, no installation scripts')
