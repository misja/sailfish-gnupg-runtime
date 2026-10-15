"""Trusted same-generation bootstrap/recovery; never accepts changed payloads."""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat

from lifecycle_admission import AdmissionError

PREFIX = Path('/usr/libexec/sailfish-gnupg')
ENTRYPOINTS = (Path('/usr/bin/sailfish-gpg'), Path('/usr/bin/sailfish-gpg-agent'))
MANIFEST = 'libexec/payload-generation.json'


class Payload:
    def __init__(self, prefix=PREFIX, *, entrypoints=ENTRYPOINTS, expected_uid=0):
        self.prefix = Path(prefix)
        self.entrypoints = tuple(Path(p) for p in entrypoints)
        self.expected_uid = expected_uid

    def _trusted(self, path):
        info = path.lstat()
        if info.st_uid != self.expected_uid or info.st_mode & 0o7022:
            raise AdmissionError('Unsafe installed-payload ownership or mode')
        return info

    def _entry(self, path):
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            if info.st_uid != self.expected_uid:
                raise AdmissionError('Unsafe payload symlink owner')
            target = os.readlink(path)
            if Path(target).is_absolute() or not path.resolve(strict=True).is_relative_to(self.prefix):
                raise AdmissionError('Payload symlink escapes private prefix')
            return {'kind': 'link', 'target': target}
        self._trusted(path)
        mode = oct(stat.S_IMODE(info.st_mode))
        if stat.S_ISDIR(info.st_mode):
            return {'kind': 'directory', 'mode': mode}
        if not stat.S_ISREG(info.st_mode):
            raise AdmissionError('Unexpected payload file type')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            opened = os.fstat(fd)
            if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
                raise AdmissionError('Payload changed while opening')
            digest = hashlib.sha256()
            while True:
                data = os.read(fd, 1024 * 1024)
                if not data:
                    break
                digest.update(data)
            after = os.fstat(fd)
            if (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise AdmissionError('Payload changed while hashing')
        finally:
            os.close(fd)
        return {'kind': 'file', 'mode': mode, 'sha256': digest.hexdigest()}

    def snapshot(self, expected_paths=None):
        if not self.prefix.is_absolute() or self.prefix.resolve(strict=True) != self.prefix:
            raise AdmissionError('Installed prefix must be canonical')
        self._trusted(self.prefix.parent)
        locations = {'.': self.prefix}
        directories = {'.'}
        for directory, dirs, files in os.walk(self.prefix, followlinks=False):
            for name in sorted(dirs + files):
                path = Path(directory) / name
                relative = str(path.relative_to(self.prefix))
                if relative == MANIFEST:
                    continue
                locations[relative] = path
                if name in dirs:
                    directories.add(relative)
        for path in self.entrypoints:
            if not path.is_absolute() or path.parent.resolve(strict=True) != path.parent:
                raise AdmissionError('Public entry path must be canonical')
            self._trusted(path.parent)
            locations['@entry/' + path.name] = path
        # Reject unknown names before hashing any contents. A stray user file
        # beneath the software prefix must never become an input to verification.
        if expected_paths is not None and set(locations) != expected_paths:
            raise AdmissionError('Unexpected or missing installed payload path')
        result = {}
        for name, path in locations.items():
            value = self._entry(path)
            if name in directories and value['kind'] != 'directory':
                raise AdmissionError('Symlinked payload directory')
            if name.startswith('@entry/') and value['kind'] != 'file':
                raise AdmissionError('Public entry point must be a regular file')
            result[name] = value
        return result

    def build_manifest(self):
        """Build-root/test operation only; administration never regenerates trust."""
        entries = self.snapshot()
        target = self.prefix / MANIFEST
        raw = (json.dumps({'schema': 1, 'entries': entries}, sort_keys=True, indent=2) + '\n').encode()
        temporary = target.with_name('.payload-generation.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(raw)
                os.fchmod(stream.fileno(), 0o644)
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return hashlib.sha256(raw).hexdigest()

    def verify(self, expected=None):
        path = self.prefix / MANIFEST
        self._trusted(path)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise AdmissionError('Payload manifest must be regular')
            raw = os.read(fd, 8 * 1024 * 1024 + 1)
        finally:
            os.close(fd)
        if len(raw) > 8 * 1024 * 1024:
            raise AdmissionError('Oversized payload manifest')
        generation = hashlib.sha256(raw).hexdigest()
        if expected is not None and generation != expected:
            raise AdmissionError('Installed generation differs from trusted state')
        try:
            manifest = json.loads(raw)
            if set(manifest) != {'schema', 'entries'} or manifest['schema'] != 1:
                raise ValueError()
            if not isinstance(manifest['entries'], dict):
                raise ValueError()
            if manifest['entries'] != self.snapshot(set(manifest['entries'])):
                raise AdmissionError('Installed payload does not match its manifest')
        except (ValueError, TypeError) as error:
            raise AdmissionError('Invalid payload manifest') from error
        return generation


class ProcessCheck:
    def __init__(self, prefix=PREFIX, proc=Path('/proc')):
        self.prefix = str(prefix) + '/'
        self.proc = Path(proc)

    def __call__(self):
        # Root-only administrative check of public executable/mapping metadata.
        # No argv, environment, key-home discovery or secret file contents.
        for process in self.proc.iterdir():
            if not process.name.isdigit() or int(process.name) == os.getpid():
                continue
            try:
                try:
                    executable = os.readlink(process / 'exe')
                except FileNotFoundError:
                    executable = ''  # Kernel thread or vanished process.
                if executable.startswith(self.prefix):
                    raise AdmissionError('Private runtime process still present')
                for line in (process / 'maps').read_text().splitlines():
                    fields = line.split(None, 5)
                    if len(fields) == 6 and fields[5].startswith(self.prefix):
                        raise AdmissionError('Private runtime mapping still present')
            except FileNotFoundError:
                if process.exists():
                    raise AdmissionError('Process metadata unavailable')
            except OSError as error:
                raise AdmissionError('Process metadata unavailable') from error


class Controller:
    def __init__(self, admission, payload, process_check=None):
        self.admission = admission
        self.payload = payload
        self.process_check = process_check if process_check is not None else ProcessCheck(payload.prefix)

    def _owner(self):
        if os.geteuid() != self.admission.expected_uid:
            raise AdmissionError('Lifecycle administration requires the state owner')

    @contextlib.contextmanager
    def _closed_locks(self):
        self._owner()
        with self.admission._directory() as directory:
            descriptors = []
            try:
                # Bootstrap excludes even clients that have not loaded Python
                # or registered their operation yet. Never replace lock inodes.
                for name in ('bootstrap.lock', 'operations.lock', 'agents.lock'):
                    fd = self.admission._file(directory, name)
                    descriptors.append(fd)
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.admission._gate(directory, exclusive=True):
                    yield directory
            finally:
                for fd in reversed(descriptors):
                    os.close(fd)

    def initialize(self):
        self._owner()
        generation = self.payload.verify()
        self.admission.initialize(generation, active=False)
        # Failure leaves persistent BLOCKED state and original lock inodes.
        with self._closed_locks() as directory:
            self.process_check()
            self.payload.verify(generation)
            self.admission._write(directory, 'ACTIVE', generation)
        return generation

    def close(self, timeout):
        self._owner()
        if self.admission.status()['state'] == 'ACTIVE':
            return self.admission.drain(timeout)
        # Reconcile a cancelled/timed-out drain, while remaining CLOSED. Agents
        # are intentionally permitted so their user can stop them in DRAINED.
        with self.admission._directory() as directory:
            descriptors = []
            try:
                for name in ('bootstrap.lock', 'operations.lock'):
                    fd = self.admission._file(directory, name)
                    descriptors.append(fd)
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.admission._gate(directory, exclusive=True):
                    state = self.admission._read(directory)
                    self.payload.verify(state['generation'])
                    self.admission._write(directory, 'DRAINED', state['generation'])
                return 'DRAINED'
            finally:
                for fd in reversed(descriptors):
                    os.close(fd)

    def recover(self):
        with self._closed_locks() as directory:
            state = self.admission._read(directory)
            if state['state'] == 'ACTIVE':
                raise AdmissionError('Recovery requires closed admission')
            try:
                self.process_check()
                self.payload.verify(state['generation'])
            except (AdmissionError, OSError, ValueError):
                self.admission._write(directory, 'BLOCKED', state['generation'])
                raise
            self.admission._write(directory, 'ACTIVE', state['generation'])
        return state['generation']
