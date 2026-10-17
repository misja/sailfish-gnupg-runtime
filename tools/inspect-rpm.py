#!/usr/bin/env python3
import argparse
import hashlib
import io
import tarfile
import json
from pathlib import Path
import re
import tempfile
import stat
import subprocess

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description='Inspect current candidate; never install RPMs')
parser.add_argument('--artifact', type=Path)
parser.add_argument('--source-artifact', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
spec = (root / 'rpm/sailfish-gnupg-runtime.spec').read_text()
version = re.search(r'^Version: (\S+)$', spec, re.M)[1]
release = re.search(r'^Release: (\S+)$', spec, re.M)[1]
identity = f'{version}-{release}'
artifact = args.artifact or root / f'build/rpmbuild/RPMS/aarch64/sailfish-gnupg-runtime-{identity}.aarch64.rpm'
source_artifact = args.source_artifact or root / f'build/rpmbuild/SRPMS/sailfish-gnupg-runtime-{identity}.src.rpm'
output = args.output or root / f'evidence/rpm-inspection-{identity}.json'
if output.exists():
    raise SystemExit(f'Refusing to overwrite inspection evidence: {output}')
def query(option):
    return subprocess.check_output(['rpm', '-qp', option, str(artifact)], text=True)
record = {name: query(option) for name, option in [('provides','--provides'), ('requires','--requires'), ('payload','--list'), ('scripts','--scripts'), ('obsoletes','--obsoletes')]}
assert set(record['provides'].splitlines()) == {f'sailfish-gnupg-runtime = {identity}', f'sailfish-gnupg-runtime(aarch-64) = {identity}', f'sailfish-gnupg-private = {identity}'}
assert record['obsoletes'].strip() == 'sailfish-gnupg-private < 2.5.24-0.7'
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
def payload(path):
    raw = subprocess.check_output(['rpm2cpio', str(path)])
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
        if name == 'TRAILER!!!': return entries
        assert name not in entries, 'Duplicate normalized payload entry'
        entries[name] = (fields[1], data)

entries = payload(artifact)
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
source_entries = payload(source_artifact)
capsule_name = f'sailfish-gnupg-runtime-{version}.tar.gz'
assert source_entries[capsule_name][1] == (root / 'sources' / capsule_name).read_bytes()
assert source_entries['sailfish-gnupg-runtime.spec'][1] == (root / 'rpm/sailfish-gnupg-runtime.spec').read_bytes()
assert subprocess.check_output(['rpm', '-qp', '--qf', '%{SOURCERPM}', str(artifact)],
                               text=True) == source_artifact.name
with tarfile.open(fileobj=io.BytesIO(source_entries[capsule_name][1])) as archive:
    prefix = f'sailfish-gnupg-runtime-{version}/'
    provenance = json.loads(archive.extractfile(prefix + 'SOURCE-PROVENANCE.json').read())
    for name, expected in provenance['files'].items():
        member = archive.getmember(prefix + name)
        assert member.isfile(), name
        assert hashlib.sha256(archive.extractfile(member).read()).hexdigest() == expected['sha256'], name
    locked = json.loads((root / 'sources.lock.json').read_text())
    for component in locked['sources']:
        name = f"sources/{component['name']}-{component['version']}.tar.bz2"
        assert provenance['files'][name]['sha256'] == component['sha256'], name
    for name in ['LICENSE', 'LICENSING.md', 'tools/build-runtime.sh',
                 'tools/prepare-sources.py', 'runtime/sailfish-gpg',
                 'runtime/sailfish-gpg-agent', 'runtime/runtime-policy.sh',
                 'sources/signature_key.asc', 'evidence/source-verification.json']:
        assert name in provenance['files'], name
record['source_package'] = {
    'sha256': hashlib.sha256(source_artifact.read_bytes()).hexdigest(),
    'capsule_sha256': hashlib.sha256(source_entries[capsule_name][1]).hexdigest(),
    'source_file_count': len(provenance['files']),
    'project_provenance': {k: v for k, v in provenance.items() if k != 'files'},
    'checks': ['matching binary SOURCERPM', 'exact spec and capsule bytes',
               'all source-provenance hashes', 'seven upstream archives',
               'build scripts, wrappers, notices and public verification material']}
record.update(artifact_sha256=hashlib.sha256(artifact.read_bytes()).hexdigest(),
              identity=identity, scope='RPM metadata and exact policy payload only; no native acceptance')
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(record, indent=2) + '\n')
print('PASS private binary RPM policy and matching complete source RPM; no installation')
