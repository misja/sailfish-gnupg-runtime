"""Admission primitives for operation and persistent-agent registration.

The future privileged coordinator owns the directory and state. Tests supply an
isolated directory/owner explicitly. No environment overrides or default paths.
DRAINED means operation leases drained, never agent/process quiescence.
"""
import contextlib
import fcntl
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import time


class AdmissionError(RuntimeError):
    pass


class Lease:
    def __init__(self, fd, generation, kind="operation"):
        self.kind = kind
        self.fd = fd
        self.generation = generation

    def close(self):
        if self.fd is not None:
            # Do not LOCK_UN: inherited copies must retain the shared lock.
            os.close(self.fd)
            self.fd = None

    def spawn(self, argv, **kwargs):
        if self.fd is None:
            raise AdmissionError("Closed operation lease")
        if "pass_fds" in kwargs or "close_fds" in kwargs:
            raise AdmissionError("Lease inheritance cannot be overridden")
        return subprocess.Popen(argv, pass_fds=(self.fd,), **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


class Admission:
    STATES = {"ACTIVE", "DRAINING", "DRAINED", "BLOCKED"}

    def __init__(self, directory, *, expected_uid=0):
        self.directory = Path(directory)
        self.expected_uid = expected_uid

    @staticmethod
    def _generation(value):
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise AdmissionError("A SHA-256 payload generation is required")
        return value

    @contextlib.contextmanager
    def _directory(self):
        # Refuse symlink aliases; no recursive creation or ownership repair.
        if not self.directory.is_absolute() or self.directory.resolve(strict=True) != self.directory:
            raise AdmissionError("Admission directory must be canonical")
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            if info.st_uid != self.expected_uid or stat.S_IMODE(info.st_mode) != 0o755:
                raise AdmissionError("Unsafe admission directory ownership or mode")
            yield fd
        finally:
            os.close(fd)

    def _file(self, directory, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != self.expected_uid
                or stat.S_IMODE(info.st_mode) != 0o644 or info.st_nlink != 1):
            os.close(fd)
            raise AdmissionError("Unsafe admission file")
        return fd

    @contextlib.contextmanager
    def _gate(self, directory, exclusive=False):
        fd = self._file(directory, "admission.lock")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            yield
        finally:
            os.close(fd)

    def _read(self, directory):
        fd = self._file(directory, "state.json")
        try:
            raw = os.read(fd, 4097)
        finally:
            os.close(fd)
        if len(raw) > 4096:
            raise AdmissionError("Oversized admission state")
        try:
            state = json.loads(raw)
            if set(state) != {"state", "generation"} or state["state"] not in self.STATES:
                raise ValueError()
            self._generation(state["generation"])
        except (ValueError, TypeError, AdmissionError) as error:
            raise AdmissionError("Invalid admission state") from error
        return state

    def _write(self, directory, state, generation):
        name = ".state-" + secrets.token_hex(16)
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory)
        try:
            payload = (json.dumps({"state": state, "generation": generation}) + "\n").encode()
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fchmod(stream.fileno(), 0o644)
                os.fsync(stream.fileno())
            os.replace(name, "state.json", src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(name, dir_fd=directory)
            except FileNotFoundError:
                pass

    def initialize(self, generation, *, active=True):
        """Explicit privileged setup; partial setup is not automatically repaired."""
        self._generation(generation)
        if os.geteuid() != self.expected_uid:
            raise AdmissionError("Only the state owner can initialize admission")
        self.directory.mkdir(mode=0o755)
        self.directory.chmod(0o755)
        with self._directory() as directory:
            for name in ("admission.lock", "operations.lock", "agents.lock", "bootstrap.lock"):
                fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o644, dir_fd=directory)
                os.fchmod(fd, 0o644)
                os.fsync(fd)
                os.close(fd)
            self._write(directory, "ACTIVE" if active else "BLOCKED", generation)

    def status(self):
        with self._directory() as directory, self._gate(directory):
            return self._read(directory)

    def acquire(self):
        """Check ACTIVE and register an operation in one gate critical section."""
        with self._directory() as directory, self._gate(directory):
            state = self._read(directory)
            if state["state"] != "ACTIVE":
                raise AdmissionError("Private runtime admission is closed")
            fd = self._file(directory, "operations.lock")
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BaseException:
                os.close(fd)
                raise
            return Lease(fd, state["generation"])

    def acquire_stop(self):
        """Stop is allowed after operation drain, but never during active work."""
        with self._directory() as directory, self._gate(directory):
            state = self._read(directory)
            if state["state"] not in {"ACTIVE", "DRAINED"}:
                raise AdmissionError("Agent stop requires active or drained admission")
            fd = self._file(directory, "operations.lock")
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BaseException:
                os.close(fd)
                raise
            return Lease(fd, state["generation"], "stop")

    def acquire_agent(self, operation):
        """Attach an agent while its admitted operation still owns registration."""
        if operation.kind != "operation" or operation.fd is None:
            raise AdmissionError("A live operation registration is required")
        with self._directory() as directory, self._gate(directory):
            state = self._read(directory)
            if (state["state"] not in {"ACTIVE", "DRAINING"}
                    or state["generation"] != operation.generation):
                raise AdmissionError("Agent generation does not match its operation")
            check = self._file(directory, "operations.lock")
            try:
                actual, expected = os.fstat(operation.fd), os.fstat(check)
                if (actual.st_dev, actual.st_ino) != (expected.st_dev, expected.st_ino):
                    raise AdmissionError("Foreign operation registration")
            finally:
                os.close(check)
            fd = self._file(directory, "agents.lock")
            try:
                fcntl.flock(fd, fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BaseException:
                os.close(fd)
                raise
            return Lease(fd, operation.generation, "agent")

    def agents_registered(self):
        """Negative result is lease-only, never evidence of process absence."""
        with self._directory() as directory:
            fd = self._file(directory, "agents.lock")
            try:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return False
                except BlockingIOError:
                    return True
            finally:
                os.close(fd)

    def drain(self, timeout):
        """Close admission first; drain leases only. Never reopen automatically."""
        if os.geteuid() != self.expected_uid:
            raise AdmissionError("Only the state owner can drain admission")
        if not isinstance(timeout, (int, float)) or not 0 <= timeout <= 3600:
            raise AdmissionError("Invalid drain deadline")
        with self._directory() as directory:
            with self._gate(directory, exclusive=True):
                state = self._read(directory)
                if state["state"] != "ACTIVE":
                    raise AdmissionError("Explicit recovery required for closed admission")
                self._write(directory, "DRAINING", state["generation"])
            fd = self._file(directory, "operations.lock")
            try:
                deadline = time.monotonic() + timeout
                while True:
                    try:
                        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        result = "DRAINED"
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            result = "BLOCKED"
                            break
                        time.sleep(min(0.02, max(0, deadline - time.monotonic())))
                with self._gate(directory, exclusive=True):
                    if self._read(directory) != {"state": "DRAINING", "generation": state["generation"]}:
                        raise AdmissionError("Maintenance state changed unexpectedly")
                    self._write(directory, result, state["generation"])
                return result
            finally:
                os.close(fd)
